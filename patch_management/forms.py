from django import forms
from .models import SSHProfile

class SetupSSHForm(forms.ModelForm):
    ssh_passphase = forms.CharField(widget=forms.PasswordInput,
                                    label ="SSH key passphase",
                                    help_text="Note: This value will NOT be saved anywhere.")

    class Meta:
        model = SSHProfile
        fields = ['ssh_server_address', 'ssh_server_port', 'ssh_username', 'ssh_key']
        labels = {
            "ssh_server_address": "SSH server address",
            "ssh_server_port": "SSH server port",
            "ssh_username": "SSH username",
            "ssh_key": "SSH private key",
        }
        help_texts = {
            "ssh_username": "Note: This must be a non-root user who is allowed to run Mcollective commands"
        }

    def __init__(self, *args, **kwargs):
        # Force to require all fields
        super(SetupSSHForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True

class SSHPassphaseSubmitForm(forms.Form):
    ssh_passphase = forms.CharField(widget=forms.PasswordInput, required=True, help_text="Please enter your SSH passphase here. Note that this value will NOT be saved anywhere.")
