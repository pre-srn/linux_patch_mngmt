from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class SSHProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ssh_server_address = models.CharField(max_length=255, blank=True)
    ssh_server_port = models.PositiveSmallIntegerField(default=22, blank=True)
    ssh_username = models.CharField(max_length=255, blank=True)
    ssh_key = models.FileField(upload_to='uploaded_keys/')

@receiver(post_save, sender=User)
def create_user_ssh_profile(sender, instance, created, **kwargs):
    if created:
        SSHProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_ssh_profile(sender, instance, **kwargs):
    instance.sshprofile.save()

class System(models.Model):
    hostname = models.CharField(max_length=255)
    connected = models.BooleanField(default=True)
    system_os_name = models.CharField(max_length=255)
    system_os_version = models.CharField(max_length=255)
    system_kernel = models.CharField(max_length=255)
    owner = models.ForeignKey(User, related_name='systems', on_delete=models.CASCADE)

    class Meta:
        unique_together = (("hostname", "owner"),)

class Package(models.Model):
    name = models.CharField(max_length=255)
    current_version = models.CharField(max_length=255)
    new_version = models.CharField(max_length=255, null=True)
    active = models.BooleanField(default=True)
    system = models.ForeignKey(System, related_name='packages', on_delete=models.CASCADE)

    class Meta:
        unique_together = (("name", "system"),)
