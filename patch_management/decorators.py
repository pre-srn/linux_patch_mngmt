from django.shortcuts import redirect

def ssh_setup_required(function):
    def wrap(request, *args, **kwargs):
        if not request.user.sshprofile.ssh_server_address:
            return redirect('setup_ssh')
        else:
            return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap