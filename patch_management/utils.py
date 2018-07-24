import os
import tempfile

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
        conn.run('uname -s')
        conn.close()
        return True, conn
    except Exception:
        del conn
        return False, None

def is_puppet_running(conn):
    try:
        result = conn.run('puppet --version')
        conn.close()
        return True
    except UnexpectedExit:
        conn.close()
        return False

def create_tmp_file(input_file):
    tmp_name = next(tempfile._get_candidate_names()) + '.tmp'
    with open(tmp_name, 'wb+') as destination:
        for chunk in input_file.chunks():
            destination.write(chunk)
    return tmp_name

def delete_tmp_file(tmp_file):
    os.remove(tmp_file)