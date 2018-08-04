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
            raise ConnectionError('Network connection / command error.')

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
def celery_ssh_run_update_package(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase, package_id, package_name, system_id, system_hostname):
    is_connected, ssh_conn = connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase)

    if is_connected:
        try:
            ssh_conn.run('mco rpc package update package={0} -I {1}'.format(package_name, system_hostname), pty=True, hide=True)
            ssh_installed_packages = ssh_conn.run('mco shell run "rpm -qa --qf \'%{{NAME}}.%{{ARCH}} %{{VERSION}}-%{{RELEASE}}\n\' || \
                                                   dpkg-query -W -f=\'\${{Package}} \${{Version}}\n\'" -I {0}'.format(system_hostname), hide=True)
            ssh_available_updates  = ssh_conn.run('mco rpc package checkupdates -I {0}'.format(system_hostname), pty=True, hide=True)
            ssh_conn.close()
        except Exception:
            raise ConnectionError('Network connection / command error')
        
        installed_packages = process_ssh_res_installed_packages(ssh_installed_packages, [system_hostname])
        available_updates = process_ssh_res_available_updates(ssh_available_updates, [system_hostname])

        # Checking the update result
        updated = check_package_update_result(package_name, available_updates[system_hostname])
        if updated:
            save_package_update_result(system_id, installed_packages[system_hostname], available_updates[system_hostname])
        else:
            raise SystemError('Puppet/Mcollective update process error.')

    else:
        raise ConnectionError('Cannot connect to your Puppet master server. Your server may unavailable or your SSH passphase may incorrect.')
    return

@shared_task
def celery_ssh_run_update_all_packages(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase, system_id, system_hostname):
    is_connected, ssh_conn = connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase)

    if is_connected:
        packages = get_package_update_list(system_id)
        try:
            for package in packages:
                ssh_conn.run('mco rpc package update package={0} -I {1}'.format(package.name, system_hostname), pty=True, hide=False)

            ssh_installed_packages = ssh_conn.run('mco shell run "rpm -qa --qf \'%{{NAME}}.%{{ARCH}} %{{VERSION}}-%{{RELEASE}}\n\' || \
                                                   dpkg-query -W -f=\'\${{Package}} \${{Version}}\n\'" -I {0}'.format(system_hostname), hide=True)
            ssh_available_updates  = ssh_conn.run('mco rpc package checkupdates -I {0}'.format(system_hostname), pty=True, hide=False)
            ssh_conn.close()
        except Exception:
            raise ConnectionError('Network connection / command error.')
        
        installed_packages = process_ssh_res_installed_packages(ssh_installed_packages, [system_hostname])
        available_updates = process_ssh_res_available_updates(ssh_available_updates, [system_hostname])

        # Checking the update result
        if len(available_updates[system_hostname]) == 0:
            save_package_update_result(system_id, installed_packages[system_hostname], available_updates[system_hostname])
        else:
            raise SystemError('Puppet/Mcollective update process error.')

    else:
        raise ConnectionError('Cannot connect to your Puppet master server. Your server may unavailable or your SSH passphase may incorrect.')
    return