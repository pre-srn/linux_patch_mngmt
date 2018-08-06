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

    # path('system/scan/cve/', main_views.get_system_info, name='get_system_info'),
    path('system/<int:system_id>/', main_views.manage_system, name='manage_system'),
    
    path('cve/scan/', main_views.scan_cve, name='scan_cve'),
    
    path('task/', main_views.list_task, name='list_task'),
    path('task/clear/', main_views.clear_task, name='clear_task'),

    # Ajax request URLs
    path('ajax/system/info/', main_views.ajax_get_system_info, name='get_system_info'),
    path('ajax/package/update/', main_views.ajax_update_package, name='update_package'),
    path('ajax/all/packages/update/', main_views.ajax_update_all_packages, name='update_all_packages'),
    
    path('ajax/system/info/table/', main_views.ajax_get_system_info_table, name='get_system_info_table'),
    path('ajax/installed/packages/table/', main_views.ajax_get_installed_packages_table, name='get_installed_packages_table'),
    path('ajax/outdated/packages/table/', main_views.ajax_get_outdated_packages_table, name='get_outdated_packages_table'),
    path('ajax/task/status/', main_views.ajax_check_task_status, name='check_task_status'),

    path('admin/', admin.site.urls), # TODO remove this
]
