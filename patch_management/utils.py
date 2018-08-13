import os
import tempfile
import json

from django.contrib.auth.models import User
from .models import System, Package, CVE
from fabric import Connection
from invoke import UnexpectedExit

def connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase):
    conn = Connection(host=ssh_addr, 
                    user=ssh_user, 
                    port=ssh_port,
                    connect_kwargs={
                        'key_filename': ssh_key, 
                        'passphrase': ssh_passphrase
                        },
                    connect_timeout="60"
                    )
    try:
        conn.run('uname -s', hide=True)
        conn.close()
        return True, conn
    except Exception:
        del conn
        return False, None


def is_puppet_running(ssh_conn):
    try:
        ssh_conn.run('puppet --version', hide=True)
        ssh_conn.run('mco ping', hide=True)
        ssh_conn.close()
        return True
    except UnexpectedExit:
        ssh_conn.close()
        return False


def save_system_information(connected_systems, request_user_id, sys_os_name, sys_os_ver, sys_kernel, package_manager, installed_packages, available_updates):
    request_user = User.objects.get(id=request_user_id)

    # Reset all connection states
    System.objects.filter(owner=request_user).update(connected = False)

    for connected_system in connected_systems:
        System.objects.update_or_create(hostname = connected_system, owner=request_user,
                                        defaults = {'connected': True, 
                                                    'system_os_name': sys_os_name[connected_system],
                                                    'system_os_version': sys_os_ver[connected_system], 
                                                    'system_kernel': sys_kernel[connected_system],
                                                    'system_package_manager': package_manager[connected_system]
                                                    }
                                        )

        cur_system = System.objects.get(hostname = connected_system, owner=request_user)
        cur_system.packages.all().update(active = False)

        for info in installed_packages[connected_system]:
            package_name = info[0]
            package_version = info[1]
            Package.objects.update_or_create(name = package_name, system = cur_system,
                defaults = {'active': True, 'current_version': package_version, 'new_version': None})

        for info in available_updates[connected_system]:
            package_name = info[0]
            package_version = info[1]
            Package.objects.filter(name = package_name, system = cur_system).update(new_version = package_version)


def process_ssh_res_connected_systems(ssh_connected_systems):
    connected_systems = []
    for line in ssh_connected_systems.stdout.split('\n'):
        line = line.strip()
        if len(line) == 0: break
        connected_systems.append(line.split(' ', 1)[0])
    return connected_systems


def process_ssh_res_sys_info(ssh_sys_info, connected_systems):
    sys_os_name = {}
    sys_os_ver = {}
    sys_kernel = {}

    ssh_sys_info_lines = iter(ssh_sys_info.stdout.split('\n'))
    for line in ssh_sys_info_lines: 
        line = line.strip()
        if line[:-1] in connected_systems: # managed-centos-0.server:
            cur_connected_system = line[:-1]
            prev_line = None
            while True:
                sys_info_line = next(ssh_sys_info_lines).strip()
                if len(sys_info_line) > 0:
                    if sys_info_line.startswith('PRETTY_NAME='):
                        sys_os_name[cur_connected_system] = sys_info_line.split('=', 2)[1].replace('"', '')
                    elif sys_info_line.startswith('VERSION='):
                        sys_os_ver[cur_connected_system] = sys_info_line.split('=', 2)[1].replace('"', '')
                else: 
                    sys_kernel[cur_connected_system] = prev_line
                    break
                prev_line = sys_info_line

    return sys_os_name, sys_os_ver, sys_kernel


def process_ssh_res_installed_packages(ssh_installed_packages, connected_systems):
    installed_packages = {}
    ssh_installed_package_lines = iter(ssh_installed_packages.stdout.split('\n'))
    for line in ssh_installed_package_lines:
        line = line.strip()
        if line[:-1] in connected_systems:
            cur_connected_system = line[:-1]
            install_package_info = []
            while True:
                package_line = next(ssh_installed_package_lines).strip()
                if (len(package_line) == 0 or package_line.startswith('STDERR:')): break
                package_info = package_line.split(' ', 2)
                package_name = package_info[0]
                package_version = package_info[1]
                if not package_name.startswith('gpg-pubkey'):
                    install_package_info.append([package_name, package_version])
            installed_packages[cur_connected_system] = install_package_info
    return installed_packages


def process_ssh_res_available_updates(ssh_available_updates, connected_systems):
    available_updates = {}
    package_manager = {}
    ssh_available_update_lines = iter(ssh_available_updates.stdout.split('\n'))
    for line in ssh_available_update_lines:
        line = line.strip() 
        if line in connected_systems: # managed-centos-0.server
            cur_connected_system = line
            available_update_result = ''
            available_update_info = []
            outdated_packages_found = False
            while True:
                available_update_line = next(ssh_available_update_lines).strip()
                if outdated_packages_found:
                    if available_update_line.startswith('Output:'): break
                    available_update_result = available_update_result + available_update_line
                elif available_update_line.startswith('Outdated Packages:'):
                    available_update_result = available_update_result + available_update_line.replace('Outdated Packages:', '')
                    outdated_packages_found = True
            # Convert the result Ruby data structure to JSON format
            available_update_result = available_update_result.replace(':package','"package"') \
                                                            .replace(':version','"version"')  \
                                                            .replace(':repo','"repo"')        \
                                                            .replace('=>',':')                \
                                                            .replace(' ','')
            available_update_json_array = json.loads(available_update_result)
            for update_info in available_update_json_array:
                package_name = update_info['package']
                package_version = update_info['version']
                if not package_name.startswith('gpg-pubkey'):
                    available_update_info.append([package_name, package_version])
            available_updates[cur_connected_system] = available_update_info
        elif line.startswith('Package Manager:'):
            package_manager[cur_connected_system] = line.split(':', 2)[1].strip()
    return available_updates, package_manager


def get_package_update_list(system_id):
    cur_system = System.objects.get(pk=system_id)
    packages = Package.objects.filter(system=cur_system, active=True, new_version__isnull=False)
    return packages


def check_package_update_result(package_name, available_updates):
    updated = True
    for available_update in available_updates:
        if package_name == available_update[0]:
            updated = False
            break
    return updated


def save_package_update_result(system_id, installed_packages, available_updates):
    cur_system = System.objects.get(pk=system_id)
    cur_system.packages.all().update(active = False)

    for info in installed_packages:
        package_name = info[0]
        package_version = info[1]
        Package.objects.update_or_create(name = package_name, system = cur_system,
            defaults = {'active': True, 'current_version': package_version, 'new_version': None})

    for info in available_updates:
        package_name = info[0]
        package_version = info[1]
        Package.objects.filter(name = package_name, system = cur_system).update(new_version = package_version)


def get_cve_package_list(request_user_id, system_id):
    result = {}
    if system_id is None:
        user = User.objects.get(pk=request_user_id)
        systems = System.objects.filter(owner=user, connected=True, system_package_manager='yum')
    else:
        systems = System.objects.filter(pk=system_id, system_package_manager='yum')

    for system in systems:
        packages = Package.objects.filter(system=system, active=True)
        package_list = []
        for package in packages:
            package_name_without_arch = package.name.split('.', 1)[0]
            package_list.append(
                [
                    package.id,
                    '{0}-{1}'.format(package_name_without_arch, package.current_version)
                ])
        result[system.id] = package_list
    return result


def save_cve_information(cve_info):
    for system_id in cve_info.keys():
        cur_system = System.objects.get(pk=system_id)
        CVE.objects.filter(system=cur_system).delete()
        cves = cve_info[system_id]
        for cve in cves:
            CVE.objects.create(
                cve_id = cve['cve_id'],
                description = cve['description'],
                cvss_v3 = cve['cvss3_score'],
                severity = cve['severity'],
                affected_package = cve['affected_package'],
                system = cur_system
            )


def create_tmp_file(input_file):
    tmp_name = next(tempfile._get_candidate_names()) + '.tmp'
    with open(tmp_name, 'wb+') as destination:
        for chunk in input_file.chunks():
            destination.write(chunk)
    return tmp_name


def delete_tmp_file(tmp_file):
    try:
        os.remove(tmp_file)
    except OSError:
        pass