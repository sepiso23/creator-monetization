from django.core.management.base import BaseCommand
from apps.creators.models import CreatorProfile
from django.db.models import Q
from utils.send_emails import welcome_early_adopter_email

class Command(BaseCommand):
    help = 'Send reminder emails to CreatorProfiles with incomplete profiles (unverified)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--end_period',
            type=str,
            default='2024-05-30',
            help='End date of the early adopter period (YYYY-MM-DD). Defaults to 2024-05-30.'
        )

    def handle(self, *args, **options):
        # Any bio with either (bio, or cover/profile image) missing is considered incomplete
        incomplete_profiles = CreatorProfile.objects.filter(
            Q(bio='') | Q(profile_image='') | Q(cover_image='')
        )
        self.stdout.write(self.style.SUCCESS(
            f'✓ Found {incomplete_profiles.count()} incomplete profiles'))

        for profile in incomplete_profiles:
            sent = welcome_early_adopter_email(profile.user.email)
            if sent:
                self.stdout.write(self.style.SUCCESS(f'✓ Sent welcome email to {profile.user.email}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ Failed to send welcome email to {profile.user.email}'))