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


def home_view(request):
  featured_pets = PetForAdoption.objects.filter(status='Available').order_by('?')[:3]

  context = {
    'featured_pets': featured_pets,
  }
  return render(request, 'users/home.html', context)


def login_view(request):
  if request.method == 'POST':
    form_username = request.POST.get('username')
    form_password = request.POST.get('password')

    user = authenticate(request, username=form_username, password=form_password)

    if user is not None:
      auth_login(request, user)
      messages.success(request, "Welcome back! You are logged in.")
      return redirect('users:dashboard')
    else:
      messages.error(request, "Invalid username or password. Please try again.")
      return render(request, 'users/login.html') 
  else:
    if request.user.is_authenticated:
      return redirect('users:dashboard')
    return render(request, 'users/login.html')

def logout_view(request):
  auth_logout(request)
  messages.info(request, "You have been logged out.")
  return redirect('users:home') 
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

  def clean(self):
    cleaned_data = super().clean()
    is_admin = cleaned_data.get('is_admin_registration')
    passcode = cleaned_data.get('admin_passcode')

    if is_admin:
      if not passcode:
        raise forms.ValidationError(
          "Admin passcode is required when registering as an admin."
        )
      from django.conf import settings
      if passcode != settings.ADMIN_REGISTRATION_PASSCODE:
        raise forms.ValidationError("Invalid admin passcode.")

      current_admin_count = User.objects.filter(is_staff=True, is_superuser=False).count()

      if current_admin_count >= 3:
        raise forms.ValidationError(
          "Cannot register as an admin at this time. The maximum number of admins (3) has been reached."
        )


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

def register_view(request):
  if request.method == 'POST':
    form = RegistrationForm(request.POST)
    if form.is_valid():
      cleaned_data = form.cleaned_data
      is_admin = cleaned_data.get('is_admin_registration')


      user = User.objects.create_user(
        username=cleaned_data['username'],
        email=cleaned_data['email'],
        password=cleaned_data['password'],
        first_name=cleaned_data.get('first_name', '')
      )

      if is_admin:
        user.is_staff = True
        user.save()


      Profile.objects.create(
        user=user,
        role='admin' if is_admin else 'user',
        age=cleaned_data.get('age'),
        city=cleaned_data.get('city'),
        phone_number=cleaned_data.get('phone_number')
      )


      auth_login(request, user)
      messages.success(request, "🎉 Registration successful! Welcome to PurPaws.")
      return redirect('users:dashboard')
    else:
      form = RegistrationForm(request.POST) 

  else:
    form = RegistrationForm()

  return render(request, 'users/register.html', {'form': form})


@login_required
def dashboard_view(request):

  profile = None
  if hasattr(request.user, 'profile'):
    profile = request.user.profile

  
  
  view_filter = request.GET.get('view')

  open_reports_qs = PetReport.objects.filter(status='Open').order_by('-date_reported')
  
  if view_filter == 'lost':
    open_reports_qs = open_reports_qs.filter(report_type='Lost')
  elif view_filter == 'found':
    open_reports_qs = open_reports_qs.filter(report_type='Found')
  
  open_reports = list(open_reports_qs) 

  context = {
    'profile': profile,
    'open_reports': open_reports,
    'current_view': view_filter or 'all', 
  }
  
  return render(request, 'users/dashboard.html', context)


def create_pet_report_view(request, report_type):

 if not request.user.is_authenticated:
    messages.error(request, "You need to be logged in to report a pet.")
    return redirect('users:login')

 if report_type not in ['Lost', 'Found']:
    messages.error(request, "Invalid report type.")
    return redirect('users:dashboard')

 if request.method == 'POST':
    form = PetReportForm(request.POST, request.FILES) 
    if form.is_valid():


        injury_detail = form.cleaned_data.get('injury') if report_type == 'Found' else None

        pet_report = PetReport.objects.create(
        report_type=report_type,
        reporter=request.user,
        name=form.cleaned_data.get('name'), 
        age=form.cleaned_data.get('age'), 
        gender=form.cleaned_data.get('gender'), 
        pet_type=form.cleaned_data['pet_type'],
        breed=form.cleaned_data.get('breed'),
        color=form.cleaned_data['color'],
        pet_image=form.cleaned_data['pet_image'],
        location=form.cleaned_data['location'],
        contact_info=form.cleaned_data['contact_info'],

        health_information=form.cleaned_data.get('health_information'),
        injury=injury_detail,

  )
    messages.success(request, f"Your  pet report has been submitted successfully!")
    return redirect('users:dashboard')

 else:

    form = PetReportForm()

 context = {
 'form': form,
 'report_type': report_type, 
 'is_found_report': report_type == 'Found' 
 }
 return render(request, 'users/create_pet_report.html', context) 

@login_required 
def pet_report_detail_view(request, report_id):
  try:
    report = PetReport.objects.get(pk=report_id)
  except PetReport.DoesNotExist:
    messages.error(request, "Report not found.")
    return redirect('users:dashboard')

  context = {
    'report': report
  }
  return render(request, 'users/pet_report_detail.html', context)


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

 health_information = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': "Known medical issues, required medications, temperament, etc."}), label="Health Information")
 injury = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': "Visible injuries, limp, signs of distress (Found reports only)."}), label="Observed Injury")


def about_view(request):
  return render(request, 'users/about.html')

def contact_view(request):
  return render(request, 'users/contact.html')


def pets_list_view(request):
  all_pets = PetForAdoption.objects.filter(status='Available')
  context = {
    'pets': all_pets
  }
  return render(request, 'users/pets_list.html', context)


@login_required 
def pet_detail_view(request, pet_id):
  """
  Displays detailed information for a pet listed for adoption (PetForAdoption model).
  """
  pet = get_object_or_404(PetForAdoption, pk=pet_id, status='Available')

  context = {
    'pet': pet
  }
  return render(request, 'users/pet_detail.html', context)


@staff_required
def admin_adoption_processing_view(request):
  """
  Lists pets that are pending adoption and need admin action.
  """

  pets_to_process = PetReport.objects.filter(status='Pending Adoption')

  context = {
    'pets_to_process': pets_to_process,
  }
  return render(request, 'admin/process_adoption.html', context)


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

      new_adoption_pet = form.save(commit=False) 
      new_adoption_pet.pet_type = report.pet_type
      new_adoption_pet.breed = report.breed
      new_adoption_pet.color = report.color
      new_adoption_pet.image = report.pet_image 
      new_adoption_pet.lister = request.user 
      new_adoption_pet.status = 'Available'
      new_adoption_pet.save()


      report.status = 'Closed'
      report.save()

      messages.success(request, f"Pet '{new_adoption_pet.name}' has been successfully listed for adoption!")
      return redirect('users:admin_adoption_processing')
  else:

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

@staff_required 
def admin_dashboard_view(request):
 """
 Displays statistics for the admin dashboard.
 (UPDATED to separate user counts)
 """

 total_admins = User.objects.filter(is_staff=True, is_superuser=False).count()



 total_normal_users = User.objects.filter(is_staff=False).count()

 pets_for_adoption_count = PetForAdoption.objects.filter(status='Available').count()
 lost_reports_count = PetReport.objects.filter(report_type='Lost', status='Open').count()
 found_reports_count = PetReport.objects.filter(report_type='Found', status='Open').count()

 context = {
  'total_normal_users': total_normal_users,
  'total_admins': total_admins,
  'pets_for_adoption_count': pets_for_adoption_count,
  'lost_reports_count': lost_reports_count,
  'found_reports_count': found_reports_count,
 }
 return render(request, 'admin/dashboard.html', context)



@staff_required 
def admin_manage_users_view(request):
  """
  Lists all non-superuser users for management.
  """

  users_to_manage = User.objects.filter(is_superuser=False).select_related('profile')

  context = {
    'users': users_to_manage,
  }
  return render(request, 'admin/manage_users.html', context)


@superuser_required 
def admin_promote_user_view(request, user_id):
  if request.method == 'POST':


    current_admin_count = User.objects.filter(is_staff=True, is_superuser=False).count()


    if current_admin_count >= 3:
      messages.error(request, "Cannot promote user. The maximum number of 3 admins has been reached.")
      return redirect('users:admin_manage_users')


    try:
      user_to_promote = User.objects.get(pk=user_id)

      if user_to_promote.is_superuser or user_to_promote.is_staff:
        messages.warning(request, "This user is already a superuser or admin.")
      else:

        user_to_promote.is_staff = True
        user_to_promote.save()

        user_to_promote.profile.role = 'admin'
        user_to_promote.profile.save()

        messages.success(request, f"User '{user_to_promote.username}' has been promoted to Admin.")

    except User.DoesNotExist:
      messages.error(request, "User not found.")

  return redirect('users:admin_manage_users')


@staff_required 
def admin_remove_user_view(request, user_id):
  if request.method == 'POST':
    try:
      user_to_remove = User.objects.get(pk=user_id)


      if user_to_remove.is_staff and not request.user.is_superuser:
        messages.error(request, "You do not have permission to remove an admin user.")
        return redirect('users:admin_manage_users')


      if user_to_remove.is_superuser:
        messages.error(request, "Superusers cannot be removed from this interface.")
        return redirect('users:admin_manage_users')

      username = user_to_remove.username
      user_to_remove.delete()
      messages.success(request, f"User '' has been removed successfully.")

    except User.DoesNotExist:
      messages.error(request, "User not found.")

  return redirect('users:admin_manage_users')


@staff_required
def admin_adoption_processing_view(request):
  """
  Lists pets that are pending adoption, and also lists open reports for management and manual processing.
  """
  
  # 1. Reports that are ready or pending adoption (Automated/Ready to finalize)
  pending_adoption_reports = PetReport.objects.filter(status='Pending Adoption').order_by('-date_reported')

  # 2. Open Found Reports (Manual override option)
  open_found_reports = PetReport.objects.filter(report_type='Found', status='Open').order_by('-date_reported')

  # 3. Open Lost Reports (For monitoring)
  open_lost_reports = PetReport.objects.filter(report_type='Lost', status='Open').order_by('-date_reported')


  context = {
    'pending_adoption_reports': pending_adoption_reports,
    'open_found_reports': open_found_reports,
    'open_lost_reports': open_lost_reports,
  }
  # Renders the new comprehensive template
  return render(request, 'admin/process_adoption.html', context)



@staff_required
def admin_put_for_adoption_view(request, report_id):
  """
  Handles the form for an admin to name a pet and put it up for adoption.
  Updated to allow processing of 'Open' reports (Found type only) for manual override.
  """
  try:
    # Allow processing if status is 'Pending Adoption' OR 'Open' AND it's a Found report
    report = PetReport.objects.get(pk=report_id, report_type='Found', status__in=['Pending Adoption', 'Open'])
  except PetReport.DoesNotExist:
    messages.error(request, "This report was not found or is not a Found report eligible for adoption processing.")
    return redirect('users:admin_adoption_processing')

  if request.method == 'POST':
    form = PutForAdoptionForm(request.POST)
    if form.is_valid():

      new_adoption_pet = form.save(commit=False)
      new_adoption_pet.pet_type = report.pet_type
      new_adoption_pet.breed = report.breed
      new_adoption_pet.color = report.color
      new_adoption_pet.image = report.pet_image 
      new_adoption_pet.lister = request.user 
      new_adoption_pet.status = 'Available'
      new_adoption_pet.save()


      report.status = 'Closed'
      report.save()

      messages.success(request, f"Pet '{new_adoption_pet.name}' has been successfully listed for adoption!")
      return redirect('users:admin_adoption_processing')
  else:

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