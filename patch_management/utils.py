import os
import tempfile

from .models import System
from fabric import Connection
from invoke import UnexpectedExit

def connect_ssh(ssh_addr, ssh_user, ssh_port, ssh_key, ssh_passphrase):
    conn = Connection(host=ssh_addr, 
                    user=ssh_user, 
                    port=ssh_port, 
                    connect_kwargs={
                        'key_filename': ssh_key, 
                        'passphrase': ssh_passphrase
                        }
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

def ssh_run_get_system_info(ssh_conn, request_user):
    connected_systems = []
    sys_os_name = {}
    sys_os_ver = {}
    sys_kernel = {}

    connected_agents = ssh_conn.run('mco ping', hide=True)
    for line in connected_agents.stdout.split('\n'):
        if len(line) == 0: break
        connected_systems.append(line.split(' ', 1)[0])

    sys_info = ssh_conn.run('mco shell run "(cat /etc/*-release && uname -msr) | sed \'/^\s*$/d\'"')
    sys_info_lines = iter(sys_info.stdout.split('\n'))

    for line in sys_info_lines: 
        if line[:-1] in connected_systems: # managed-centos-0.server:
            cur_connected_system = line[:-1]
            prev_line = None
            while True:
                curr_line = next(sys_info_lines)
                if len(curr_line) > 0:
                    if 'PRETTY_NAME=' in curr_line:
                        sys_os_name[cur_connected_system] = curr_line.split('=', 2)[1].replace('"', '')
                    elif 'VERSION=' in curr_line:
                        sys_os_ver[cur_connected_system] = curr_line.split('=', 2)[1].replace('"', '')
                else: 
                    sys_kernel[cur_connected_system] = prev_line
                    break
                prev_line = curr_line

    ssh_conn.run('mco shell run "rpm -qa --qf \'%{NAME} %{VERSION}-%{RELEASE}\n\' || dpkg-query -W -f=\'\${Package} \${Version}\n\'"')

    ssh_conn.close()

    managed_systems = System.objects.filter(owner=request_user)
    managed_systems.update(connected = False)

    for connected_system in connected_systems:
        System.objects.update_or_create(hostname = connected_system, owner=request_user,
        defaults = {'connected': True, 'system_os_name': sys_os_name[connected_system],
        'system_os_version': sys_os_ver[connected_system], 'system_kernel': sys_kernel[connected_system]})


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