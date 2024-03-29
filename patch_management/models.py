import ast
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_results.models import TaskResult

class SSHProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ssh_server_address = models.CharField(max_length=255, blank=True)
    ssh_server_port = models.PositiveSmallIntegerField(default=22, blank=True)
    ssh_username = models.CharField(max_length=255, blank=True)
    ssh_server_pub_key = models.FileField(upload_to='uploaded_keys/')
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
    system_package_manager = models.CharField(max_length=255)
    owner = models.ForeignKey(User, related_name='systems', on_delete=models.CASCADE)

    class Meta:
        unique_together = (("hostname", "owner"),)

    def get_available_updates_count(self):
        return Package.objects.filter(system=self, active=True, new_version__isnull=False).count()

    def get_cves_count(self):
        return CVE.objects.filter(system=self).count()

    def get_cves_scanned_date(self):
        cve = CVE.objects.filter(system=self).order_by('-scanned_at')[0]
        return cve.scanned_at

    def __str__(self):
        return self.hostname

class Package(models.Model):
    name = models.CharField(max_length=255)
    current_version = models.CharField(max_length=255)
    new_version = models.CharField(max_length=255, null=True)
    active = models.BooleanField(default=True)
    system = models.ForeignKey(System, related_name='packages', on_delete=models.CASCADE)

    class Meta:
        unique_together = (("name", "system"),)

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.current_version)

class CVE(models.Model):
    cve_id = models.CharField(max_length=255)
    description = models.TextField()
    cvss_v3 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    severity = models.CharField(max_length=20)
    scanned_at = models.DateTimeField(auto_now_add=True)
    affected_package = models.CharField(max_length=255, blank=True)
    system = models.ForeignKey(System, related_name='cves', on_delete=models.CASCADE)

    class Meta:
        unique_together = (("cve_id", "system"),)

    def __str__(self):
        return '{0} on {1}'.format(self.cve_id, self.system.hostname)

class Task(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    task_name = models.CharField(max_length=255)
    started_at = models.DateTimeField(auto_now_add=True)
    is_notified = models.BooleanField(default=False)
    initiated_by = models.ForeignKey(User, related_name='tasks', on_delete=models.CASCADE)

    def get_task_status(self):
        try:
            taskResult = TaskResult.objects.get(task_id=self.task_id)
            return taskResult.status
        except TaskResult.DoesNotExist:
            return 'RUNNING'

    def get_task_result(self):
        try:
            taskResult = TaskResult.objects.get(task_id=self.task_id)
            if taskResult.result == 'null':
                return '-'
            else:
                result = ast.literal_eval(taskResult.result)
                return result['exc_message'][0]
        except TaskResult.DoesNotExist:
            return '-'

    def get_task_date_done(self):
        try:
            taskResult = TaskResult.objects.get(task_id=self.task_id)
            return taskResult.date_done
        except TaskResult.DoesNotExist:
            return '-'

    def __str__(self):
        return self.task_id
