from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class SSHProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ssh_server_address = models.CharField(max_length=255, blank=True)
    ssh_server_port = models.PositiveSmallIntegerField(default=22, blank=True)
    ssh_username = models.CharField(max_length=30, blank=True)
    ssh_key = models.TextField(blank=True) 
    ssh_passphase = models.CharField(max_length=255, blank=True)

@receiver(post_save, sender=User)
def create_user_ssh_profile(sender, instance, created, **kwargs):
    if created:
        SSHProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_ssh_profile(sender, instance, **kwargs):
    instance.sshprofile.save()

class Server(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, related_name='servers', on_delete=models.CASCADE)





class MyModel(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    message = models.TextField(null=True)

    def __str__(self):
        return self.name