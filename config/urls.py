"""linux_patch_management_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from patch_management import views as main_views

urlpatterns = [
    path('', main_views.home, name='home'),
    path('account/login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('account/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('account/register/', main_views.register, name='register'),
    path('account/setup/ssh/', main_views.setup_ssh, name='setup_ssh'),
    path('account/config/ssh/', main_views.setup_ssh, name='config_ssh'),
    path('account/config/password/', auth_views.PasswordChangeView.as_view(template_name='account/config_password.html'), name='password_change'),
    path('account/config/password/done/', main_views.config_password_done, name='password_change_done'),

    path('system/get/info/', main_views.get_system_info, name='get_system_info'),
    # path('system/scan/cve/', main_views.get_system_info, name='get_system_info'),
    path('system/<int:system_id>/', main_views.manage_system, name='manage_system'),
    # path('system/<int:system_id>/package/<int:package_id>/update', ),
    # path('system/<int:system_id>/package/<int:package_id>/uninstall', ),
    
    path('admin/', admin.site.urls), # TODO remove this
]
