from django.test import TestCase
from django.urls import reverse, resolve

from ..models import User, SSHProfile, System, Package, CVE
from ..tasks import celery_scan_cve

class CveScanViewTestCase(TestCase):
    '''
    Test CVE scanning function
    This test requires an internet connection to consume Redhat CVE public API 
    (https://access.redhat.com/labs/securitydataapi)
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

        # Setup System information
        self.system1 = System.objects.create(
            hostname='test1.server', 
            owner=self.user,
            connected=True,
            system_os_name= 'OS1_name',
            system_os_version= 'OS1_version',
            system_kernel= 'OS1_kernel_version',
            system_package_manager= 'yum' # Set to support RPM
        )
        self.system2 = System.objects.create(
            hostname='test2.server', 
            owner=self.user,
            connected=True,
            system_os_name= 'OS2_name',
            system_os_version= 'OS2_version',
            system_kernel= 'OS2_kernel_version',
            system_package_manager= 'apt' # Set to not support RPM
        )

        # Setup package information
        Package.objects.create(name='openssh.x86_64', current_version='7.4p1-16.el7', new_version=None, active=True, system=self.system1)
        Package.objects.create(name='openssh.x86_64', current_version='7.4p1-16.el7', new_version=None, active=True, system=self.system2)

    def test_scan_cve_all_systems(self):
        celery_scan_cve(self.user.id, None)
        cves_on_system1 = CVE.objects.filter(system=self.system1)
        cves_on_system2 = CVE.objects.filter(system=self.system2)
        '''
        Should find CVE info on system 1 as it uses RPM/YUM.
        Expected CVE-2017-15906 according to openssh-7.4p1-16.el7.
        (https://access.redhat.com/labs/securitydataapi/cve.json?package=openssh-7.4p1-16.el7)
        '''
        self.assertEquals(len(cves_on_system1), 1)
        self.assertEquals(cves_on_system1[0].cve_id, 'CVE-2017-15906')
        self.assertEquals(cves_on_system1[0].affected_package, 'openssh-7.4p1-16.el7')
        '''
        Should not find CVE info on system 2 as it doesn't use RPM/YUM.
        Thus the scan won't occur.
        '''
        self.assertEquals(len(cves_on_system2), 0)

    def test_scan_cve_on_RPM_supported_system(self):
        celery_scan_cve(self.user.id, self.system1.id)
        cves_on_system1 = CVE.objects.filter(system=self.system1)
        '''
        Should find CVE info on system 1 as it uses RPM/YUM.
        Expected CVE-2017-15906 according to openssh-7.4p1-16.el7.
        (https://access.redhat.com/labs/securitydataapi/cve.json?package=openssh-7.4p1-16.el7)
        '''
        self.assertEquals(len(cves_on_system1), 1)
        self.assertEquals(cves_on_system1[0].cve_id, 'CVE-2017-15906')
        self.assertEquals(cves_on_system1[0].affected_package, 'openssh-7.4p1-16.el7')

    def test_scan_cve_on_non_RPM_supported_system(self):
        celery_scan_cve(self.user.id, self.system2.id)
        cves_on_system2 = CVE.objects.filter(system=self.system2)
        '''
        Should not find CVE info on system 2 as it doesn't use RPM/YUM.
        Thus the scan won't occur.
        '''
        self.assertEquals(len(cves_on_system2), 0)