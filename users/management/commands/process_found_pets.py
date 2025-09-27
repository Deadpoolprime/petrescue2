# users/management/commands/process_found_pets.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import PetReport, Notification, User
import datetime

class Command(BaseCommand):
    help = 'Flags unclaimed found pets older than 15 days and notifies admins.'

    def handle(self, *args, **options):
        self.stdout.write("Checking for found pets eligible for adoption...")

        # 1. Define the time threshold (15 days ago)
        fifteen_days_ago = timezone.now() - datetime.timedelta(days=15)

        # 2. Find all 'Found' pet reports that are still 'Open' and older than 15 days
        eligible_reports = PetReport.objects.filter(
            report_type='Found',
            status='Open',
            date_reported__lt=fifteen_days_ago
        )

        if not eligible_reports.exists():
            self.stdout.write(self.style.SUCCESS("No new pets are eligible for adoption today."))
            return

        # 3. Find all admin users to notify
        admin_users = User.objects.filter(is_staff=True)
        if not admin_users.exists():
            self.stdout.write(self.style.ERROR("No admin users found to notify."))
            return

        notification_count = 0
        # 4. For each eligible report, create a notification for each admin
        for report in eligible_reports:
            # Create a notification message
            message = (
                f"The found '{report.pet_type}' (Report ID: {report.id}) "
                f"reported on {report.date_reported.strftime('%Y-%m-%d')} is now eligible for adoption."
            )

            # Check if a similar notification already exists to avoid duplicates
            for admin in admin_users:
                if not Notification.objects.filter(recipient=admin, pet_report=report).exists():
                    Notification.objects.create(
                        recipient=admin,
                        pet_report=report, # Link the notification to the report
                        message=message
                    )
                    notification_count += 1

            # IMPORTANT: We change the status of the PetReport to 'Pending Adoption'
            # This prevents it from being picked up by this script again.
            report.status = 'Pending Adoption' # You'll need to add this to your STATUS_CHOICES
            report.save()

        self.stdout.write(self.style.SUCCESS(
            f"Created {notification_count} new notifications for {eligible_reports.count()} eligible pets."
        ))