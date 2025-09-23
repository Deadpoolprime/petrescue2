from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .models import Profile, PetReport, PetForAdoption, Notification
from .serializers import ProfileSerializer, PetReportSerializer, PetForAdoptionSerializer, NotificationSerializer, UserSerializer

# New view for user registration
class RegisterView(APIView):
    permission_classes = [AllowAny] # Anyone can access this view to register

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Basic validation
        if not username or not password or not email:
            return Response({'error': 'Username, email, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create User
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Create Profile with additional data
        profile = Profile.objects.get(user=user)
        profile.age = request.data.get('age')
        profile.city = request.data.get('city')
        profile.phone_number = request.data.get('phone_number')
        profile.save()

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# These are the viewsets for your other models
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

class PetReportViewSet(viewsets.ModelViewSet):
    queryset = PetReport.objects.all()
    serializer_class = PetReportSerializer

class PetForAdoptionViewSet(viewsets.ModelViewSet):
    queryset = PetForAdoption.objects.all()
    serializer_class = PetForAdoptionSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
