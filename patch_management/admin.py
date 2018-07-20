from django.contrib import admin
from .models import Server, MyModel, SSHProfile

admin.site.register(SSHProfile)
admin.site.register(Server)
admin.site.register(MyModel)
