from django import forms
from .models import SSHProfile

class SetupSSHForm(forms.ModelForm):
    ssh_server_address = forms.CharField(required=True)
    ssh_server_port = forms.CharField(required=True)
    ssh_username = forms.CharField(required=True)
    ssh_passphase = forms.CharField(required=True)

    class Meta:
        model = SSHProfile
        fields = ['ssh_server_address', 'ssh_server_port', 'ssh_username', 'ssh_key', 'ssh_passphase']




# class NewMyModelForm(forms.ModelForm):
    
#     # name = forms.CharField(
#     #         widget=forms.TextInput(attrs={'autocomplete':'off'})
#     #     )

#     # description = forms.CharField(
#     #         widget=forms.TextInput(attrs={'autocomplete':'off'})
#     #     )

#     message = forms.CharField(
#         widget=forms.Textarea(
#             attrs={'rows': 5, 'placeholder': 'What is on your mind?'}
#         ),
#         max_length=4000,
#         help_text='The max length of the text is 4000.'
#     )

#     class Meta:
#         model = MyModel
#         fields = ['name', 'description', 'message']