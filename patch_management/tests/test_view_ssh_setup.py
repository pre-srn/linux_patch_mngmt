from django.test import TestCase
from django.urls import reverse, resolve

from ..forms import SetupSSHForm
from ..views import setup_ssh

class SSHSetupTests(TestCase):
    '''
    Testing/verifying the SSH setup form
    '''
    def setUp(self):
        # Setup an account
        register_url = reverse('register')
        register_data = {
            'username': 'johndoe',
            'password1': 'test1234',
            'password2': 'test1234'
        }
        self.client.post(register_url, register_data)
        url = reverse('setup_ssh')
        self.response = self.client.get(url)

    def test_SSH_setup_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_SSH_setup_url_resolves_signup_view(self):
        view = resolve('/account/setup/ssh/')
        self.assertEquals(view.func, setup_ssh)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, SetupSSHForm)

class SSHSetupRequiredTests(TestCase):
    '''
    Testing SSH setup required on each page for a new registered user
    '''
    def setUp(self):
        # Setup an account
        register_url = reverse('register')
        register_data = {
            'username': 'johndoe',
            'password1': 'test1234',
            'password2': 'test1234'
        }
        self.client.post(register_url, register_data)
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