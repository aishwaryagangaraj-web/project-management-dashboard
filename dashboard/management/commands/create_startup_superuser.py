from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the one-time deployment superuser if it does not already exist."

    def handle(self, *args, **options):
        User = get_user_model()
        username = "aishwarya"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS("Deployment superuser already exists."))
            return

        User.objects.create_superuser(
            username=username,
            email="aishwaryagangaraj@gmail.com",
            password="Aishu@123",
        )
        self.stdout.write(self.style.SUCCESS("Deployment superuser created."))
