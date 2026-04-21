from django.core.management.base import BaseCommand
from apps.creators.models import CreatorProfile
from django.db.models import Q
from utils.send_emails import send_reminder_to_complete_profile

class Command(BaseCommand):
    help = 'Send reminder emails to CreatorProfiles with incomplete profiles (unverified)'

    def handle(self, *args, **options):
        # Any bio with either (bio, or cover/profile image) missing is considered incomplete
        incomplete_profiles = CreatorProfile.objects.filter(
            Q(bio='') | Q(profile_image='') | Q(cover_image='')
        )
        self.stdout.write(self.style.SUCCESS(
            f'✓ Found {incomplete_profiles.count()} incomplete profiles'))

        for profile in incomplete_profiles:
            sent = send_reminder_to_complete_profile(profile.user.email)
            if sent:
                self.stdout.write(self.style.SUCCESS(f'✓ Sent reminder to {profile.user.email}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ Failed to send reminder to {profile.user.email}'))