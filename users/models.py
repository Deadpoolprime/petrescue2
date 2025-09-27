from django.db import models
from django.contrib.auth.models import User

# This model extends Django's User to add the 'role' field.
class Profile(models.Model):
    ROLE_CHOICES = (('admin', 'Admin'), ('user', 'User'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    age = models.PositiveIntegerField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_picture = models.ImageField(default='profile_pics/default.png', upload_to='profile_pics/', null=True, blank=True)
    def __str__(self): return f"{self.user.username} Profile"

# This table handles both LOST and FOUND pet "incidents".
class PetReport(models.Model):
    REPORT_TYPE_CHOICES = (('Lost', 'I lost my pet'), ('Found', 'I found a pet'))
    STATUS_CHOICES = (('Open', 'Open'), ('Closed', 'Closed'))
    GENDER_CHOICES = (('Male', 'Male'), ('Female', 'Female'), ('Unknown', 'Unknown')) # Add gender choices here

    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pet_reports')

    # NEW FIELDS ADDED:
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Pet's name (if known)") # Optional name
    age = models.PositiveIntegerField(null=True, blank=True, help_text="Pet's age in years (if known)") # Optional age
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Unknown', help_text="Pet's gender") # Gender field

    pet_type = models.CharField(max_length=50, help_text="e.g., Dog, Cat, Bird")
    breed = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50)
    pet_image = models.ImageField(upload_to='pet_images/')
    location = models.CharField(max_length=255, help_text="Area where the pet was lost or found.")
    contact_info = models.CharField(max_length=255, help_text="Your phone or email for contact.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    date_reported = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Updated __str__ to include name if available
        pet_name = self.name if self.name else "Unnamed Pet"
        return f"{self.get_report_type_display()}: {pet_name} ({self.pet_type}) by {self.reporter.username}"

# This separate table is a catalog for pets available for ADOPTION.
class PetForAdoption(models.Model):
    GENDER_CHOICES = (('Male', 'Male'), ('Female', 'Female'), ('Unknown', 'Unknown'))
    ADOPTION_STATUS_CHOICES = (('Available', 'Available'), ('Pending', 'Adoption Pending'), ('Adopted', 'Adopted'))
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(help_text="Age in years.")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Unknown')
    pet_type = models.CharField(max_length=50)
    breed = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50)
    image = models.ImageField(upload_to='adoption_images/')
    description = models.TextField(help_text="Describe the pet's personality, story, and needs.")
    lister = models.ForeignKey(User, on_delete=models.CASCADE, related_name='adoption_listings')
    status = models.CharField(max_length=10, choices=ADOPTION_STATUS_CHOICES, default='Available')
    date_listed = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.name} ({self.pet_type}) - {self.get_status_display()}"

# This table handles notifications from the system/admins to users.
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    pet_report = models.ForeignKey(PetReport, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Notification for {self.recipient.username}: {self.message[:30]}..."