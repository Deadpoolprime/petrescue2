# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from django.urls import reverse # Import reverse for url naming
from django.contrib import messages

from .models import Profile, PetReport, PetForAdoption, Notification
from .serializers import ProfileSerializer, PetReportSerializer, PetForAdoptionSerializer, NotificationSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

# --- API ViewSets ---
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    # permission_classes = [IsAuthenticated]

class PetReportViewSet(viewsets.ModelViewSet):
    queryset = PetReport.objects.all()
    serializer_class = PetReportSerializer
    # permission_classes = [IsAuthenticated]

class PetForAdoptionViewSet(viewsets.ModelViewSet):
    queryset = PetForAdoption.objects.all()
    serializer_class = PetForAdoptionSerializer
    # permission_classes = [IsAuthenticated]

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    # permission_classes = [IsAuthenticated]

# --- API View for Registration ---
class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not username or not password or not email:
            return Response({'error': 'Username, email, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# --- HTML Rendering Views ---

# Removed home_view as it's no longer the root of the project.
# The login_view will now be rendered by the root URL.

# Login View
def login_view(request):
    if request.method == 'POST':
        form_username = request.POST.get('username')
        form_password = request.POST.get('password')

        user = authenticate(request, username=form_username, password=form_password)

        if user is not None:
            auth_login(request, user)
            # Redirect to the dashboard page after successful login
            return redirect('users:dashboard') # <-- Now redirects to dashboard
        else:
            # Authentication failed
            messages.error(request, "Invalid username or password. Please try again.") # Using messages framework
            # Re-render login page with error message
            return render(request, 'users/login.html') # Removed explicit error_message from context
    else:
        # GET request: show the login form
        if request.user.is_authenticated:
            return redirect('users:dashboard') # Redirect logged-in users away from login
        return render(request, 'users/login.html')


# Logout View
def logout_view(request):
    auth_logout(request)
    return redirect('users:login') # Redirect to login after logout

# Registration Form
class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'id': 'id_username', 'class': 'form-input'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'id': 'id_email', 'class': 'form-input'}))
    first_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'id': 'id_first_name', 'class': 'form-input'}))
    age = forms.IntegerField(min_value=0, required=False, widget=forms.NumberInput(attrs={'id': 'id_age', 'class': 'form-input'}))
    city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'id': 'id_city', 'class': 'form-input'}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'id': 'id_phone_number', 'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'id_password1', 'class': 'form-input'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'id_password2', 'class': 'form-input'}), label="Confirm Password")

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            if len(password) < 8: raise forms.ValidationError("Password must contain at least 8 characters.")
            if not any(c.islower() for c in password): raise forms.ValidationError("Password must contain at least one lowercase letter.")
            if not any(c.isupper() for c in password): raise forms.ValidationError("Password must contain at least one uppercase letter.")
            if not any(c.isdigit() for c in password): raise forms.ValidationError("Password must contain at least one number.")
            if not any(not c.isalnum() for c in password): raise forms.ValidationError("Password must contain at least one special character.")
        return password

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

# Registration View
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data.get('first_name', ''),
            )
            Profile.objects.create(
                user=user,
                age=form.cleaned_data.get('age'),
                city=form.cleaned_data.get('city'),
                phone_number=form.cleaned_data.get('phone_number')
            )
            auth_login(request, user)
            messages.success(request, "🎉 Registration successful!")
            # Redirect to the pets list page after successful registration and login
            return redirect('users:login') # <-- MODIFIED: Redirect to pets list
    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})

# Placeholder View for Pets List
def pets_list_view(request):
    all_pets = PetForAdoption.objects.filter(status='Available')
    context = {
        'pets': all_pets
    }
    return render(request, 'users/pets_list.html', context)

# Placeholder View for Pet Detail
def pet_detail_view(request, pet_id):
    pet = get_object_or_404(PetForAdoption, pk=pet_id)
    context = {
        'pet': pet
    }
    return render(request, 'users/pet_detail.html', context)

# Placeholder View for About Page
def about_view(request):
    return render(request, 'users/about.html')

# Placeholder View for Contact Page
def contact_view(request):
    return render(request, 'users/contact.html')

# Example of a protected view (requires login)
@login_required
def dashboard_view(request):
    # This view will now serve as the landing page after login.
    # It will render the dashboard.html template.
    # We'll add the three buttons to dashboard.html.
    # The fetching of user profile and reports is already here and useful.
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        user_profile = None

    user_reports = request.user.pet_reports.all()

    context = {
        'profile': user_profile,
        'reports': user_reports
    }
    return render(request, 'users/dashboard.html', context)

# Placeholder View for Pets List (This will be our "Found pets for adoption" page)
# We'll add @login_required here later if needed, but for now, let's make it accessible.
def pets_list_view(request):
    # Fetch pets from your database that are available for adoption
    all_pets = PetForAdoption.objects.filter(status='Available')
    context = {
        'pets': all_pets
    }
    return render(request, 'users/pets_list.html', context)

# Placeholder View for Pet Detail
# Add @login_required if pet details should only be seen by logged-in users
# @login_required
def pet_detail_view(request, pet_id):
    pet = get_object_or_404(PetForAdoption, pk=pet_id)
    context = {
        'pet': pet
    }
    return render(request, 'users/pet_detail.html', context)

# Placeholder View for About Page (Not protected)
def about_view(request):
    return render(request, 'users/about.html')

# Placeholder View for Contact Page (Not protected)
def contact_view(request):
    return render(request, 'users/contact.html')

# --- Views for Reporting Lost/Found Pets (To be implemented next) ---
# For now, these are just placeholder URL names for the dashboard links.
# We'll create the actual views and templates for these later.
# def create_pet_report(request, report_type):
#     pass # Placeholder
#
# def pet_report_detail(request, report_id):
#     pass # Placeholder