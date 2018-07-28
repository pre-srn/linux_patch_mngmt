from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from .decorators import ssh_setup_required
from .models import Server, SSHProfile
from .forms import SetupSSHForm
from .utils import *

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST, request.FILES)
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
    servers = Server.objects.all()
    return render(request, 'home.html', {'servers': servers})

@login_required
@ssh_setup_required
def server(request):
    pass

@login_required
@ssh_setup_required
def task(request):
    pass

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

            is_connected, ssh_connection = connect_ssh(str(form.instance.ssh_server_address), 
                                                    str(form.instance.ssh_username), 
                                                    str(form.instance.ssh_server_port), 
                                                    tmp_ssh_key, 
                                                    str(form.instance.ssh_passphase))
                                 
            # Test connection                   
            if is_connected:
                if (is_puppet_running(ssh_connection)):
                    messages.info(request, 'Successfully connected to your server. A task to get system information has been initiated.')
                    # form.save()
                    return redirect('home')
                else:
                    messages.error(request, 'Puppet is not installed/running on your server. Please recheck again.')
            else:
                messages.error(request, 'Cannot connect to your server. Please check your connection.')

            if 'ssh_key' in request.FILES:
                delete_tmp_file(tmp_ssh_key)
    else:
        form = SetupSSHForm(instance=request.user.sshprofile)
    return render(request, 'account/setup_ssh.html', {'form': form, 'user': request.user})

@login_required
def config_password_done(request):
    messages.success(request, 'Your password has been successfully updated.')
    return redirect('home') 