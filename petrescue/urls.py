from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# --- Import ViewSets directly from users.views ---
from users.views import (
    ProfileViewSet, PetReportViewSet, PetForAdoptionViewSet, NotificationViewSet, RegisterView
)
# --- Import the users app's URLs module for HTML routes ---
from users import urls as users_html_urls # This contains only HTML routes and has app_name='users'

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
    # This includes the router's URLs under /api/.
    # We are not using include(router.urls, namespace='api') directly.
    # Instead, we are including the router.urls and applying the 'api' namespace to the *entire* block.
    # This makes API URLs like http://127.0.0.1:8000/api/profiles/
    # and they will be namespaced as 'api:profiles', 'api:petreports', etc.
    path('api/', include(api_router.urls), name='api_root'), # No namespace argument here for router.urls

    # API Registration endpoint (if it's not part of the router)
    # Make sure this is also under the /api/ prefix if it's an API endpoint.
    path('api/register/', RegisterView.as_view(), name='api_register'),

    # --- HTML Rendering URLs ---
    # Include the users app's URL patterns (HTML routes only) at the root ('').
    # These are namespaced as 'users' (because of app_name='users' in users.urls).
    # This makes HTML URLs like http://127.0.0.1:8000/login/
    # and they'll be namespaced as 'users:login'.
    path('', include(users_html_urls, namespace='users')), # This is correct for HTML routes
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)