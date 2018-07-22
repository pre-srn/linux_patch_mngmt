from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from .models import Server, SSHProfile
from .forms import SetupSSHForm
from .utils import *

@login_required
# TODO add my own @....
def home(request):
    if not request.user.sshprofile.ssh_server_address:
        return redirect('setup_ssh')
    servers = Server.objects.all()
    return render(request, 'home.html', {'servers': servers})

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
def setup_ssh(request):
    if request.method == 'POST':
        form = SetupSSHForm(request.POST, request.FILES, instance=request.user.sshprofile)
        if form.is_valid():

            # Test connection
            if 'ssh_key' in request.FILES:
                tmp_filename = create_tmp_file(request.FILES['ssh_key'])
            else:
                tmp_filename = str(form.instance.ssh_key)
            
            if test_ssh_connection(form, tmp_filename):
                messages.success(request, 'Successfully connected to your server')
                # form.save()
                return redirect('home')  
            else:
                messages.error(request, 'Cannot connect to your server. Please check your connection.')

            if 'ssh_key' in request.FILES:
                delete_tmp_file(tmp_filename)
    else:
        form = SetupSSHForm(instance=request.user.sshprofile)
    return render(request, 'account/setup_ssh.html', {'form': form, 'user': request.user})

@login_required
def config_password_done(request):
    messages.success(request, 'Your password has been successfully updated.')
    return redirect('home') 