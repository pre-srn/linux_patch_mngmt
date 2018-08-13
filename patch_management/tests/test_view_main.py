from pytz import timezone
from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User

from ..forms import SSHPassphaseSubmitForm
from ..models import SSHProfile, System, Package, CVE


class HomeViewTestCase(TestCase):
    '''
    A base test case for Home view unit test
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

        url = reverse('home')
        self.response = self.client.get(url)


class HomeViewTests(HomeViewTestCase):
    '''
    Verifying Home view elements
    '''
    def setUp(self):
        super().setUp()

    def test_home_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_home_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, SSHPassphaseSubmitForm)

    def test_home_view_status_code(self):
        self.assertEquals(self.response.status_code, 200)


class HomeViewNoDataTests(HomeViewTestCase):
    '''
    Testing Home view with no data message
    '''
    def setUp(self):
        super().setUp()

    def test_home_view_message(self):
        self.assertContains(self.response, 'No Puppet/Mcollective system information.', 1)
        self.assertContains(self.response, 'Please initial a task to get system information first.', 1)


class HomeViewWithDataTests(HomeViewTestCase):
    '''
    Testing Home view with connected system data
    '''
    def setUp(self):
        super().setUp()

        # Setup System information
        self.system1 = System.objects.create(
            hostname='test1.server', 
            owner=self.user,
            connected=True,
            system_os_name= 'OS1_name',
            system_os_version= 'OS1_version',
            system_kernel= 'OS1_kernel_version',
            system_package_manager= 'OS1_package_manager'
        )
        self.system2 = System.objects.create(
            hostname='test2.server', 
            owner=self.user,
            connected=False,
            system_os_name= 'OS2_name',
            system_os_version= 'OS2_version',
            system_kernel= 'OS2_kernel_version',
            system_package_manager= 'OS2_package_manager'
        )

    def test_home_view_system_info_message(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, 'test1.server', 2)
        self.assertContains(response, 'OS1_name', 2)
        self.assertContains(response, 'OS1_version', 1)
        self.assertContains(response, 'OS1_kernel_version', 1)
        self.assertContains(response, 'OS1_package_manager', 1)

    def test_home_view_system_not_displaying_disconnected_systems(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertNotContains(response, 'test2.server')
        self.assertNotContains(response, 'OS2_name')
        self.assertNotContains(response, 'OS2_version')
        self.assertNotContains(response, 'OS2_kernel_version')
        self.assertNotContains(response, 'OS2_package_manager')

    def test_home_view_patch_information_message_low_priority(self):
        Package.objects.all().delete()
        CVE.objects.all().delete()
        for i in range(10):
            Package.objects.create(name='package{0}'.format(i+1), current_version='1', new_version='2', active=True, system=self.system1)
        Package.objects.create(name='package11', current_version='1', new_version=None, active=True, system=self.system1)
        Package.objects.create(name='package12', current_version='1', new_version=None, active=True, system=self.system1)

        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, '<span class="badge badge-secondary">', 1)
        self.assertContains(response, '10 updates available', 1)

    def test_home_view_patch_information_message_medium_priority(self):
        Package.objects.all().delete()
        CVE.objects.all().delete()
        for i in range(30):
            Package.objects.create(name='package{0}'.format(i+1), current_version='1', new_version='2', active=True, system=self.system1)
        Package.objects.create(name='package31', current_version='1', new_version=None, active=True, system=self.system1)
        Package.objects.create(name='package32', current_version='1', new_version=None, active=True, system=self.system1)

        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, '<span class="badge badge-warning">', 1)
        self.assertContains(response, '30 updates available', 1)

    def test_home_view_patch_information_message_high_priority(self):
        Package.objects.all().delete()
        CVE.objects.all().delete()
        for i in range(35):
            Package.objects.create(name='package{0}'.format(i+1), current_version='1', new_version='2', active=True, system=self.system1)
        Package.objects.create(name='package36', current_version='1', new_version=None, active=True, system=self.system1)
        Package.objects.create(name='package37', current_version='1', new_version=None, active=True, system=self.system1)

        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, '<span class="badge badge-danger">', 1)
        self.assertContains(response, '35 updates available', 1)

    def test_home_view_patch_information_message_cve_count(self):
        Package.objects.all().delete()
        CVE.objects.all().delete()
        for i in range(12):
            CVE.objects.create(cve_id='cve-{0}-{0}'.format(i+1), description='desc_test',cvss_v3=1.23,
            severity='low', affected_package='package1', system=self.system1)

        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, '12 CVEs', 1)

    def test_accessing_connected_system(self):
        url = reverse('manage_system', kwargs={'system_id': self.system1.id})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_accessing_disconnected_system(self):
        url = reverse('manage_system', kwargs={'system_id': self.system2.id})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_accessing_non_existed_system(self):
        url = reverse('manage_system', kwargs={'system_id': 99})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)


class ManageSystemViewTestCase(TestCase):
    '''
    A base test case for Manage System view unit test
    '''
    def setUp(self, total_mocked_package):
        # Setup a test account
        self.user = User.objects.create_user(username='johndoe', email='mail@example.com', password='test1234')
        self.client.login(username='johndoe', password='test1234')
        # Setup a test SSH profile
        ssh_setup_url = reverse('setup_ssh')
        sshProfile = SSHProfile.objects.get(pk=self.user.id)
        sshProfile.ssh_server_address = '127.0.0.1'
        sshProfile.ssh_username = 'test_user'
        sshProfile.save()

        # Setup System information
        self.system1 = System.objects.create(
            hostname='test1.server', 
            owner=self.user,
            connected=True,
            system_os_name= 'OS1_name',
            system_os_version= 'OS1_version',
            system_kernel= 'OS1_kernel_version',
            system_package_manager= 'OS1_package_manager'
        )

        for i in range(total_mocked_package):
            Package.objects.create(name='package{0}'.format(i+1), current_version='1', new_version=None, active=True, system=self.system1)

        url = reverse('manage_system', kwargs={'system_id': self.system1.id})
        self.response = self.client.get(url)


class ManageSystemViewTests(ManageSystemViewTestCase):
    '''
    Verifying Manage System view elements
    '''
    def setUp(self):
        super().setUp(total_mocked_package=35)

    def test_manage_system_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_manage_system_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, SSHPassphaseSubmitForm) 

    def test_manage_system_status_code(self):
        self.assertEquals(self.response.status_code, 200)


class ManageSystemViewNoDataTests(ManageSystemViewTestCase):
    '''
    Testing Manage System view with no data message
    '''
    def setUp(self):
        super().setUp(total_mocked_package=35)

    def test_manage_system_view_with_no_updates_message(self):
        self.assertContains(self.response, 'All packages are up-to-date.')

    def test_manage_system_view_with_no_cve_info_message(self):
        self.assertContains(self.response, 'No CVE information found.')
        self.assertContains(self.response, 'Please scan/re-scan the system to analyse CVE.')

    def test_manage_system_view_contains_install_packages_list(self):
        self.assertContains(self.response, '<td>1<', 35)
        for i in range(35):
            self.assertContains(self.response, '<td>package{0}<'.format(i+1), 1)


class ManageSystemViewWithUpdatesTests(ManageSystemViewTestCase):
    '''
    Testing Manage System view with available update information
    '''
    def setUp(self):
        super().setUp(total_mocked_package=0)

        for i in range(5):
            Package.objects.create(name='package{0}'.format(i+1), current_version='1', new_version='2', active=True, system=self.system1)

    def test_manage_system_view_with_updates(self):
        url = reverse('manage_system', kwargs={'system_id': self.system1.id})
        response = self.client.get(url)
        for i in range(5):
            self.assertContains(response, 'package{0}'.format(i+1), 3)


class ManageSystemViewWithCveInfoTests(ManageSystemViewTestCase):
    '''
    Testing Manage System view with CVE information
    '''
    def setUp(self):
        super().setUp(total_mocked_package=35)
        
        # Setup test CVE information
        for i in range(20):
            if i < 5:
                CVE.objects.create(cve_id='cve-{0}-{0}'.format(i+1), description='desc_test', cvss_v3=1.23,
                severity='low', affected_package='package1-cve', system=self.system1)
            elif i < 10:
                CVE.objects.create(cve_id='cve-{0}-{0}'.format(i+1), description='desc_test', cvss_v3=1.23,
                severity='moderate', affected_package='package2-cve', system=self.system1)
            elif i < 15:
                CVE.objects.create(cve_id='cve-{0}-{0}'.format(i+1), description='desc_test', cvss_v3=1.23,
                severity='important', affected_package='package3-cve', system=self.system1)
            else:
                CVE.objects.create(cve_id='cve-{0}-{0}'.format(i+1), description='desc_test', cvss_v3=1.23,
                severity='critical', affected_package='package4-cve', system=self.system1)
        
    def test_manage_system_view_with_cve_info(self):
        url = reverse('manage_system', kwargs={'system_id': self.system1.id})
        response = self.client.get(url)
        self.assertContains(response, 'package1-cve', 10)
        self.assertContains(response, 'package2-cve', 10)
        self.assertContains(response, 'package3-cve', 10)
        self.assertContains(response, 'package4-cve', 10)
        self.assertContains(response, '1.23', 40)
        self.assertContains(response, 'Desc_test', 20)
        for i in range(20):
            self.assertContains(response, 'cve-{0}-{0}'.format(i+1), 2)

    def test_manage_system_view_with_cve_severity_label_colour(self):
        url = reverse('manage_system', kwargs={'system_id': self.system1.id})
        response = self.client.get(url)
        self.assertContains(response, '<span class="badge badge-secondary">', 5)
        self.assertContains(response, '<span class="badge badge-warning">', 5)
        self.assertContains(response, '<span class="badge badge-danger">', 10)
        self.assertContains(response, 'Low', 10)
        self.assertContains(response, 'Moderate', 10)
        self.assertContains(response, 'Important', 10)
        self.assertContains(response, 'Critical', 10)

    def test_manage_system_view_cve_scanned_datetime(self):
        url = reverse('manage_system', kwargs={'system_id': self.system1.id})
        scanned_date = self.system1.get_cves_scanned_date()
        expected_datetime = scanned_date.astimezone(timezone('Europe/London')).strftime('%d/%m/%Y %H:%M:%S')
        response = self.client.get(url)
        self.assertContains(response, expected_datetime)