# Linux Patch Management

A proof-of-concept Linux patch management application that is designed to manage systems via Puppet/Mcollective.

### Features
- Gathering managed system information
- Update single/all patches on amanaged system
- CVE scanning via RedHat Security Data API (only support RPM)
- Background task submissions with statues

### Prerequisites
On the patch management consolse (running this application):
- Please install RabbitMQ (https://www.rabbitmq.com/download.html)
- Python 3; install Python packages with `pip install -r requirements.txt`

On managed systems:
- A Puppet enviroment with Mcollective (Recommend installing with Choria packages) must be set up first, as this application is designed to control managed system via Puppet
- You may test using this demo (https://github.com/choria-io/vagrant-demo)


### Builds
For the first time, run these commands to create databases:

```
$ manage.py makemigrations patch_management
$ manage.py migrate
```

### Usages
To start the application, run the following commands:

```
$ manage.py runserver
$ celery -A patch_management worker -l info -P eventlet -c 1
```

By default, the application can be accessed via `localhost:8000`.
Then follow the initial steps to connect to your Puppet master.

### Built with
- Django (https://www.djangoproject.com)
- Django-celery-results (https://pypi.org/project/django_celery_results)
- Celery (http://www.celeryproject.org)
- Eventlet (http://eventlet.net)
- RabbitMQ (https://www.rabbitmq.com)
- Fabric (https://www.fabfile.org)
- Bootstrap v4 (https://getbootstrap.com)
- Toastr (https://github.com/CodeSeven/toastr)
- RedHat Security Data API (https://access.redhat.com/labs/securitydataapi)

### TODOs
- Better UX when adding and validating the Puppet master server's public key
- Implement bulk actions
- Add abilities to run custom scripts/manage config files on managed systems
- Improve the CVE scanning method to support all Linux distros
- A feature to set up local update repositories and deploy in-house patches
- Fix local DB concurrency (known) issue
