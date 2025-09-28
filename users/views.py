# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from django.urls import reverse
from django.contrib import messages
from .decorators import staff_required, superuser_required
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

            # --- NEW LOGIC: CHECK ADMIN LIMIT ---
            # An "Admin" is a staff member who is NOT a superuser.
            current_admin_count = User.objects.filter(is_staff=True, is_superuser=False).count()
            
            # We allow a maximum of 3 admins.
            if current_admin_count >= 3:
                raise forms.ValidationError(
                    "Cannot register as an admin at this time. The maximum number of admins (3) has been reached."
                )
            # ------------------------------------

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
            messages.success(request, "🎉 Registration successful! Welcome to PurPaws.")
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

@staff_required
def admin_adoption_processing_view(request):
    """
    Lists pets that are pending adoption and need admin action.
    """
    # Find all PetReports marked as 'Pending Adoption'
    pets_to_process = PetReport.objects.filter(status='Pending Adoption')

    context = {
        'pets_to_process': pets_to_process,
    }
    return render(request, 'admin/process_adoption.html', context)

# Form for putting a pet up for adoption
class PutForAdoptionForm(forms.ModelForm):
    # We can inherit from PetForAdoption and add fields
    class Meta:
        model = PetForAdoption
        fields = ['name', 'age', 'gender', 'description'] # Fields the admin will fill in
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

@staff_required
def admin_put_for_adoption_view(request, report_id):
    """
    Handles the form for an admin to name a pet and put it up for adoption.
    """
    try:
        report = PetReport.objects.get(pk=report_id, status='Pending Adoption')
    except PetReport.DoesNotExist:
        messages.error(request, "This pet report was not found or is not pending adoption.")
        return redirect('users:admin_adoption_processing')

    if request.method == 'POST':
        form = PutForAdoptionForm(request.POST)
        if form.is_valid():
            # Create the new PetForAdoption record
            new_adoption_pet = form.save(commit=False) # Don't save to DB yet
            new_adoption_pet.pet_type = report.pet_type
            new_adoption_pet.breed = report.breed
            new_adoption_pet.color = report.color
            new_adoption_pet.image = report.pet_image # Directly assign the image file
            new_adoption_pet.lister = request.user # The admin is the lister
            new_adoption_pet.status = 'Available'
            new_adoption_pet.save()

            # Close the original report
            report.status = 'Closed'
            report.save()

            messages.success(request, f"Pet '{new_adoption_pet.name}' has been successfully listed for adoption!")
            return redirect('users:admin_adoption_processing')
    else:
        # Pre-populate the form with data from the report
        initial_data = {
            'name': report.name or '',
            'age': report.age or '',
            'gender': report.gender
        }
        form = PutForAdoptionForm(initial=initial_data)

    context = {
        'form': form,
        'report': report,
    }
    return render(request, 'admin/put_for_adoption_form.html', context)

@staff_required # Only staff (Admins and Superusers) can access this
def admin_dashboard_view(request):
    """
    Displays statistics for the admin dashboard.
    """
    user_count = User.objects.count()
    pets_for_adoption_count = PetForAdoption.objects.filter(status='Available').count()
    lost_reports_count = PetReport.objects.filter(report_type='Lost', status='Open').count()
    found_reports_count = PetReport.objects.filter(report_type='Found', status='Open').count()

    context = {
        'user_count': user_count,
        'pets_for_adoption_count': pets_for_adoption_count,
        'lost_reports_count': lost_reports_count,
        'found_reports_count': found_reports_count,
    }
    return render(request, 'admin/dashboard.html', context)


@staff_required # Only staff can manage users
def admin_manage_users_view(request):
    """
    Lists all non-superuser users for management.
    """
    # Exclude superusers so they cannot be managed from this interface
    users_to_manage = User.objects.filter(is_superuser=False).select_related('profile')

    context = {
        'users': users_to_manage,
    }
    return render(request, 'admin/manage_users.html', context)


@superuser_required # ONLY a superuser can promote another user to admin
def admin_promote_user_view(request, user_id):
    if request.method == 'POST':
        # --- NEW LOGIC: Check the current number of admins ---
        # An "Admin" is a staff member who is NOT a superuser.
        current_admin_count = User.objects.filter(is_staff=True, is_superuser=False).count()
        
        # We allow a maximum of 2 admins.
        if current_admin_count >= 3:
            messages.error(request, "Cannot promote user. The maximum number of 3 admins has been reached.")
            return redirect('users:admin_manage_users')
        # ---------------------------------------------------

        try:
            user_to_promote = User.objects.get(pk=user_id)

            if user_to_promote.is_superuser or user_to_promote.is_staff:
                messages.warning(request, "This user is already a superuser or admin.")
            else:
                # Promote the user
                user_to_promote.is_staff = True
                user_to_promote.save()

                user_to_promote.profile.role = 'admin'
                user_to_promote.profile.save()

                messages.success(request, f"User '{user_to_promote.username}' has been promoted to Admin.")

        except User.DoesNotExist:
            messages.error(request, "User not found.")

    return redirect('users:admin_manage_users')


@staff_required # Any staff member can attempt to remove a user
def admin_remove_user_view(request, user_id):
    if request.method == 'POST':
        try:
            user_to_remove = User.objects.get(pk=user_id)

            # Security check: Prevent non-superusers from removing admins.
            if user_to_remove.is_staff and not request.user.is_superuser:
                messages.error(request, "You do not have permission to remove an admin user.")
                return redirect('users:admin_manage_users')

            # Prevent anyone from removing a superuser via this view
            if user_to_remove.is_superuser:
                messages.error(request, "Superusers cannot be removed from this interface.")
                return redirect('users:admin_manage_users')
            
            username = user_to_remove.username
            user_to_remove.delete()
            messages.success(request, f"User '{username}' has been removed successfully.")

        except User.DoesNotExist:
            messages.error(request, "User not found.")

    return redirect('users:admin_manage_users')


@staff_required
def admin_adoption_processing_view(request):
    """
    Lists pets that are pending adoption and need admin action.
    """
    pets_to_process = PetReport.objects.filter(status='Pending Adoption')
    context = {'pets_to_process': pets_to_process}
    return render(request, 'admin/process_adoption.html', context)


# Form for putting a pet up for adoption (can be defined here or with other forms)
class PutForAdoptionForm(forms.ModelForm):
    class Meta:
        model = PetForAdoption
        fields = ['name', 'age', 'gender', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'name': "Pet's New Name (for adoption listing)",
            'age': "Estimated Age",
            'description': "Adoption Profile Description",
        }


@staff_required
def admin_put_for_adoption_view(request, report_id):
    """
    Handles the form for an admin to name a pet and put it up for adoption.
    """
    try:
        report = PetReport.objects.get(pk=report_id, status='Pending Adoption')
    except PetReport.DoesNotExist:
        messages.error(request, "This pet report was not found or is not pending adoption.")
        return redirect('users:admin_adoption_processing')

    if request.method == 'POST':
        form = PutForAdoptionForm(request.POST)
        if form.is_valid():
            # Create the new PetForAdoption record
            new_adoption_pet = form.save(commit=False)
            new_adoption_pet.pet_type = report.pet_type
            new_adoption_pet.breed = report.breed
            new_adoption_pet.color = report.color
            new_adoption_pet.image = report.pet_image # Directly assign the image file
            new_adoption_pet.lister = request.user # The admin is the lister
            new_adoption_pet.status = 'Available'
            new_adoption_pet.save()

            # Close the original report
            report.status = 'Closed'
            report.save()

            messages.success(request, f"Pet '{new_adoption_pet.name}' has been successfully listed for adoption!")
            return redirect('users:admin_adoption_processing')
    else:
        # Pre-populate the form with data from the report for GET request
        initial_data = {
            'name': report.name if report.name else f"Friendly {report.pet_type}",
            'age': report.age or None,
            'gender': report.gender,
            'description': f"This lovely {report.pet_type} was found near {report.location}. We are looking for a forever home for them!"
        }
        form = PutForAdoptionForm(initial=initial_data)

    context = {
        'form': form,
        'report': report,
    }
    return render(request, 'admin/put_for_adoption_form.html', context)