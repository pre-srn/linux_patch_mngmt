# Patch management linux

### Prerequisites
- Please install RabbitMQ first (https://www.rabbitmq.com/download.html)
- Python 3; install Python packages with `pip install -r requirements.txt`

### Usages
For the first time, run these commands to create databases:

```
$ manage.py makemigrations patch_management
$ manage.py migrate
```

To start the project, run the following commands on diferrent terminals separately:

```
$ manage.py runserver
$ celery -A patch_management worker -l info -P eventlet -c 1
```

By default, the application can be accessed via `localhost:8000`
