import os
import tempfile

from fabric import Connection

def test_ssh_connection(input_form, tmp_ssh_key):
    c = Connection(host=str(input_form.instance.ssh_server_address), 
                    user=str(input_form.instance.ssh_username), 
                    port=str(input_form.instance.ssh_server_port), 
                    connect_kwargs={
                        'key_filename': tmp_ssh_key, 
                        'passphrase': str(input_form.instance.ssh_passphase)
                        }
                    )
    try:
        result = c.run('uname -s')
        c.close()
        return True
    except Exception:
        return False
 

def create_tmp_file(input_file):
    tmp_name = next(tempfile._get_candidate_names()) + '.tmp'
    print(tmp_name)
    with open(tmp_name, 'wb+') as destination:
        for chunk in input_file.chunks():
            destination.write(chunk)
    return tmp_name

def delete_tmp_file(tmp_file):
    os.remove(tmp_file)