# users/admin.py

from django.contrib import admin
from .models import Profile, PetReport, PetForAdoption, Notification

# These classes customize how the models are displayed in the admin interface.

class PetReportAdmin(admin.ModelAdmin):
    """Customizes the display for PetReport in the admin."""
    list_display = ('id', 'report_type', 'pet_type', 'status', 'reporter', 'date_reported', 'location')
    list_filter = ('status', 'report_type', 'pet_type')
    search_fields = ('location', 'breed', 'reporter__username')
    readonly_fields = ('date_reported',)
    list_per_page = 25

class PetForAdoptionAdmin(admin.ModelAdmin):
    """Customizes the display for PetForAdoption in the admin."""
    list_display = ('name', 'pet_type', 'status', 'lister', 'date_listed')
    list_filter = ('status', 'pet_type', 'gender')
    search_fields = ('name', 'breed', 'lister__username')
    readonly_fields = ('date_listed',)

class ProfileAdmin(admin.ModelAdmin):
    """Customizes the display for user Profiles."""
    list_display = ('user', 'role', 'city', 'phone_number')
    search_fields = ('user__username', 'city')

class NotificationAdmin(admin.ModelAdmin):
    """Customizes the display for Notifications."""
    list_display = ('recipient', 'message_summary', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('recipient__username', 'message')

    def message_summary(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_summary.short_description = 'Message'

# Register your models with the admin site
admin.site.register(PetReport, PetReportAdmin)
admin.site.register(PetForAdoption, PetForAdoptionAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Notification, NotificationAdmin)