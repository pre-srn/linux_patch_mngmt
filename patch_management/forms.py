from django import forms
from .models import SSHProfile

class SetupSSHForm(forms.ModelForm):
    ssh_passphrase = forms.CharField(widget=forms.PasswordInput,
                                    label ="SSH key passphrase",
                                    help_text="Note: This value will NOT be saved anywhere.")

    class Meta:
        model = SSHProfile
        fields = ['ssh_server_address', 'ssh_server_port', 'ssh_username', 'ssh_server_pub_key', 'ssh_key',]
        labels = {
            "ssh_server_address": "SSH server address",
            "ssh_server_port": "SSH server port",
            "ssh_username": "SSH username",
            "ssh_server_pub_key": "SSH server public key",
            "ssh_key": "SSH private key (for authentication)",
        }
        help_texts = {
            "ssh_username": "Note: This must be a non-root user who is allowed to run Mcollective commands",
            "ssh_server_pub_key": "Note: This key is for validating the server public key to prevent man-in-the-middle (MiTM) attacks. By default, the Ed25519 key is used."
        }

    def __init__(self, *args, **kwargs):
        # Force to require all fields
        super(SetupSSHForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True

class SSHPassphraseSubmitForm(forms.Form):
    ssh_passphrase = forms.CharField(widget=forms.PasswordInput, 
                    required=True, 
                    help_text="Please enter your SSH passphrase here. Note that this value will NOT be saved anywhere.")

class UpdateAllPackagesAjaxSubmitForm(forms.Form):
    system_id = forms.CharField(required=True)
    ssh_passphrase = forms.CharField(widget=forms.PasswordInput, required=True)

class UpdatePackageAjaxSubmitForm(forms.Form):
    system_id = forms.CharField(required=True)
    package_id = forms.CharField(required=True)
    ssh_passphrase = forms.CharField(widget=forms.PasswordInput, required=True)
