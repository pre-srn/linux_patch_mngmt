from celery import shared_task
from .utils import *

@shared_task
def celery_ssh_run_get_system_info(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase, request_user_id):
    is_connected, ssh_conn = connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase)

    if is_connected:
        try:
            ssh_connected_systems   = ssh_conn.run('mco ping', hide=True)
            ssh_sys_info            = ssh_conn.run('mco shell run "(cat /etc/*-release && uname -msr) | sed \'/^\s*$/d\'"', hide=True)
            ssh_installed_packages  = ssh_conn.run('mco shell run "rpm -qa --qf \'%{NAME}.%{ARCH} %{VERSION}-%{RELEASE}\n\' || \
                                                    dpkg-query -W -f=\'\${Package} \${Version}\n\'"', hide=True)
            ssh_available_updates   = ssh_conn.run('mco rpc package checkupdates', pty=True, hide=True)
            ssh_conn.close()
        except Exception:
            raise ConnectionError('Network connection error.')

        # Getting STDOUT from each SSH command and converting them to Python data structure
        connected_systems = process_ssh_res_connected_systems(ssh_connected_systems)
        sys_os_name, sys_os_ver, sys_kernel = process_ssh_res_sys_info(ssh_sys_info, connected_systems)
        installed_packages = process_ssh_res_installed_packages(ssh_installed_packages, connected_systems)
        available_updates = process_ssh_res_available_updates(ssh_available_updates, connected_systems)

        # Save all system information data
        save_system_information(connected_systems, request_user_id, sys_os_name, sys_os_ver, sys_kernel, installed_packages, available_updates)
    else:
        raise ConnectionError('Cannot connect to your Puppet master server. Your server may unavailable or your SSH passphase may incorrect.')
    return

@shared_task
def celery_ssh_run_update_package(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase, package_id, package_name, system_hostname):
    is_connected, ssh_conn = connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase)

    if is_connected:
        try:
            update_result = ssh_conn.run('mco rpc package update package=' + package_name + ' -I ' + system_hostname, pty=True, hide=True)
            ssh_conn.close()
        except Exception:
            raise ConnectionError('Network connection error.')
        
        package_version = get_update_package_result(update_result)
        if (is_package_updated(package_id, package_version)):
            save_package_update_result(package_id, package_version)
        else:
            raise SystemError('Puppet/Mcollective update process error.')
    else:
        raise ConnectionError('Cannot connect to your Puppet master server. Your server may unavailable or your SSH passphase may incorrect.')
    return