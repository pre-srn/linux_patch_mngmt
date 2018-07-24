from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class SSHProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ssh_server_address = models.CharField(max_length=255, blank=True)
    ssh_server_port = models.PositiveSmallIntegerField(default=22, blank=True)
    ssh_username = models.CharField(max_length=30, blank=True)
    ssh_key = models.FileField(upload_to='uploaded_keys/')
    ssh_passphase = models.CharField(max_length=255, blank=True)

@receiver(post_save, sender=User)
def create_user_ssh_profile(sender, instance, created, **kwargs):
    if created:
        SSHProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_ssh_profile(sender, instance, **kwargs):
    instance.sshprofile.save()

class Server(models.Model):
    hostname = models.CharField(max_length=255)
    connected = models.BooleanField(default=False)
    server_os = models.CharField(max_length=255)
    server_version = models.CharField(max_length=255)
    owner = models.ForeignKey(User, related_name='servers', on_delete=models.CASCADE)

    class Meta:
        unique_together = (("hostname", "owner"),)

class Package(models.Model):
    name = models.CharField(max_length=255)
    current_version = models.CharField(max_length=255)
    new_version = models.CharField(max_length=255, null=True)
    server = models.ForeignKey(Server, related_name='packages', on_delete=models.CASCADE)