# users/management/commands/process_found_pets.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import PetReport, PetForAdoption
from django.contrib.auth.models import User
import datetime

class Command(BaseCommand):
    help = 'Automatically converts approved, unclaimed found pets into adoption listings after 15 days.'

    def handle(self, *args, **options):
        self.stdout.write("Starting job to process found pets for adoption...")

        # Find a system user (first superuser) to be the "lister"
        system_user = User.objects.filter(is_superuser=True).order_by('pk').first()
        if not system_user:
            self.stdout.write(self.style.ERROR(
                "CRITICAL: No superuser found to act as the lister. "
                "Please create a superuser. Aborting."
            ))
            return

        # 1. Define the time threshold (15 days ago from now).
        # This will be a datetime object, suitable for comparing with date_reported.
        threshold_datetime = timezone.now() - datetime.timedelta(days=15)

        # 2. Find all 'Found' pet reports that are approved, still 'Open', and reported more than 15 days ago.
        # --- CORRECTED LOGIC: Using `date_reported` instead of `event_date` ---
        eligible_reports = PetReport.objects.filter(
            report_type='Found',
            status='Open',
            is_approved=True,
            date_reported__lt=threshold_datetime  # Use the report date for the 15-day rule
        )

        if not eligible_reports.exists():
            self.stdout.write(self.style.SUCCESS("No new pets are eligible for automatic adoption listing today."))
            return

        self.stdout.write(f"Found {eligible_reports.count()} pet(s) to process for adoption.")
        
        pets_listed_count = 0
        for report in eligible_reports:
            try:
                # Generate a default name if not provided
                pet_name = report.name if report.name else f"Friendly {report.pet_type}"

                # Generate a default description (still uses event_date for public info, which is correct)
                description = (
                    f"This lovely {report.pet_type} was found near {report.location} on "
                    f"{report.event_date.strftime('%B %d, %Y')}. After a waiting period, "
                    f"this pet is now looking for a loving forever home!"
                )
                
                # 3. Create the new PetForAdoption object
                PetForAdoption.objects.create(
                    name=pet_name,
                    age=report.age or 1,  # Default to 1 year old if age is unknown
                    gender=report.gender,
                    pet_type=report.pet_type,
                    breed=report.breed,
                    color=report.color,
                    image=report.pet_image,  # Django handles copying the file
                    description=description,
                    lister=system_user,
                    status='Available'
                )

                # 4. IMPORTANT: Close the original report to prevent re-processing
                report.status = 'Closed'
                report.save()
                
                pets_listed_count += 1
                self.stdout.write(self.style.SUCCESS(f"  - Successfully listed pet from report ID {report.id} for adoption."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  - FAILED to process report ID {report.id}: {e}"))

        self.stdout.write(f"\nJob finished. Successfully listed {pets_listed_count} pet(s) for adoption.")