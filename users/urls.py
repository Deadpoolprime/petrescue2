# users/urls.py
from django.urls import path
from .views import (
    # Removed home_view from here, it's no longer the main root
   login_view, logout_view, register_view,
    pets_list_view, pet_detail_view, about_view, contact_view, dashboard_view
)

app_name = 'users' # This is essential

urlpatterns = [
    # --- HTML Rendering URLs ---
    # LOGIN is now the root for the users app, which will be mapped to the project root.
    path('', login_view, name='login'), # <-- MODIFIED: login is now the root for this app.
    # Removed the old path('', home_view, name='home'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('pets/', pets_list_view, name='pets_list'),
    path('pets/<int:pet_id>/', pet_detail_view, name='pet_detail'),
    path('about/', about_view, name='about'),
    path('contact/', contact_view, name='contact'),
    path('dashboard/', dashboard_view, name='dashboard'), # <-- ADDED: URL for the dashboard
    # Placeholder URLs for reporting (will be implemented later)
    # path('report/lost/', create_pet_report_view, {'report_type': 'Lost'}, name='create_pet_report'),
    # path('report/found/', create_pet_report_view, {'report_type': 'Found'}, name='create_pet_report'),
    # path('report/<int:report_id>/', report_detail_view, name='pet_report_detail'),
]