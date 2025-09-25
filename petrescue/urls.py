from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# --- Import ViewSets directly from users.views ---
from users.views import (
    ProfileViewSet, PetReportViewSet, PetForAdoptionViewSet, NotificationViewSet, RegisterView
)
# --- Import the users app's URLs module for HTML routes ---
from users import urls as users_html_urls # This file has app_name = 'users'

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
    # Include the router's URLs under /api/.
    # We are applying the 'api' namespace to this block of URLs.
    # So, API URLs like 'profiles/' will become '/api/profiles/' and be namespaced as 'api:profiles'.
    # Note: We are NOT trying to namespace 'api_router.urls' with app_name here,
    # but rather applying a project-level namespace for API routes.
    path('api/', include(api_router.urls), name='api_root'), # No namespace argument on include for router.urls

    # API Registration endpoint
    path('api/register/', RegisterView.as_view(), name='api_register'),

    # --- HTML Rendering URLs ---
    # Include the users app's URL patterns (HTML routes only) at the root ('').
    # Django will automatically pick up app_name='users' from users_html_urls
    # and use it as the namespace for these routes.
    # This makes HTML URLs like http://127.0.0.1:8000/login/ accessible as 'users:login'.
    path('', include(users_html_urls)), # No namespace argument here; app_name from users.urls is used.
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)