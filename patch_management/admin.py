from django.contrib import admin
from .models import System, SSHProfile, Package, CVE

admin.site.register(SSHProfile)
admin.site.register(System)
admin.site.register(Package)
admin.site.register(CVE)
