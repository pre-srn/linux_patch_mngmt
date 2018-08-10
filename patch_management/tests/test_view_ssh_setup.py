from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User

from ..models import SSHProfile
from ..forms import SetupSSHForm

class SSHSetupTests(TestCase):
    '''
    Testing/verifying the SSH setup form
    '''
    def setUp(self):
        # Setup an account
        self.user = User.objects.create_user(username='johndoe', email='mail@example.com', password='test1234')
        self.client.login(username='johndoe', password='test1234')
        url = reverse('setup_ssh')
        self.response = self.client.get(url)

    def test_ssh_setup_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, SetupSSHForm)

    def test_contains_setup_message(self):
        self.assertContains(self.response, 'Welcome')
        self.assertContains(self.response, 'Please setup an SSH configuration to your Puppet master server')


class SSHSetupInvalidFormTests(TestCase):
    def setUp(self):
        # Setup an account
        self.user = User.objects.create_user(username='johndoe', email='mail@example.com', password='test1234')
        self.client.login(username='johndoe', password='test1234')
        # Submit an empty form
        url = reverse('setup_ssh')
        self.response = self.client.post(url, {})

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)

    def test_ssh_profile_hasnt_been_set(self):
        self.assertEqual(SSHProfile.objects.get(user=self.user).ssh_server_address, '')
    

class SSHConfigTests(TestCase):
    '''
    Testing/verifying the SSH config form
    '''
    def setUp(self):
        # Setup an account
        self.user = User.objects.create_user(username='johndoe', email='mail@example.com', password='test1234')
        self.client.login(username='johndoe', password='test1234')

        url = reverse('config_ssh')
        self.response = self.client.get(url)

    def test_ssh_setup_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, SetupSSHForm)

    def test_contains_setup_message(self):
        self.assertContains(self.response, 'SSH configuration')


class SSHConfigInvalidFormTests(TestCase):
    def setUp(self):
        # Setup an account
        self.user = User.objects.create_user(username='johndoe', email='mail@example.com', password='test1234')
        self.client.login(username='johndoe', password='test1234')
        # Submit an empty form
        url = reverse('config_ssh')
        self.response = self.client.post(url, {})

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)

    def test_ssh_profile_hasnt_been_set(self):
        self.assertEqual(SSHProfile.objects.get(user=self.user).ssh_server_address, '')
    

class SSHSetupRequiredTests(TestCase):
    '''
    Testing SSH setup required on each page for a new registered user
    '''
    def setUp(self):
        # Setup an account
        self.user = User.objects.create_user(username='johndoe', email='mail@example.com', password='test1234')
        self.client.login(username='johndoe', password='test1234')
        self.setup_ssh_url = reverse('setup_ssh')

    def test_home_url_ssh_setup_required(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_manage_system_url_ssh_setup_required(self):
        url = reverse('manage_system', kwargs={
            'system_id': 1
        })
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_list_task_url_ssh_setup_required(self):
        url = reverse('list_task')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_clear_task_url_ssh_setup_required(self):
        url = reverse('clear_task')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_clear_task_url_ssh_setup_required(self):
        url = reverse('clear_task')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_get_system_info_url_ssh_setup_required(self):
        url = reverse('get_system_info')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_update_package_url_ssh_setup_required(self):
        url = reverse('update_package')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_update_all_packages_url_ssh_setup_required(self):
        url = reverse('update_all_packages')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_scan_cve_url_ssh_setup_required(self):
        url = reverse('scan_cve', kwargs={
            'system_id': 1
        })
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_scan_cve_all_systems_url_ssh_setup_required(self):
        url = reverse('scan_cve_all_systems')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_get_system_info_table_url_ssh_setup_required(self):
        url = reverse('get_system_info_table')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_get_installed_packages_table_url_ssh_setup_required(self):
        url = reverse('get_installed_packages_table')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_get_outdated_packages_table_url_ssh_setup_required(self):
        url = reverse('get_outdated_packages_table')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_get_cve_info_table_url_ssh_setup_required(self):
        url = reverse('get_cve_info_table')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_get_task_info_table_url_ssh_setup_required(self):
        url = reverse('get_task_info_table')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)

    def test_ajax_check_task_status_url_ssh_setup_required(self):
        url = reverse('check_task_status')
        response = self.client.get(url)
        self.assertRedirects(response, self.setup_ssh_url)