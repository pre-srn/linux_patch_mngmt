from django.shortcuts import render, redirect, get_object_or_404

from django.urls import resolve
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django_celery_results.models import TaskResult

from django.http import HttpResponse
from .decorators import ssh_setup_required
from .models import System, SSHProfile, Package, Task
from .forms import SetupSSHForm, SSHPassphaseSubmitForm
from .utils import connect_ssh, is_puppet_running, ssh_run_get_system_info, create_tmp_file, delete_tmp_file
from .tasks import *

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'account/register.html', {'form': form})

@login_required
@ssh_setup_required
def home(request):
    systems = System.objects.filter(owner=request.user, connected=True)
    form = SSHPassphaseSubmitForm()
    return render(request, 'home.html', {'form': form, 'systems': systems})

@login_required
@ssh_setup_required
def manage_system(request, system_id):
    system = get_object_or_404(System, pk=system_id)
    installed_packages = system.packages.filter(active=True).order_by(Lower('name'))
    outdated_packages = installed_packages.filter(new_version__isnull=False).order_by(Lower('name'))
    return render(request, 'system.html', {'installed_packages': installed_packages, 'outdated_packages': outdated_packages})

@login_required
@ssh_setup_required
def list_task(request):
    tasks = Task.objects.filter(initiated_by=request.user).order_by('-started_at')
    return render(request, 'task.html', {'tasks': tasks})

@login_required
@ssh_setup_required
def clear_task(request):
    tasks = Task.objects.filter(initiated_by=request.user)
    for task in tasks:
        TaskResult.objects.filter(task_id=task.task_id).delete()
    tasks.delete()
    messages.success(request, 'All task results have been cleared.')
    return redirect('list_task')

@login_required
@ssh_setup_required
def get_system_info(request):
    if request.method == 'POST':
        form = SSHPassphaseSubmitForm(request.POST)
        if form.is_valid():
            ssh_profile = request.user.sshprofile
            # run an ssh task in Celery
            celery_task_id = celery_ssh_run_get_system_info.delay(str(ssh_profile.ssh_server_address), 
                                                                str(ssh_profile.ssh_username),
                                                                str(ssh_profile.ssh_server_port),
                                                                str(ssh_profile.ssh_key),
                                                                str(form.cleaned_data['ssh_passphase']), 
                                                                request.user.id)
            Task.objects.create(task_id=celery_task_id, task_name="Get system information", initiated_by=request.user)
            messages.success(request, 'Task initiated')
        else:
            messages.error(request, 'Please input your SSH passphase first.')
    return redirect('home') 

@login_required
def setup_ssh(request):
    if request.method == 'POST':
        form = SetupSSHForm(request.POST, request.FILES, instance=request.user.sshprofile)
        if form.is_valid():

            if 'ssh_key' in request.FILES:
                tmp_ssh_key = create_tmp_file(request.FILES['ssh_key'])
            else:
                # In case the file already exists on the server
                tmp_ssh_key = str(form.instance.ssh_key)

            is_connected, ssh_connection = connect_ssh(str(form.cleaned_data['ssh_server_address']), 
                                                    str(form.cleaned_data['ssh_username']), 
                                                    str(form.cleaned_data['ssh_server_port']), 
                                                    tmp_ssh_key, 
                                                    str(form.cleaned_data['ssh_passphase']))
            # Test connection
            if is_connected:
                if (is_puppet_running(ssh_connection)):
                    messages.info(request, 'Successfully connected to your Puppet master server. \
                                            A task to get system information has been initiated.')
                    form.save()
                    ssh_run_get_system_info(ssh_connection, request.user)
                    if 'ssh_key' in request.FILES: delete_tmp_file(tmp_ssh_key)
                    return redirect('home')
                else:
                    messages.error(request, 'Puppet or Mcollective is not installed/running on your server. Please recheck again.')
            else:
                messages.error(request, 'Cannot connect to your server. Please check your connection.')
            
            if 'ssh_key' in request.FILES: delete_tmp_file(tmp_ssh_key)
    else:
        form = SetupSSHForm(instance=request.user.sshprofile)

    url_name = resolve(request.path_info).url_name
    return render(request, 'account/'+ url_name + '.html', {'form': form, 'user': request.user})

@login_required
def config_password_done(request):
    messages.success(request, 'Your password has been successfully updated.')
    return redirect('home') 