from pytz import timezone
from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User

from ..models import SSHProfile, Task, TaskResult

class TaskViewTestCase(TestCase):
    '''
    A base test case of Task view
    '''
    def setUp(self):
        # Setup a test account
        self.user = User.objects.create_user(username='johndoe', email='mail@example.com', password='test1234')
        self.client.login(username='johndoe', password='test1234')
        # Setup a test SSH profile
        ssh_setup_url = reverse('setup_ssh')
        sshProfile = SSHProfile.objects.get(pk=self.user.id)
        sshProfile.ssh_server_address = '127.0.0.1'
        sshProfile.ssh_username = 'test_user'
        sshProfile.save()

        url = reverse('list_task')
        self.response = self.client.get(url)


class TaskViewTests(TaskViewTestCase):
    '''
    Verifying Task view
    '''
    def setUp(self):
        super().setUp()

    def test_task_view_status_code(self):
        self.assertEquals(self.response.status_code, 200)


class TaskViewNoDataTests(TaskViewTestCase):
    '''
    Testing Task view with no data message
    '''
    def setUp(self):
        super().setUp()

    def test_task_view_no_data_message(self):
        self.assertContains(self.response, 'Currently, there is no task information.')


class TaskViewWithDataTests(TaskViewTestCase):
    '''
    Testing Task view with task data
    '''
    def setUp(self):
        super().setUp()

        for i in range(5):
            Task.objects.create(task_id='task_id_{0}'.format(i+1), task_name='task_name_{0}'.format(i+1), initiated_by=self.user)

    def test_running_task_view_with_data_message(self):
        url = reverse('list_task')
        response = self.client.get(url)
        self.assertContains(response, '<span class="badge badge-info">RUNNING</span>', 5)
        for i in range(5):
            self.assertContains(response, 'task_id_{0}'.format(i+1), 1)
            self.assertContains(response, 'task_name_{0}'.format(i+1), 1)

    def test_task_view_with_result_message(self):
        TaskResult.objects.all().delete()
        TaskResult.objects.create(task_id='task_id_1', status='SUCCESS', result={'exc_message':['task_id_1_success']})
        TaskResult.objects.create(task_id='task_id_2', status='FAILURE', result={'exc_message':['task_id_2_failure']})
        url = reverse('list_task')
        response = self.client.get(url)
        self.assertContains(response, '<span class="badge badge-success">SUCCESS</span>', 1)
        self.assertContains(response, '<span class="badge badge-danger">FAILURE</span>', 1)
        self.assertContains(response, '<span class="badge badge-info">RUNNING</span>', 3)
        self.assertContains(response, 'task_id_1_success', 1)
        self.assertContains(response, 'task_id_2_failure', 1)

    def test_task_view_clear_task(self):
        '''
        Testing clear completed tasks 
        '''
        TaskResult.objects.all().delete()
        TaskResult.objects.create(task_id='task_id_1', status='SUCCESS', result={'exc_message':['task_id_1_success']})
        TaskResult.objects.create(task_id='task_id_2', status='FAILURE', result={'exc_message':['task_id_2_failure']})
        Task.objects.filter(task_id='task_id_1').update(is_notified=True)
        Task.objects.filter(task_id='task_id_2').update(is_notified=True)

        # Clearing tasks
        clear_task_url = reverse('clear_task')
        self.client.get(clear_task_url)
        list_task_url = reverse('list_task')
        response = self.client.get(list_task_url)
        self.assertContains(response, 'All completed tasks have been cleared.', 1)
        self.assertNotContains(response, '<span class="badge badge-success">SUCCESS</span>')
        self.assertNotContains(response, '<span class="badge badge-danger">FAILURE</span>')
        self.assertContains(response, '<span class="badge badge-info">RUNNING</span>', 3)
        self.assertContains(response, 'task_id_3', 1)
        self.assertContains(response, 'task_name_3', 1)
        self.assertContains(response, 'task_id_4', 1)
        self.assertContains(response, 'task_name_4', 1)
        self.assertContains(response, 'task_id_5', 1)
        self.assertContains(response, 'task_name_5', 1)