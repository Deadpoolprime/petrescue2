# users/urls.py
from django.urls import path
from .views import (
    home_view, login_view, logout_view, register_view,
    pets_list_view, pet_detail_view, about_view, contact_view
)

app_name = 'users' # This is essential

urlpatterns = [
    # --- HTML Rendering URLs ---
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('pets/', pets_list_view, name='pets_list'),
    path('pets/<int:pet_id>/', pet_detail_view, name='pet_detail'),
    path('about/', about_view, name='about'),
    path('contact/', contact_view, name='contact'),
]