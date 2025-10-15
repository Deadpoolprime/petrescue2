from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
import datetime
from django.db.models import Q 

from .decorators import staff_required, superuser_required
from .models import Profile, PetReport, PetForAdoption, Notification
from .serializers import (
    ProfileSerializer,
    PetReportSerializer,
    PetForAdoptionSerializer,
    NotificationSerializer,
    UserSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny

# -----------------------
# REST viewsets / APIView
# -----------------------
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
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not password or not email:
            return Response(
                {"error": "Username, email, and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# -----------------------
# Forms
# -----------------------
class RegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150, required=True, widget=forms.TextInput(attrs={"id": "id_username", "class": "form-input"})
    )
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"id": "id_email", "class": "form-input"}))
    first_name = forms.CharField(
        label="Full Name",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"id": "id_first_name", "class": "form-input"}),
    )
    age = forms.IntegerField(min_value=0, required=False, widget=forms.NumberInput(attrs={"id": "id_age", "class": "form-input"}))
    city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"id": "id_city", "class": "form-input"}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"id": "id_phone_number", "class": "form-input"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"id": "id_password1", "class": "form-input"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"id": "id_password2", "class": "form-input"}), label="Confirm Password")
    is_admin_registration = forms.BooleanField(required=False, label="Register as Admin")
    admin_passcode = forms.CharField(widget=forms.PasswordInput, required=False, label="Admin Passcode")

    def clean(self):
        cleaned_data = super().clean()
        is_admin = cleaned_data.get("is_admin_registration")
        passcode = cleaned_data.get("admin_passcode")

        if is_admin:
            if not passcode:
                raise forms.ValidationError("Admin passcode is required when registering as an admin.")

            if passcode != getattr(settings, "ADMIN_REGISTRATION_PASSCODE", None):
                raise forms.ValidationError("Invalid admin passcode.")

            current_admin_count = User.objects.filter(is_staff=True, is_superuser=False).count()
            if current_admin_count >= 3:
                raise forms.ValidationError("Cannot register as an admin at this time. The maximum number of admins (3) has been reached.")

        return cleaned_data

    # Field-level validation for password strength (applies to field named 'password')
    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            if len(password) < 8:
                raise forms.ValidationError("Password must contain at least 8 characters.")
            if not any(c.islower() for c in password):
                raise forms.ValidationError("Password must contain at least one lowercase letter.")
            if not any(c.isupper() for c in password):
                raise forms.ValidationError("Password must contain at least one uppercase letter.")
            if not any(c.isdigit() for c in password):
                raise forms.ValidationError("Password must contain at least one number.")
            if not any(not c.isalnum() for c in password):
                raise forms.ValidationError("Password must contain at least one special character.")
        return password

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email


class PetReportForm(forms.Form):
    pet_type = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={"placeholder": "e.g., Dog, Cat, Bird"}))
    breed = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"placeholder": "e.g., Labrador, Siamese"}))
    color = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={"placeholder": "e.g., Brown, Black and White"}))
    pet_image = forms.ImageField(required=True)
    location = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={"placeholder": "Area where the pet was lost or found"}))
    contact_info = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={"placeholder": "Your phone or email"}))
    name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"placeholder": "Pet's name (if known)"}))
    age = forms.IntegerField(min_value=0, required=False, widget=forms.NumberInput(attrs={"placeholder": "Pet's age in years (if known)"}))
    gender = forms.ChoiceField(choices=PetReport.GENDER_CHOICES, required=False, widget=forms.Select(attrs={"placeholder": "Select Gender"}))
    event_date = forms.DateField(required=True, widget=forms.DateInput(attrs={"type": "date"}), label="Date Lost/Found")
    health_information = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Known medical issues, required medications, temperament, etc."}), label="Health Information")
    injury = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Visible injuries, limp, signs of distress (Found reports only)."}), label="Observed Injury")


class PutForAdoptionForm(forms.ModelForm):
    class Meta:
        model = PetForAdoption
        fields = ["name", "age", "gender", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
        labels = {
            "name": "Pet's New Name (for adoption listing)",
            "age": "Estimated Age",
            "description": "Adoption Profile Description",
        }


# -----------------------
# Public views
# -----------------------
def home_view(request):
    context = {}
    return render(request, "users/home.html", context)


def login_view(request):
    if request.method == "POST":
        form_username = request.POST.get("username")
        form_password = request.POST.get("password")

        user = authenticate(request, username=form_username, password=form_password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, "Welcome back! You are logged in.")
            return redirect("users:dashboard")
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, "users/login.html")
    else:
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        return render(request, "users/login.html")


def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("users:home")


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            is_admin = cleaned_data.get("is_admin_registration")

            user = User.objects.create_user(
                username=cleaned_data["username"],
                email=cleaned_data["email"],
                password=cleaned_data["password"],
                first_name=cleaned_data.get("first_name", ""),
            )

            if is_admin:
                user.is_staff = True
                user.save()

            Profile.objects.create(
                user=user,
                role="admin" if is_admin else "user",
                age=cleaned_data.get("age"),
                city=cleaned_data.get("city"),
                phone_number=cleaned_data.get("phone_number"),
            )

            auth_login(request, user)
            messages.success(request, "🎉 Registration successful! Welcome to PurPaws.")
            return redirect("users:dashboard")
    else:
        form = RegistrationForm()

    return render(request, "users/register.html", {"form": form})


def about_view(request):
    return render(request, "users/about.html")


def contact_view(request):
    return render(request, "users/contact.html")


def pets_list_view(request):
    all_pets = PetForAdoption.objects.filter(status="Available")
    context = {"pets": all_pets}
    return render(request, "users/pets_list.html", context)


def pet_detail_view(request, pet_id):
    """
    Displays detailed information for a pet listed for adoption (PetForAdoption model).
    This view is public and does not require login.
    """
    pet = get_object_or_404(PetForAdoption, pk=pet_id, status="Available")
    context = {"pet": pet}
    return render(request, "users/pet_detail.html", context)


# -----------------------
# User dashboard / reports
# -----------------------
@login_required
def dashboard_view(request):
    profile = getattr(request.user, "profile", None)

    view_filter = request.GET.get("view")
    open_reports_qs = PetReport.objects.filter(status="Open", is_approved=True).order_by("-date_reported")

    if view_filter == "lost":
        open_reports_qs = open_reports_qs.filter(report_type="Lost")
    elif view_filter == "found":
        open_reports_qs = open_reports_qs.filter(report_type="Found")

    open_reports = list(open_reports_qs)

    context = {
        "profile": profile,
        "open_reports": open_reports,
        "current_view": view_filter or "all",
    }
    return render(request, "users/dashboard.html", context)


def create_pet_report_view(request, report_type):
    if not request.user.is_authenticated:
        messages.error(request, "You need to be logged in to report a pet.")
        return redirect("users:login")

    if report_type not in ["Lost", "Found"]:
        messages.error(request, "Invalid report type.")
        return redirect("users:dashboard")

    if request.method == "POST":
        form = PetReportForm(request.POST, request.FILES)
        if form.is_valid():
            injury_detail = form.cleaned_data.get("injury") if report_type == "Found" else None
            is_approved_status = False
            pet_report = PetReport.objects.create(
                report_type=report_type,
                reporter=request.user,
                name=form.cleaned_data.get("name"),
                age=form.cleaned_data.get("age"),
                gender=form.cleaned_data.get("gender"),
                pet_type=form.cleaned_data["pet_type"],
                breed=form.cleaned_data.get("breed"),
                color=form.cleaned_data["color"],
                pet_image=form.cleaned_data["pet_image"],
                location=form.cleaned_data["location"],
                contact_info=form.cleaned_data["contact_info"],
                event_date=form.cleaned_data.get("event_date"),
                health_information=form.cleaned_data.get("health_information"),
                injury=injury_detail,
                is_approved=is_approved_status,
            )
            messages.success(request, "Your pet report has been submitted successfully!")
            return redirect("users:dashboard")
    else:
        form = PetReportForm()

    context = {"form": form, "report_type": report_type, "is_found_report": report_type == "Found"}
    return render(request, "users/create_pet_report.html", context)


@login_required
def pet_report_detail_view(request, report_id):
    report = get_object_or_404(PetReport, pk=report_id)
    context = {"report": report}
    return render(request, "users/pet_report_detail.html", context)


# -----------------------
# Admin / staff views
# -----------------------
@staff_required
def admin_adoption_processing_view(request):
    """
    Dynamically lists pets ready for adoption.
    A pet is ready if its status is 'Pending Adoption' OR if it's a 'Found'
    report that is older than 15 days.
    """
    # 1. Define the 15-day threshold
    threshold_date = timezone.now() - datetime.timedelta(days=15)

    # 2. Define the conditions for a pet to be "Ready for Listing"
    # Condition A: The status is already 'Pending Adoption'
    pending_status_q = Q(status='Pending Adoption')
    # Condition B: The report is 'Found', 'Open', approved, AND older than 15 days
    overdue_q = Q(
        report_type='Found',
        status='Open',
        is_approved=True,
        date_reported__lt=threshold_date
    )

    # Combine the conditions with an OR operator
    pets_ready_for_listing = PetReport.objects.filter(pending_status_q | overdue_q).distinct().order_by('-date_reported')

    # 3. Get 'Open Found' reports that are NOT overdue for the monitoring section
    open_found_reports = PetReport.objects.filter(
        report_type='Found',
        status='Open',
        is_approved=True,
        date_reported__gte=threshold_date  # GTE = Greater than or equal to (i.e., not overdue)
    ).order_by('-date_reported')

    # 4. Get 'Open Lost' reports for monitoring
    open_lost_reports = PetReport.objects.filter(
        report_type='Lost',
        status='Open',
        is_approved=True
    ).order_by('-date_reported')

    context = {
        'pets_ready_for_listing': pets_ready_for_listing, # Renamed for clarity
        'open_found_reports': open_found_reports,
        'open_lost_reports': open_lost_reports,
    }
    return render(request, 'admin/process_adoption.html', context)


@staff_required
def admin_put_for_adoption_view(request, report_id):
    """
    Handles the form for an admin to list a pet for adoption.
    Updated to allow processing of 'Open' reports that have passed the 15-day mark.
    """
    # This query now accepts reports that are either 'Pending Adoption' or 'Open',
    # as long as they are a 'Found' report. The logic in the previous view ensures
    # only the correct 'Open' reports can reach this point.
    report = get_object_or_404(PetReport, pk=report_id, report_type='Found', status__in=['Pending Adoption', 'Open'])
    
    # Check if the report is 'Open' and if it has actually passed the 15-day mark, as a security measure
    if report.status == 'Open':
        if report.date_reported > (timezone.now() - datetime.timedelta(days=15)):
             messages.error(request, "This 'Open' report is not yet eligible for adoption processing.")
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

            # Close the original report
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
    """
    total_admins = User.objects.filter(is_staff=True, is_superuser=False).count()
    total_normal_users = User.objects.filter(is_staff=False).count()
    pets_for_adoption_count = PetForAdoption.objects.filter(status="Available").count()
    lost_reports_count = PetReport.objects.filter(report_type="Lost", status="Open").count()
    found_reports_count = PetReport.objects.filter(report_type="Found", status="Open").count()
    unapproved_reports_count = PetReport.objects.filter(is_approved=False).count()

    context = {
        "total_normal_users": total_normal_users,
        "total_admins": total_admins,
        "pets_for_adoption_count": pets_for_adoption_count,
        "lost_reports_count": lost_reports_count,
        "found_reports_count": found_reports_count,
        "unapproved_reports_count": unapproved_reports_count,
    }
    return render(request, "admin/dashboard.html", context)


@staff_required
def admin_moderate_reports_view(request):
    """
    Admin view to list reports awaiting approval.
    """
    reports_to_moderate = PetReport.objects.filter(is_approved=False).order_by("-date_reported")
    context = {"reports_to_moderate": reports_to_moderate}
    return render(request, "admin/moderate_reports.html", context)


@staff_required
def admin_approve_report_view(request, report_id):
    """
    Admin action to approve a pet report, making it public.
    """
    if request.method == "POST":
        report = get_object_or_404(PetReport, pk=report_id)

        if report.is_approved:
            messages.warning(request, f"Report #{report.pk} is already approved.")
            return redirect("users:admin_moderate_reports")

        report.is_approved = True
        report.save()
        messages.success(
            request,
            f"Report #{report.pk} ({report.report_type}) has been successfully approved and is now visible on the dashboard.",
        )
        return redirect("users:admin_moderate_reports")

    messages.error(request, "Invalid request method.")
    return redirect("users:admin_moderate_reports")


@staff_required
def admin_reject_report_view(request, report_id):
    """
    Admin action to reject a pet report.
    """
    if request.method == "POST":
        report = get_object_or_404(PetReport, pk=report_id)
        report.delete()
        messages.success(request, f"Report #{report_id} ({report.report_type}) has been successfully rejected and deleted.")
        return redirect("users:admin_moderate_reports")

    messages.error(request, "Invalid request method.")
    return redirect("users:admin_moderate_reports")


@staff_required
def admin_manage_users_view(request):
    """
    Lists all non-superuser users for management.
    """
    users_to_manage = User.objects.filter(is_superuser=False).select_related("profile")
    context = {"users": users_to_manage}
    return render(request, "admin/manage_users.html", context)


@superuser_required
def admin_promote_user_view(request, user_id):
    if request.method == "POST":
        current_admin_count = User.objects.filter(is_staff=True, is_superuser=False).count()
        if current_admin_count >= 3:
            messages.error(request, "Cannot promote user. The maximum number of 3 admins has been reached.")
            return redirect("users:admin_manage_users")

        try:
            user_to_promote = User.objects.get(pk=user_id)
            if user_to_promote.is_superuser or user_to_promote.is_staff:
                messages.warning(request, "This user is already a superuser or admin.")
            else:
                user_to_promote.is_staff = True
                user_to_promote.save()

                if hasattr(user_to_promote, "profile"):
                    user_to_promote.profile.role = "admin"
                    user_to_promote.profile.save()

                messages.success(request, f"User '{user_to_promote.username}' has been promoted to Admin.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")

    return redirect("users:admin_manage_users")


@staff_required
def admin_remove_user_view(request, user_id):
    """
    Remove a user. Staff can remove normal users; only superuser may remove staff members.
    """
    if request.method == "POST":
        try:
            user_to_remove = User.objects.get(pk=user_id)

            # Prevent self-deletion through this interface
            if user_to_remove == request.user:
                messages.error(request, "You cannot remove your own account from this interface.")
                return redirect("users:admin_manage_users")

            # Only superusers can remove staff members
            if user_to_remove.is_staff and not request.user.is_superuser:
                messages.error(request, "You do not have permission to remove an admin user.")
                return redirect("users:admin_manage_users")

            if user_to_remove.is_superuser:
                messages.error(request, "Superusers cannot be removed from this interface.")
                return redirect("users:admin_manage_users")

            username = user_to_remove.username
            user_to_remove.delete()
            messages.success(request, f"User '{username}' has been removed successfully.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")

    return redirect("users:admin_manage_users")


@staff_required
def admin_view_user_reports(request, user_id):
    """
    Admin view to display all reports submitted by a specific user.
    """
    try:
        user = User.objects.get(pk=user_id)
        reports = PetReport.objects.filter(reporter=user).order_by("-date_reported")

        context = {"user": user, "reports": reports}
        return render(request, "admin/user_reports.html", context)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("users:admin_manage_users")


def user_report_history_view(request, user_id):
    """
    View to display the report history of a specific user.
    """
    try:
        user = User.objects.get(pk=user_id)
        reports = PetReport.objects.filter(reporter=user).order_by("-date_reported")

        context = {"user": user, "reports": reports}
        return render(request, "admin/user_report_history.html", context)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("users:admin_manage_users")
