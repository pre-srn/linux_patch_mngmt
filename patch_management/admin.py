from django.contrib import admin
from .models import System, SSHProfile

admin.site.register(SSHProfile)
admin.site.register(System)
