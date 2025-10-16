from django.contrib import admin
from .models import Profile, PetReport, PetForAdoption, Notification,  Message


class PetReportAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'report_type', 'pet_type', 'status', 'reporter', 'date_reported', 'location', 'health_information', 'injury')
    list_filter = ('status', 'report_type', 'pet_type')
    search_fields = ('location', 'breed', 'reporter__username')
    readonly_fields = () 
    list_per_page = 25

class PetForAdoptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'pet_type', 'status', 'lister', 'date_listed')
    list_filter = ('status', 'pet_type', 'gender')
    search_fields = ('name', 'breed', 'lister__username')
    readonly_fields = ('date_listed',)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'city', 'phone_number')
    search_fields = ('user__username', 'city')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message_summary', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('recipient__username', 'message')

    def message_summary(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_summary.short_description = 'Message'

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'content_summary', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('sender__username', 'recipient__username', 'content')

    def content_summary(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_summary.short_description = 'Content'

admin.site.register(PetReport, PetReportAdmin)
admin.site.register(PetForAdoption, PetForAdoptionAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Message, MessageAdmin)