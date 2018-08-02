from celery import shared_task
from .utils import *


@shared_task
def celery_ssh_run_get_system_info(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase, request_user_id):

    is_connected, ssh_conn = connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase)

    ssh_connected_systems   = ssh_conn.run('mco ping', hide=True)
    ssh_sys_info            = ssh_conn.run('mco shell run "(cat /etc/*-release && uname -msr) | sed \'/^\s*$/d\'"', hide=True)
    ssh_installed_packages  = ssh_conn.run('mco shell run "rpm -qa --qf \'%{NAME} %{VERSION}-%{RELEASE}\n\' || \
                                            dpkg-query -W -f=\'\${Package} \${Version}\n\'"', hide=True)
    ssh_available_updates   = ssh_conn.run('mco rpc package checkupdates', pty=True, hide=True)
    ssh_conn.close()

    connected_systems = process_ssh_res_connected_systems(ssh_connected_systems)
    sys_os_name, sys_os_ver, sys_kernel = process_ssh_res_sys_info(ssh_sys_info, connected_systems)
    installed_packages = process_ssh_res_installed_packages(ssh_installed_packages, connected_systems)
    available_updates = process_ssh_res_available_updates(ssh_available_updates, connected_systems)

    # Create or update all data
    save_system_information(connected_systems, request_user_id, sys_os_name, sys_os_ver, sys_kernel, installed_packages, available_updates)