from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from users.views import (
    ProfileViewSet, PetReportViewSet, PetForAdoptionViewSet, NotificationViewSet, RegisterView
)
from users import urls as users_html_urls

from rest_framework.routers import DefaultRouter

api_router = DefaultRouter()
api_router.register(r'profiles', ProfileViewSet)
api_router.register(r'petreports', PetReportViewSet)
api_router.register(r'petsforadoption', PetForAdoptionViewSet)
api_router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_router.urls), name='api_root'), # Note: no namespace here on include
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)