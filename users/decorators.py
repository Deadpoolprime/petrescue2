# users/decorators.py
from django.contrib.auth.decorators import user_passes_test

def staff_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is a staff member.
    """
    decorated_view = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url='users:login', # Redirect to your login page if test fails
        redirect_field_name=None
    )
    return decorated_view(view_func)

def superuser_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is a superuser.
    """
    decorated_view = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url='users:login', # Redirect to login if test fails
        redirect_field_name=None
    )
    return decorated_view(view_func)