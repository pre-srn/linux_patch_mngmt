import requests
from celery import shared_task
from .utils import *

@shared_task
def celery_ssh_run_get_system_info(ssh_addr, ssh_user, ssh_port, ssh_server_pub_key, ssh_key, ssh_passphrase, request_user_id):
    is_connected, key_match, ssh_conn = connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_server_pub_key, ssh_key, ssh_passphrase)

    if is_connected:
        if key_match:
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
            available_updates, package_manager = process_ssh_res_available_updates(ssh_available_updates, connected_systems)

            # Save all system information data
            save_system_information(connected_systems, request_user_id, sys_os_name, sys_os_ver, sys_kernel, 
                                    package_manager, installed_packages, available_updates)
        else:
            raise ConnectionError("Server public key doesn't match. Please verify your server authenticity again.")
    else:
        raise ConnectionError('Cannot connect to your Puppet master server. Your server may be unavailable or \
                               your SSH passphrase may be invalid.')
    return
    
@shared_task
def celery_ssh_run_update_package(ssh_addr, ssh_user, ssh_port, ssh_server_pub_key, ssh_key, ssh_passphrase, package_id,
    package_name, system_id, system_hostname):

    is_connected, key_match, ssh_conn = connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_server_pub_key, ssh_key, ssh_passphrase)

    if is_connected:
        if key_match:
            try:
                ssh_connected_systems = ssh_conn.run('mco ping', hide=True)
            except Exception:
                raise ConnectionError('Network connection / command error')

            # Checking whether a system is connected or not
            connected_systems = process_ssh_res_connected_systems(ssh_connected_systems)
            if system_hostname not in connected_systems:
                raise ConnectionError('Cannot connect to {0}. The server may be unavailable or has disconnected.'.format(system_hostname))
            try: # Updating a package
                ssh_conn.run('mco rpc package update package={0} -I {1}'.format(package_name, system_hostname), pty=True, hide=True)
                ssh_installed_packages = ssh_conn.run('mco shell run "rpm -qa --qf \'%{{NAME}}.%{{ARCH}} %{{VERSION}}-%{{RELEASE}}\n\' || \
                                                    dpkg-query -W -f=\'\${{Package}} \${{Version}}\n\'" -I {0}'.format(system_hostname), hide=True)
                ssh_available_updates  = ssh_conn.run('mco rpc package checkupdates -I {0}'.format(system_hostname), pty=True, hide=True)
                ssh_conn.close()
            except Exception:
                raise ConnectionError('Network connection / command error')
            
            installed_packages = process_ssh_res_installed_packages(ssh_installed_packages, [system_hostname])
            available_updates, package_manager = process_ssh_res_available_updates(ssh_available_updates, [system_hostname])

            # Checking the update result
            updated = check_package_update_result(package_name, available_updates[system_hostname])
            if updated:
                save_package_update_result(system_id, installed_packages[system_hostname], available_updates[system_hostname])
            else:
                raise SystemError('Puppet/Mcollective update process error.')
        else:
            raise ConnectionError("Server public key doesn't match. Please verify your server authenticity again.")
    else:
        raise ConnectionError('Cannot connect to your Puppet master server. Your server may be unavailable \
         or your SSH passphrase may be invalid.')
    return

@shared_task
def celery_ssh_run_update_all_packages(ssh_addr, ssh_user, ssh_port, ssh_server_pub_key, ssh_key, ssh_passphrase, system_id, system_hostname):
    is_connected, key_match, ssh_conn = connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_server_pub_key, ssh_key, ssh_passphrase)

    if is_connected:
        if key_match:
            try:
                ssh_connected_systems = ssh_conn.run('mco ping', hide=True)
            except Exception:
                raise ConnectionError('Network connection / command error')
                
            connected_systems = process_ssh_res_connected_systems(ssh_connected_systems)
            if system_hostname not in connected_systems:
                raise ConnectionError('Cannot connect to {0}. The server may be unavailable or has disconnected.'.format(system_hostname))

            packages = get_package_update_list(system_id)
            try:
                for package in packages:
                    ssh_conn.run('mco rpc package update package={0} -I {1}'.format(package.name, system_hostname), pty=True, hide=True)

                ssh_installed_packages = ssh_conn.run('mco shell run "rpm -qa --qf \'%{{NAME}}.%{{ARCH}} %{{VERSION}}-%{{RELEASE}}\n\' || \
                                                    dpkg-query -W -f=\'\${{Package}} \${{Version}}\n\'" -I {0}'.format(system_hostname), hide=True)
                ssh_available_updates  = ssh_conn.run('mco rpc package checkupdates -I {0}'.format(system_hostname), pty=True, hide=True)
                ssh_conn.close()
            except Exception:
                raise ConnectionError('Network connection / command error.')
            
            installed_packages = process_ssh_res_installed_packages(ssh_installed_packages, [system_hostname])
            available_updates, package_manager = process_ssh_res_available_updates(ssh_available_updates, [system_hostname])

            # Checking the update result
            if len(available_updates[system_hostname]) == 0:
                save_package_update_result(system_id, installed_packages[system_hostname], available_updates[system_hostname])
            else:
                raise SystemError('Puppet/Mcollective update process error.')
        else:
            raise ConnectionError("Server public key doesn't match. Please verify your server authenticity again.")
    else:
        raise ConnectionError('Cannot connect to your Puppet master server. Your server may be unavailable or your SSH passphrase may be invalid.')
    return

@shared_task
def celery_scan_cve(request_user_id, input_system_id):
    package_list = get_cve_package_list(request_user_id, input_system_id)

    cve_info = {}
    for system_id in package_list.keys():
        packages = package_list[system_id]
        cve_info_per_system = []
        for package in packages:
            package_id = package[0]
            package_name = package[1]
            # Calling Redhat CVE API (JSON format)
            response = requests.get('https://access.redhat.com/labs/securitydataapi/cve.json?package={0}'.format(package_name))
            # If CVE found
            if (len(response.json()) > 0):
                for cve in response.json():
                    cve_info_record = {}
                    cve_info_record['affected_package'] = package_name
                    cve_info_record['cve_id']           = cve['CVE']
                    cve_info_record['description']      = cve['bugzilla_description'].split(': ',1)[1].strip()
                    cve_info_record['severity']         = cve['severity']
                    if 'cvss3_score' in cve:
                        cve_info_record['cvss3_score'] = cve['cvss3_score']
                    else:
                        cve_info_record['cvss3_score'] = None
                    cve_info_per_system.append(cve_info_record)
        cve_info[system_id] = cve_info_per_system
    
    save_cve_information(cve_info)

    return
