from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from .models import Server
from .forms import SetupSSHForm

@login_required
def home(request):
    if not request.user.sshprofile.ssh_server_address:
        return redirect('setup_ssh')
    servers = Server.objects.all()
    return render(request, 'home.html', {'servers': servers})

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
def setup_ssh(request):
    user = request.user
    if request.method == 'POST':
        form = SetupSSHForm(request.POST)
        if form.is_valid():
            # topic = form.save()
            return redirect('home')  
    else:
        form = SetupSSHForm(instance=user.sshprofile)
    return render(request, 'account/setup_ssh.html', {'form': form, 'user': user})

@login_required
def config_password_done(request):
    messages.success(request, 'Your password has been successfully updated.')
    return redirect('home') 