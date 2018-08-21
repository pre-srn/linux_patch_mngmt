from django.shortcuts import render, redirect, get_object_or_404

from django.http import HttpResponse, JsonResponse
from django.urls import resolve
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django_celery_results.models import TaskResult

from .decorators import ssh_setup_required
from .models import System, SSHProfile, Package, Task, CVE
from .forms import SetupSSHForm, SSHPassphraseSubmitForm, UpdatePackageAjaxSubmitForm, UpdateAllPackagesAjaxSubmitForm
from .utils import connect_ssh, is_puppet_running, create_tmp_file, delete_tmp_file
from .tasks import *

######################################################
# General HTML request views
######################################################

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('setup_ssh')
    else:
        form = UserCreationForm()
    return render(request, 'account/register.html', {'form': form})

@login_required
@ssh_setup_required
def home(request):
    systems = System.objects.filter(owner=request.user, connected=True).order_by('hostname')
    total_systems = systems.count()
    form = SSHPassphraseSubmitForm()
    return render(request, 'home.html', {'form': form, 'systems': systems, 'total_systems': total_systems})

@login_required
@ssh_setup_required
def manage_system(request, system_id):
    form = SSHPassphraseSubmitForm()
    system = get_object_or_404(System.objects.filter(owner=request.user, connected=True), pk=system_id)
    installed_packages = system.packages.filter(active=True).order_by(Lower('name'))
    outdated_packages = installed_packages.filter(new_version__isnull=False).order_by(Lower('name'))
    case_sql = '(case when severity="low" then 1 when severity="moderate" then 2 when severity="important" then 3 when severity="critical" then 4 end)'
    cves = CVE.objects.filter(system=system).extra(select={'severity_order': case_sql}, order_by=['affected_package', '-severity_order'])
    return render(request, 'system.html', 
        {'form': form, 'installed_packages': installed_packages, 'outdated_packages': outdated_packages,
        'system': system, 'cves': cves})

@login_required
@ssh_setup_required
def list_task(request):
    tasks = Task.objects.filter(initiated_by=request.user).order_by('-started_at')
    total_tasks = tasks.count()
    return render(request, 'task.html', {'tasks': tasks, 'total_tasks': total_tasks})

@login_required
@ssh_setup_required
def clear_task(request):
    tasks = Task.objects.filter(initiated_by=request.user, is_notified=True)
    for task in tasks:
        TaskResult.objects.filter(task_id=task.task_id).delete()
    tasks.delete()
    messages.success(request, 'All completed tasks have been cleared.')
    return redirect('list_task')

@login_required
def setup_ssh(request):
    if request.method == 'POST':
        form = SetupSSHForm(request.POST, request.FILES, instance=request.user.sshprofile)
        if form.is_valid():
            if 'ssh_server_pub_key' in request.FILES:
                tmp_ssh_server_pub_key = create_tmp_file(request.FILES['ssh_server_pub_key'])
            else:
                tmp_ssh_server_pub_key = str(form.instance.ssh_server_pub_key) # In case the file already exists on the server

            if 'ssh_key' in request.FILES:
                tmp_ssh_key = create_tmp_file(request.FILES['ssh_key'])
            else:
                tmp_ssh_key = str(form.instance.ssh_key) # In case the file already exists on the server

            is_connected, key_match, ssh_connection = connect_ssh(str(form.cleaned_data['ssh_server_address']), 
                                                    str(form.cleaned_data['ssh_username']), 
                                                    str(form.cleaned_data['ssh_server_port']),
                                                    tmp_ssh_server_pub_key,
                                                    tmp_ssh_key,
                                                    str(form.cleaned_data['ssh_passphrase']))
            # Test connection
            if is_connected:
                if key_match:
                    if (is_puppet_running(ssh_connection)):
                        form.save()
                        if 'ssh_key' in request.FILES: delete_tmp_file(tmp_ssh_key)
                        if 'ssh_server_pub_key' in request.FILES: delete_tmp_file(tmp_ssh_server_pub_key)
                        ssh_profile = request.user.sshprofile
                        celery_task_id = celery_ssh_run_get_system_info.delay(str(ssh_profile.ssh_server_address), 
                                                                            str(ssh_profile.ssh_username),
                                                                            str(ssh_profile.ssh_server_port),
                                                                            str(ssh_profile.ssh_server_pub_key),
                                                                            str(ssh_profile.ssh_key),
                                                                            str(form.cleaned_data['ssh_passphrase']), 
                                                                            request.user.id)
                        Task.objects.create(task_id=celery_task_id, task_name="Get system information", initiated_by=request.user)
                        messages.info(request, 'Successfully connected to your Puppet master server. \
                                                A task to get system information has been initiated. \
                                                <p><small>[{0}]</small></p>'.format(celery_task_id))
                        return redirect('home')
                    else:
                        messages.error(request, 'Puppet or Mcollective is not installed/running on your server. Please setup and recheck again.')
                else:
                    messages.error(request, "Server public key doesn't match. Please verify your server authenticity again.")
            else:
                messages.error(request, 'Cannot connect to your server. Your SSH login certificate may be invalid or your server may be unavailable.')
            
            if 'ssh_key' in request.FILES: delete_tmp_file(tmp_ssh_key)
            if 'ssh_server_pub_key' in request.FILES: delete_tmp_file(tmp_ssh_server_pub_key)
    else:
        form = SetupSSHForm(instance=request.user.sshprofile)

    url_name = resolve(request.path_info).url_name
    first_time = False
    if url_name == 'setup_ssh':
        first_time = True

    return render(request, 'account/config_ssh.html', {'form': form, 'user': request.user, 'first_time': first_time})

@login_required
def config_password_done(request):
    messages.success(request, 'Your password has been successfully updated.')
    return redirect('home')


######################################################
# AJAX request views
######################################################

@login_required
@ssh_setup_required
def ajax_get_system_info(request):
    if request.method == 'POST':
        form = SSHPassphraseSubmitForm(request.POST)
        response = {}
        if form.is_valid():
            ssh_profile = request.user.sshprofile
            celery_task_id = celery_ssh_run_get_system_info.delay(str(ssh_profile.ssh_server_address), 
                                                                str(ssh_profile.ssh_username),
                                                                str(ssh_profile.ssh_server_port),
                                                                str(ssh_profile.ssh_server_pub_key),
                                                                str(ssh_profile.ssh_key),
                                                                str(form.cleaned_data['ssh_passphrase']), 
                                                                request.user.id)
            Task.objects.create(task_id=celery_task_id, task_name="Get system information", initiated_by=request.user)
            response['error'] = False
            response['message'] = '<strong>Task initiated</strong><p>Task: Get system information<br/><small>[{0}]</small></p>'.format(celery_task_id)
        else:
            response['error'] = True
            response['message'] = 'Please input your SSH passphrase first.'
        return JsonResponse(response)
    else:
        return redirect('home') 


@login_required
@ssh_setup_required
def ajax_get_system_info_table(request):
    systems = System.objects.filter(owner=request.user, connected=True).order_by('hostname')
    return render(request, 'ajax_templates/system_info_table.html', {'systems': systems})


@login_required
@ssh_setup_required
def ajax_get_installed_packages_table(request):
    if 'system_id' in request.GET:
        system_id = int(request.GET.get('system_id', None))
        system = get_object_or_404(System.objects.filter(owner=request.user, connected=True), pk=system_id)
        installed_packages = system.packages.filter(active=True).order_by(Lower('name'))
        return render(request, 'ajax_templates/installed_packages_table.html', {'installed_packages': installed_packages})
    else:
        return redirect('home') 


@login_required
@ssh_setup_required
def ajax_get_outdated_packages_table(request):
    if 'system_id' in request.GET:
        system_id = int(request.GET.get('system_id', None))
        system = get_object_or_404(System.objects.filter(owner=request.user, connected=True), pk=system_id)
        outdated_packages = system.packages.filter(active=True, new_version__isnull=False).order_by(Lower('name'))
        return render(request, 'ajax_templates/outdated_packages_table.html', {'system':system, 'outdated_packages': outdated_packages})
    else:
        return redirect('home') 


@login_required
@ssh_setup_required
def ajax_get_cve_info_table(request):
    if 'system_id' in request.GET:
        system_id = int(request.GET.get('system_id', None))
        system = get_object_or_404(System.objects.filter(owner=request.user, connected=True), pk=system_id)
        case_sql = '(case when severity="low" then 1 when severity="moderate" then 2 when severity="important" then 3 when severity="critical" then 4 end)'
        cves = CVE.objects.filter(system=system).extra(select={'severity_order': case_sql}, order_by=['affected_package', '-severity_order'])
        return render(request, 'ajax_templates/cve_info_table.html', {'system': system, 'cves': cves})
    else:
        return redirect('home')


@login_required
@ssh_setup_required
def ajax_get_task_info_table(request):
    tasks = Task.objects.filter(initiated_by=request.user).order_by('-started_at')
    return render(request, 'ajax_templates/task_info_table.html', {'tasks': tasks})


@login_required
@ssh_setup_required
def ajax_update_package(request):
    if request.method == 'POST':
        form = UpdatePackageAjaxSubmitForm(request.POST)
        response = {}
        if form.is_valid():
            system_id = int(form.cleaned_data['system_id'])
            package_id = int(form.cleaned_data['package_id'])
            system = get_object_or_404(System.objects.filter(owner=request.user, connected=True), pk=system_id)
            package = get_object_or_404(system.packages, pk=package_id)
            ssh_profile = request.user.sshprofile
            celery_task_id = celery_ssh_run_update_package.delay(str(ssh_profile.ssh_server_address), 
                                                                str(ssh_profile.ssh_username),
                                                                str(ssh_profile.ssh_server_port),
                                                                str(ssh_profile.ssh_server_pub_key),
                                                                str(ssh_profile.ssh_key),
                                                                str(form.cleaned_data['ssh_passphrase']),
                                                                package_id,
                                                                package.name,
                                                                system_id,
                                                                system.hostname)
            Task.objects.create(task_id=celery_task_id, 
                                task_name='Update {0} on {1}'.format(package.name, system.hostname), 
                                initiated_by=request.user)
            response['error'] = False
            response['message'] = '<strong>Task initiated</strong><p>Task: Update {0} on {1}<br/><small>[{2}]</small></p>'.format(package.name, system.hostname, celery_task_id)
        else:
            response['error'] = True
            response['message'] = 'Please input your SSH passphrase first.'
        return JsonResponse(response)
    else:
        return redirect('home')


@login_required
@ssh_setup_required
def ajax_update_all_packages(request):
    if request.method == 'POST':
        form = UpdateAllPackagesAjaxSubmitForm(request.POST)
        response = {}
        if form.is_valid():
            system_id = int(form.cleaned_data['system_id'])
            system = get_object_or_404(System.objects.filter(owner=request.user, connected=True), pk=system_id)
            ssh_profile = request.user.sshprofile
            celery_task_id = celery_ssh_run_update_all_packages.delay(str(ssh_profile.ssh_server_address), 
                                                                    str(ssh_profile.ssh_username),
                                                                    str(ssh_profile.ssh_server_port),
                                                                    str(ssh_profile.ssh_server_pub_key),
                                                                    str(ssh_profile.ssh_key),
                                                                    str(form.cleaned_data['ssh_passphrase']),
                                                                    system_id,
                                                                    system.hostname)
            Task.objects.create(task_id=celery_task_id, 
                                task_name='Update all packages on {0}'.format(system.hostname), 
                                initiated_by=request.user)
            response['error'] = False
            response['message'] = '<strong>Task initiated</strong><p>Task: Update all packages on {0}<br/><small>[{1}]</small></p>'.format(system.hostname, celery_task_id)
        else:
            response['error'] = True
            response['message'] = 'Please input your SSH passphrase first.'
        return JsonResponse(response)
    else:
        return redirect('home')


@login_required
@ssh_setup_required
def ajax_scan_cve_all_systems(request):
    response = {}
    celery_task_id = celery_scan_cve.delay(request.user.id, None)
    Task.objects.create(task_id=celery_task_id, task_name="Scan CVE on all systems", initiated_by=request.user)
    response['error'] = False
    response['message'] = '<strong>Task initiated</strong><p>Task: Scan CVE on all systems<br/><small>[{0}]</small></p>'.format(celery_task_id)
    return JsonResponse(response)


@login_required
@ssh_setup_required
def ajax_scan_cve_specific_system(request, system_id):
    response = {}
    system = get_object_or_404(System.objects.filter(owner=request.user, connected=True), pk=system_id)
    if system.system_package_manager == 'yum':
        celery_task_id = celery_scan_cve.delay(request.user.id, system.id)
        Task.objects.create(task_id=celery_task_id, task_name="Scan CVE on {0}".format(system.hostname), initiated_by=request.user)
        response['error'] = False
        response['message'] = '<strong>Task initiated</strong><p>Task: Scan CVE on {0}<br/><small>[{1}]</small></p>'.format(system.hostname, celery_task_id)
    else:
        response['error'] = True
        response['message'] = "This system doesn't support CVE scanning at the moment as it doesn't use RPM."
    return JsonResponse(response)


@login_required
@ssh_setup_required
def ajax_check_task_status(request):
    response = {}
    tasks = Task.objects.filter(initiated_by=request.user, is_notified=False)
    response['notified_tasks'] = []
    for task in tasks:
        task_status = task.get_task_status()
        if (task_status != 'RUNNING'):
            notified_task = {'task_id': task.task_id, 'task_name': task.task_name, 'task_status': task_status}
            task.is_notified = True
            task.save()
            response['notified_tasks'].append(notified_task)
    return JsonResponse(response)