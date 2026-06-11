from django.core.management.base import BaseCommand

from dashboard.demo_data import DEMO_PASSWORD, DEMO_USERNAME, reset_demo_data, seed_demo_data


class Command(BaseCommand):
    help = "Seed realistic demo data for the project management dashboard."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo-owned records and recreate demo data.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            result = reset_demo_data()
        else:
            result = seed_demo_data()

        self.stdout.write(self.style.SUCCESS("Demo user and data synced successfully."))
        self.stdout.write(f"Login with username: {DEMO_USERNAME}")
        self.stdout.write(f"Password: {DEMO_PASSWORD}")
        self.stdout.write(
            "Created "
            f"{len(result['projects'])} projects, "
            f"{len(result['tasks'])} tasks, "
            f"{len(result['notifications'])} notifications, and "
            f"{len(result['activity_logs'])} activity logs."
        )
