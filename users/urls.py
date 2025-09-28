# users/urls.py
from django.urls import path
from .views import (
   login_view, logout_view, register_view,
    pets_list_view, pet_detail_view, about_view, contact_view, dashboard_view, create_pet_report_view, # Make sure this is imported
    pet_report_detail_view, admin_dashboard_view,
    admin_manage_users_view,
    admin_promote_user_view,
    admin_remove_user_view,
    admin_adoption_processing_view,
    admin_put_for_adoption_view
)

app_name = 'users' 

urlpatterns = [
    # --- HTML Rendering URLs ---
    path('', login_view, name='login'), 
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('pets/', pets_list_view, name='pets_list'),
    path('pets/<int:pet_id>/', pet_detail_view, name='pet_detail'),
    path('about/', about_view, name='about'),
    path('contact/', contact_view, name='contact'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('report/pet/<str:report_type>/', create_pet_report_view, name='create_pet_report'),
    path('report/<int:report_id>/', pet_report_detail_view, name='pet_report_detail'), 
    path('admin_dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('admin_dashboard/users/', admin_manage_users_view, name='admin_manage_users'),
    path('admin_dashboard/users/promote/<int:user_id>/', admin_promote_user_view, name='admin_promote_user'),
    path('admin_dashboard/users/remove/<int:user_id>/', admin_remove_user_view, name='admin_remove_user'),
    path('admin_dashboard/process-adoption/', admin_adoption_processing_view, name='admin_adoption_processing'),
    path('admin_dashboard/process-adoption/<int:report_id>/', admin_put_for_adoption_view, name='admin_put_for_adoption'),
]

