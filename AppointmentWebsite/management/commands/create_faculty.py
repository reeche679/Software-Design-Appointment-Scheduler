from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from AppointmentWebsite.models import UserProfile

class Command(BaseCommand):
    help = 'Creates a faculty user'

    def handle(self, *args, **options):
        # Create the user
        user = User.objects.create_user(
            username='fel',
            password='cpefaculty',
            email='fel@example.com'
        )
        user.save()

        # Create the user profile
        profile = UserProfile.objects.create(
            user=user,
            user_type='faculty'
        )
        profile.save()

        self.stdout.write(self.style.SUCCESS('Successfully created faculty user "fel"')) 