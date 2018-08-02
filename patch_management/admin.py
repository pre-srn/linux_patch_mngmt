from django.contrib import admin
from .models import System, SSHProfile, Package

admin.site.register(SSHProfile)
admin.site.register(System)
admin.site.register(Package)
