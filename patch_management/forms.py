from django import forms
from .models import SSHProfile

class SetupSSHForm(forms.ModelForm):

    class Meta:
        model = SSHProfile
        fields = ['ssh_server_address', 'ssh_server_port', 'ssh_username', 'ssh_key', 'ssh_passphase']
        labels = {
            "ssh_server_address": "SSH server address",
            "ssh_server_port": "SSH server port",
            "ssh_username": "SSH username",
            "ssh_key": "SSH private key",
            "ssh_passphase": "SSH key passphase",
        }

    def __init__(self, *args, **kwargs):
        # Force to require all fields
        super(SetupSSHForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True
