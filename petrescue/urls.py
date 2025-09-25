from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# --- Import ViewSets directly from users.views ---
from users.views import (
    ProfileViewSet, PetReportViewSet, PetForAdoptionViewSet, NotificationViewSet, RegisterView
)
# --- Import the users app's URLs module for HTML routes ---
from users import urls as users_html_urls

# --- Import DefaultRouter ---
from rest_framework.routers import DefaultRouter

# --- Setup the router for API ViewSets ---
api_router = DefaultRouter()
api_router.register(r'profiles', ProfileViewSet)
api_router.register(r'petreports', PetReportViewSet)
api_router.register(r'petsforadoption', PetForAdoptionViewSet)
api_router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- API Endpoints ---
    path('api/', include(api_router.urls), name='api_root'), # Note: no namespace here on include
    path('api/register/', RegisterView.as_view(), name='api_register'),

    # --- HTML Rendering URLs ---
    # Point the root URL ('') to the login view's URL pattern
    # The 'users' namespace is correctly applied here.
    # Since login_view is named 'login' in users.urls, it will be 'users:login'
    # when referenced in templates, but because it's at the root include, it's just 'login'
    # if referenced by name directly. However, with namespace 'users', it's 'users:login'.
    # For the ROOT URL, we need to include the LOGIN path directly.
    path('', include('users.urls')), # Include users.urls. Django will find 'login/' within it.
    # IMPORTANT: The previous `namespace='users'` was causing issues with conflicting root routes.
    # By including users.urls at the root directly, Django will pick up the patterns within it.
    # The `app_name = 'users'` in users.urls will ensure namespacing.
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)