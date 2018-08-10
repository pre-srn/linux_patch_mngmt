from django.test import TestCase

from fabric.runners import Result as SSHResult
from ..utils import *

class TestSSHProcesses(TestCase):
    def setUp(self):
        self.expected_connected_systems = ['puppet-master.server', 'managed.server']
        self.expected_system_os_name = {
            'puppet-master.server': 'CentOS Linux 7 (Core)', 
            'managed.server'      : 'Ubuntu 16.04.4 LTS'
            }
        self.expected_system_os_version = {
            'puppet-master.server': '7 (Core)',
            'managed.server'      : '16.04.4 LTS (Xenial Xerus)'
            }
        self.expected_system_kernel = {
            'puppet-master.server': 'Linux 3.10.0-862.2.3.el7.x86_64 x86_64', 
            'managed.server'      : 'Linux 4.4.0-127-generic x86_64'
            }
        self.expected_installed_packages = {
            'puppet-master.server': [
                                    ['app-1', '4.01-17.el7'],
                                    ['app-2', '7.4p1-16.el7'],
                                    ['app-3', '1.10.2-13.el7']
                                    ],
            'managed.server':       [
                                    ['app-1', '5.4.0-6ubuntu1~16.04.10'], 
                                    ['app-2', '1:2.4.47-2'],
                                    ['app-3', '1:7.2p2-4ubuntu2.4'],
                                    ['app-4', '1:9.9p2-4ubuntu2.4']
                                    ]
            }
        self.expected_available_updates = {
            'puppet-master.server': [['app-1', '1:9.9.9']],
            'managed.server':       [['app-2', '1:9.9.9'], 
                                     ['app-3', '1:9.1.2']]
            }
        self.expected_package_managers = {
            'puppet-master.server': 'yum',
            'managed.server':       'apt'
            }

    def test_process_ssh_res_connected_systems(self):
        ssh_result = SSHResult(connection=None, 
        stdout='\
puppet-master.server                     time=124.04 ms\n\
managed.server                           time=119.36 ms\n\
\n\
\n\
---- ping statistics ----\n\
2 replies max: 124.04 min: 119.36 avg: 121.70\n')

        connected_systems = process_ssh_res_connected_systems(ssh_result)
        self.assertEquals(connected_systems, self.expected_connected_systems)

    def test_process_ssh_res_sys_info(self):
        ssh_result = SSHResult(connection=None, 
        stdout='\
\n\
2 / 2\n\
\n\
managed.server:\n\
DISTRIB_ID=Ubuntu\n\
DISTRIB_RELEASE=16.04\n\
DISTRIB_CODENAME=xenial\n\
DISTRIB_DESCRIPTION="Ubuntu 16.04.4 LTS"\n\
NAME="Ubuntu"\n\
VERSION="16.04.4 LTS (Xenial Xerus)"\n\
ID=ubuntu\n\
ID_LIKE=debian\n\
PRETTY_NAME="Ubuntu 16.04.4 LTS"\n\
VERSION_ID="16.04"\n\
HOME_URL="http://www.ubuntu.com/"\n\
SUPPORT_URL="http://help.ubuntu.com/"\n\
BUG_REPORT_URL="http://bugs.launchpad.net/ubuntu/"\n\
VERSION_CODENAME=xenial\n\
UBUNTU_CODENAME=xenial\n\
Linux 4.4.0-127-generic x86_64\n\
\n\
puppet-master.server:\n\
CentOS Linux release 7.5.1804 (Core)\n\
NAME="CentOS Linux"\n\
VERSION="7 (Core)"\n\
ID="centos"\n\
ID_LIKE="rhel fedora"\n\
VERSION_ID="7"\n\
PRETTY_NAME="CentOS Linux 7 (Core)"\n\
ANSI_COLOR="0;31"\n\
CPE_NAME="cpe:/o:centos:centos:7"\n\
HOME_URL="https://www.centos.org/"\n\
BUG_REPORT_URL="https://bugs.centos.org/"\n\
CENTOS_MANTISBT_PROJECT="CentOS-7"\n\
CENTOS_MANTISBT_PROJECT_VERSION="7"\n\
REDHAT_SUPPORT_PRODUCT="centos"\n\
REDHAT_SUPPORT_PRODUCT_VERSION="7"\n\
CentOS Linux release 7.5.1804 (Core)\n\
CentOS Linux release 7.5.1804 (Core)\n\
Linux 3.10.0-862.2.3.el7.x86_64 x86_64\n\
\n\
\n\
Finished processing ?[32m2?[0m / ?[32m2?[0m hosts in 129.34 ms\n\
')
        system_os_name, system_os_version, system_kernel = process_ssh_res_sys_info(ssh_result, self.expected_connected_systems)
        self.assertDictEqual(system_os_name, self.expected_system_os_name)
        self.assertDictEqual(system_os_version, self.expected_system_os_version)
        self.assertDictEqual(system_kernel, self.expected_system_kernel)

    def test_process_ssh_res_installed_packages(self):
        ssh_result = SSHResult(connection=None,
        stdout='\
\n\
2 / 2\n\
\n\
managed.server:\n\
app-1 5.4.0-6ubuntu1~16.04.10\n\
app-2 1:2.4.47-2\n\
app-3 1:7.2p2-4ubuntu2.4\n\
app-4 1:9.9p2-4ubuntu2.4\n\
    STDERR:\n\
sh: 1: rpm: not found\n\
\n\
puppet-master.server:\n\
app-1 4.01-17.el7\n\
app-2 7.4p1-16.el7\n\
app-3 1.10.2-13.el7\n\
\n\
\n\
\n\
Finished processing ?[32m2?[0m / ?[32m2?[0m hosts in 1166.34 ms\n\
')
        installed_packages = process_ssh_res_installed_packages(ssh_result, self.expected_connected_systems)
        self.assertDictEqual(installed_packages, self.expected_installed_packages)
        
    def test_process_ssh_res_available_updates(self):
        ssh_result = SSHResult(connection=None,
        stdout='\
Discovering hosts using the mc method for 2 second(s) .... 2\n\
\n\
 ?[32m*?[0m [ ============================================================> ] 2 / 2\n\
\n\
\n\
managed.server\n\
           Exit Code: 0\n\
   Outdated Packages: [{:package=>"app-2",\n\
                        :version=>"1:9.9.9",\n\
                        :repo=>"Ubuntu:16.04/xenial-updates [amd64]"},\n\
                       {:package=>"app-3",\n\
                        :version=>"1:9.1.2",\n\
                        :repo=>"Ubuntu:16.04/xenial-updates [amd64]"}]\n\
              Output: Reading package lists...\n\
     Package Manager: apt\n\
\n\
puppet-master.server\n\
           Exit Code: 100\n\
   Outdated Packages: [{:package=>"app-1",\n\
                        :version=>"1:9.9.9",\n\
                        :repo=>"updates"}]\n\
              Output:\n\
                      app-1               1:9.9.9                    updates\n\
     Package Manager: yum\n\
\n\
\n\
\n\
Finished processing ?[32m2?[0m / ?[32m2?[0m hosts in 3142.49 ms\n\
')
        available_updates, package_managers = process_ssh_res_available_updates(ssh_result, self.expected_connected_systems)
        self.assertDictEqual(available_updates, self.expected_available_updates)
        self.assertDictEqual(package_managers, self.expected_package_managers)
