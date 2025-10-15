
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import PetReport, PetForAdoption
from django.contrib.auth.models import User
import datetime

class Command(BaseCommand):
    help = 'Automatically converts approved, unclaimed found pets into adoption listings after 15 days.'

    def handle(self, *args, **options):
        self.stdout.write("Starting job to process found pets for adoption...")

        
        system_user = User.objects.filter(is_superuser=True).order_by('pk').first()
        if not system_user:
            self.stdout.write(self.style.ERROR(
                "CRITICAL: No superuser found to act as the lister. "
                "Please create a superuser. Aborting."
            ))
            return

        
        
        threshold_datetime = timezone.now() - datetime.timedelta(days=15)

        
        
        eligible_reports = PetReport.objects.filter(
            report_type='Found',
            status='Open',
            is_approved=True,
            date_reported__lt=threshold_datetime  
        )

        if not eligible_reports.exists():
            self.stdout.write(self.style.SUCCESS("No new pets are eligible for automatic adoption listing today."))
            return

        self.stdout.write(f"Found {eligible_reports.count()} pet(s) to process for adoption.")
        
        pets_listed_count = 0
        for report in eligible_reports:
            try:
                
                pet_name = report.name if report.name else f"Friendly {report.pet_type}"

                
                description = (
                    f"This lovely {report.pet_type} was found near {report.location} on "
                    f"{report.event_date.strftime('%B %d, %Y')}. After a waiting period, "
                    f"this pet is now looking for a loving forever home!"
                )
                
                
                PetForAdoption.objects.create(
                    name=pet_name,
                    age=report.age or 1,  
                    gender=report.gender,
                    pet_type=report.pet_type,
                    breed=report.breed,
                    color=report.color,
                    image=report.pet_image,  
                    description=description,
                    lister=system_user,
                    status='Available'
                )

                
                report.status = 'Closed'
                report.save()
                
                pets_listed_count += 1
                self.stdout.write(self.style.SUCCESS(f"  - Successfully listed pet from report ID {report.id} for adoption."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  - FAILED to process report ID {report.id}: {e}"))

        self.stdout.write(f"\nJob finished. Successfully listed {pets_listed_count} pet(s) for adoption.")