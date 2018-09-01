Prerequisite
- Please install RabbitMQ first (https://www.rabbitmq.com/download.html)

Only for the first time, please run these commands to create databases:
1) manage.py makemigrations patch_management
2) manage.py migrate

Then to start the project, run the following commands on diferrent terminals separately:
1) manage.py runserver
2) celery -A patch_management worker -l info -P eventlet -c 1
