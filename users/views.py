# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from django.urls import reverse
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
    # permission_classes = [IsAuthenticated] # Uncomment if API access should be restricted

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
        Profile.objects.create(user=user) # Creates profile with default values
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# --- HTML Rendering Views ---

# Login View
def login_view(request):
    if request.method == 'POST':
        form_username = request.POST.get('username')
        form_password = request.POST.get('password')

        user = authenticate(request, username=form_username, password=form_password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, "Welcome back! You are logged in.")
            # Redirect to the dashboard after successful login
            return redirect('users:dashboard')
        else:
            # Authentication failed
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, 'users/login.html') # Re-render login page with error message
    else:
        # GET request: show the login form
        # If user is already authenticated, redirect them away from the login page.
        if request.user.is_authenticated:
            return redirect('users:dashboard') # Redirect logged-in users to dashboard
        return render(request, 'users/login.html')

# Logout View
def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('users:login') # Redirect to login after logout

# Registration Form
class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'id': 'id_username', 'class': 'form-input'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'id': 'id_email', 'class': 'form-input'}))
    first_name = forms.CharField(label="Full Name",max_length=100, required=False, widget=forms.TextInput(attrs={'id': 'id_first_name', 'class': 'form-input'}))
    age = forms.IntegerField(min_value=0, required=False, widget=forms.NumberInput(attrs={'id': 'id_age', 'class': 'form-input'}))
    city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'id': 'id_city', 'class': 'form-input'}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'id': 'id_phone_number', 'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'id_password1', 'class': 'form-input'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'id_password2', 'class': 'form-input'}), label="Confirm Password")
    is_admin_registration = forms.BooleanField(required=False, label="Register as Admin")
    admin_passcode = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Admin Passcode"
    )

    # We need a custom validation method to check the passcode
    def clean(self):
        cleaned_data = super().clean()
        is_admin = cleaned_data.get('is_admin_registration')
        passcode = cleaned_data.get('admin_passcode')

        if is_admin:
            # If the admin box is checked, the passcode is required
            if not passcode:
                raise forms.ValidationError(
                    "Admin passcode is required when registering as an admin."
                )

            # Check if the passcode is correct
            from django.conf import settings
            if passcode != settings.ADMIN_REGISTRATION_PASSCODE:
                raise forms.ValidationError("Invalid admin passcode.")

        return cleaned_data
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

# Registration View (Modified for correct form handling and redirection)
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            is_admin = cleaned_data.get('is_admin_registration')

            # Step 1: Create the User
            user = User.objects.create_user(
                username=cleaned_data['username'],
                email=cleaned_data['email'],
                password=cleaned_data['password'],
                first_name=cleaned_data.get('first_name', '')
            )

            if is_admin:
                user.is_staff = True
                user.save()

            # Step 2: Explicitly create the Profile with all the form data
            # This is the crucial part that creates the row in the `users_profile` table.
            Profile.objects.create(
                user=user,
                role='admin' if is_admin else 'user',
                age=cleaned_data.get('age'),
                city=cleaned_data.get('city'),
                phone_number=cleaned_data.get('phone_number')
            )

            # Step 3: Log in and redirect
            auth_login(request, user)
            messages.success(request, "🎉 Registration successful! Welcome to PawFinder.")
            return redirect('users:dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})

# Dashboard View (Modified to show available pets and action buttons)
@login_required
def dashboard_view(request):
    # Fetch available pets for adoption
    available_pets = PetForAdoption.objects.filter(status='Available')

    context = {
        'available_pets': available_pets
        # We can also fetch user profile and reports here if needed for dashboard
    }
    return render(request, 'users/dashboard.html', context)


# New View for Reporting Lost/Found Pet
# This view will handle both 'Lost' and 'Found' report types.
def create_pet_report_view(request, report_type):
    # Ensure user is logged in
    if not request.user.is_authenticated:
        messages.error(request, "You need to be logged in to report a pet.")
        return redirect('users:login')

    if request.method == 'POST':
        form = PetReportForm(request.POST, request.FILES) # Pass POST data and FILES
        if form.is_valid():

            # Get cleaned data, handling potential None for optional fields
            pet_name = form.cleaned_data.get('name')
            pet_age = form.cleaned_data.get('age')
            pet_gender = form.cleaned_data.get('gender') # This might be '' if not selected


            if not pet_gender: 
                pass # Let the model's default handle it if blank is submitted

            pet_report = PetReport.objects.create(
                report_type=report_type,
                reporter=request.user,
                name=pet_name, # This will be None if left blank, which is correct for optional
                age=pet_age,   # This will be None if left blank, which is correct for optional
                gender=pet_gender, # This is the key field to watch
                pet_type=form.cleaned_data['pet_type'],
                breed=form.cleaned_data.get('breed'),
                color=form.cleaned_data['color'],
                pet_image=form.cleaned_data['pet_image'],
                location=form.cleaned_data['location'],
                contact_info=form.cleaned_data['contact_info'],
                # status defaults to 'Open'
            )
            messages.success(request, f"Your '{report_type}' pet report has been submitted successfully!")
            return redirect('users:dashboard')
        # If form is not valid, 'form' still holds the invalid data and errors.
    else:
        # GET request: Initialize an empty form
        form = PetReportForm()

    context = {
        'form': form,
        'report_type': report_type, # Pass to template for dynamic title/heading
    }
    return render(request, 'users/create_pet_report.html', context) # New template

# View to show a single pet report's details
@login_required # Protect this view
def pet_report_detail_view(request, report_id):
    try:
        report = PetReport.objects.get(pk=report_id)
        # Optional: Check if the logged-in user is the reporter of this report
        # if report.reporter != request.user:
        #     messages.error(request, "You do not have permission to view this report.")
        #     return redirect('users:dashboard')
    except PetReport.DoesNotExist:
        messages.error(request, "Report not found.")
        return redirect('users:dashboard')

    context = {
        'report': report
    }
    return render(request, 'users/pet_report_detail.html', context)

# --- Form for Reporting Lost/Found Pet ---
class PetReportForm(forms.Form):
    pet_type = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'e.g., Dog, Cat, Bird'}))
    breed = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'e.g., Labrador, Siamese'}))
    color = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'e.g., Brown, Black and White'}))
    pet_image = forms.ImageField(required=True)
    location = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'placeholder': 'Area where the pet was lost or found'}))
    contact_info = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'placeholder': 'Your phone or email'}))
    name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': "Pet's name (if known)"}))
    age = forms.IntegerField(min_value=0, required=False, widget=forms.NumberInput(attrs={'placeholder': "Pet's age in years (if known)"}))
    gender = forms.ChoiceField(choices=PetReport.GENDER_CHOICES, required=False, widget=forms.Select(attrs={'placeholder': "Select Gender"}))

# --- Placeholder views for About, Contact, etc. ---
def about_view(request):
    return render(request, 'users/about.html')

def contact_view(request):
    return render(request, 'users/contact.html')

# Dashboard View (already modified to fetch available pets)
@login_required
def dashboard_view(request):
    # Fetch available pets for adoption
    available_pets = PetForAdoption.objects.filter(status='Available')

    context = {
        'available_pets': available_pets
        # We can also fetch user profile and reports here if needed for dashboard
    }
    return render(request, 'users/dashboard.html', context)

def pets_list_view(request):
    all_pets = PetForAdoption.objects.filter(status='Available')
    context = {
        'pets': all_pets
    }
    return render(request, 'users/pets_list.html', context)

@login_required # Protect this view
def pet_detail_view(request, report_id):
    # ... (implementation for pet_report_detail_view) ...
    pass # Placeholder for now