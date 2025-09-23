from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, ProfileViewSet, PetReportViewSet, PetForAdoptionViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet)
router.register(r'petreports', PetReportViewSet)
router.register(r'petsforadoption', PetForAdoptionViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
]