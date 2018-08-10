from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from ..views import home, register

class RegisterTests(TestCase):
    '''
    Testing/verifying the registration form
    '''
    def setUp(self):
        url = reverse('register')
        self.response = self.client.get(url)

    def test_signup_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_signup_url_resolves_signup_view(self):
        view = resolve('/account/register/')
        self.assertEquals(view.func, register)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, UserCreationForm)

class SuccessfulRegisterTests(TestCase):
    def setUp(self):
        url = reverse('register')
        data = {
            'username': 'johndoe',
            'password1': 'test1234',
            'password2': 'test1234'
        }
        self.response = self.client.post(url, data)
        self.setup_ssh_url = reverse('setup_ssh')

    def test_redirection(self):
        '''
        The user should be redirected to setup SSH connection after registered
        '''
        self.assertRedirects(self.response, self.setup_ssh_url)

    def test_user_creation(self):
        self.assertTrue(User.objects.exists())

    def test_user_authentication(self):
        '''
        Verifying the existence of the 'user' context
        '''
        response = self.client.get(self.setup_ssh_url)
        user = response.context.get('user')
        self.assertTrue(user.is_authenticated)


class InvalidSignUpTests(TestCase):
    def setUp(self):
        url = reverse('register')
        self.response = self.client.post(url, {})

    def test_signup_status_code(self):
        '''
        An invalid form submission should return to the same page
        '''
        self.assertEquals(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)

    def test_dont_create_user(self):
        self.assertFalse(User.objects.exists())

class LoginRequiredTests(TestCase):
    '''
    Testing login required on each page
    '''
    def setUp(self):
        self.login_url = reverse('login')

    def test_home_url_login_required(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_setup_ssh_login_required(self):
        url = reverse('setup_ssh')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_config_ssh_login_required(self):
        url = reverse('config_ssh')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_password_change_login_required(self):
        url = reverse('password_change')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_password_change_done_login_required(self):
        url = reverse('password_change_done')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_manage_system_url_login_required(self):
        url = reverse('manage_system', kwargs={
            'system_id': 1
        })
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_list_task_done_login_required(self):
        url = reverse('list_task')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_clear_task_login_required(self):
        url = reverse('clear_task')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_ajax_get_system_info_login_required(self):
        url = reverse('get_system_info')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))
        
    def test_ajax_update_package_login_required(self):
        url = reverse('update_package')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_ajax_update_all_packages_login_required(self):
        url = reverse('update_all_packages')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_ajax_scan_cve_login_required(self):
        url = reverse('scan_cve', kwargs={
            'system_id': 1
        })
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_ajax_scan_cve_all_systems_login_required(self):
        url = reverse('scan_cve_all_systems')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_ajax_get_system_info_table_login_required(self):
        url = reverse('get_system_info_table')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_ajax_get_installed_packages_table_login_required(self):
        url = reverse('get_installed_packages_table')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_ajax_get_outdated_packages_table_login_required(self):
        url = reverse('get_outdated_packages_table')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_ajax_get_cve_info_table_login_required(self):
        url = reverse('get_cve_info_table')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))

    def test_ajax_get_task_info_table_login_required(self):
        url = reverse('get_task_info_table')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))
        
    def test_ajax_check_task_status_login_required(self):
        url = reverse('check_task_status')
        response = self.client.get(url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=self.login_url, url=url))
