from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from analytics.models import ActivityLog
from notifications.models import Notification
from projects.models import Project
from tasks.models import Task


class Command(BaseCommand):
    help = "Seed realistic demo data for the project management dashboard."

    def handle(self, *args, **options):
        with transaction.atomic():
            user = self._get_demo_user()
            self._clear_existing_demo_data(user)

            projects = self._create_projects(user)
            tasks = self._create_tasks(user, projects)
            self._create_notifications(user, tasks)
            self._create_activity_logs(user, projects, tasks)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write("Login with username: demo_admin")
        self.stdout.write("Password: demo12345")
        self.stdout.write(f"Created {len(projects)} projects and {len(tasks)} tasks.")

    def _get_demo_user(self):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username="demo_admin",
            defaults={
                "email": "demo@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.email = "demo@example.com"
        user.is_staff = True
        user.is_superuser = True
        user.set_password("demo12345")
        user.save()
        return user

    def _clear_existing_demo_data(self, user):
        Project.objects.filter(owner=user, slug__startswith="demo-").delete()
        Notification.objects.filter(
            recipient=user,
            title__in=[
                "Task due soon",
                "Review requested",
                "Blocked task",
                "Project completed",
                "New assignment",
            ],
        ).delete()
        ActivityLog.objects.filter(actor=user, metadata__seed_demo=True).delete()

    def _create_projects(self, user):
        today = timezone.localdate()
        project_specs = [
            {
                "name": "Customer Success Portal",
                "slug": "demo-customer-success-portal",
                "description": "A client-facing portal for onboarding, support tickets, renewals, and account health tracking.",
                "status": "active",
                "priority": "critical",
                "start": today - timedelta(days=35),
                "due": today + timedelta(days=28),
                "budget": "85000.00",
            },
            {
                "name": "Mobile App Redesign",
                "slug": "demo-mobile-app-redesign",
                "description": "A refreshed mobile experience with cleaner navigation, faster task flows, and improved accessibility.",
                "status": "active",
                "priority": "high",
                "start": today - timedelta(days=22),
                "due": today + timedelta(days=45),
                "budget": "64000.00",
            },
            {
                "name": "Q3 Marketing Automation",
                "slug": "demo-q3-marketing-automation",
                "description": "Automated campaign journeys, lead scoring, reporting dashboards, and CRM handoff improvements.",
                "status": "planning",
                "priority": "medium",
                "start": today + timedelta(days=5),
                "due": today + timedelta(days=70),
                "budget": "42000.00",
            },
            {
                "name": "Data Warehouse Modernization",
                "slug": "demo-data-warehouse-modernization",
                "description": "Migration of legacy reporting pipelines into a scalable warehouse with reliable business metrics.",
                "status": "paused",
                "priority": "high",
                "start": today - timedelta(days=60),
                "due": today + timedelta(days=30),
                "budget": "120000.00",
            },
            {
                "name": "Internal HR Workflow System",
                "slug": "demo-internal-hr-workflow-system",
                "description": "Self-service employee requests, approval workflows, onboarding checklists, and HR analytics.",
                "status": "completed",
                "priority": "low",
                "start": today - timedelta(days=95),
                "due": today - timedelta(days=8),
                "budget": "38000.00",
            },
        ]

        projects = []
        for spec in project_specs:
            project = Project.objects.create(
                name=spec["name"],
                slug=spec["slug"],
                description=spec["description"],
                owner=user,
                status=spec["status"],
                priority=spec["priority"],
                start_date=spec["start"],
                due_date=spec["due"],
                budget=Decimal(spec["budget"]),
            )
            projects.append(project)
        return projects

    def _create_tasks(self, user, projects):
        now = timezone.now()
        today = timezone.localdate()
        task_specs = [
            (0, "Design customer onboarding dashboard", "Build the main onboarding overview with milestones and account owner context.", "done", "high", -18, now - timedelta(days=4), 8),
            (0, "Implement ticket escalation workflow", "Create automated routing for high-priority support tickets.", "in_progress", "urgent", 6, None, 12),
            (0, "Add renewal risk indicators", "Surface account health, product usage, and renewal blockers.", "review", "high", 12, None, 10),
            (0, "Create customer document center", "Allow customers to access shared onboarding and contract files.", "todo", "medium", 18, None, 7),
            (1, "Audit mobile navigation patterns", "Review current mobile navigation and document friction points.", "done", "medium", -12, now - timedelta(days=7), 5),
            (1, "Build redesigned project board view", "Create the mobile board layout with status columns and quick actions.", "in_progress", "high", 9, None, 14),
            (1, "Optimize mobile task detail page", "Improve task metadata density and responsive readability.", "todo", "medium", 16, None, 6),
            (1, "Run accessibility contrast review", "Validate color contrast and keyboard focus behavior.", "todo", "high", 21, None, 4),
            (2, "Map campaign lifecycle stages", "Define the marketing lifecycle from acquisition to handoff.", "done", "medium", -5, now - timedelta(days=2), 6),
            (2, "Create lead scoring rules", "Score leads by engagement, firmographics, and buying intent.", "in_progress", "high", 14, None, 9),
            (2, "Draft nurture email sequence", "Prepare email content for evaluation and reactivation journeys.", "todo", "medium", 20, None, 8),
            (2, "Connect CRM attribution fields", "Sync campaign source data into CRM reporting fields.", "blocked", "urgent", 3, None, 6),
            (3, "Inventory legacy reporting jobs", "Catalog existing ETL jobs, owners, and downstream dashboards.", "done", "high", -30, now - timedelta(days=15), 10),
            (3, "Design warehouse star schema", "Model core facts and dimensions for revenue and product analytics.", "review", "high", 7, None, 16),
            (3, "Migrate product usage pipeline", "Move usage events into the new transformation framework.", "blocked", "urgent", -2, None, 18),
            (3, "Create data quality checks", "Add freshness, volume, uniqueness, and referential integrity tests.", "todo", "high", 11, None, 8),
            (4, "Build employee request intake", "Create forms for HR requests and route them to the correct team.", "done", "medium", -42, now - timedelta(days=25), 8),
            (4, "Implement approval notifications", "Send approval and rejection updates to employees and managers.", "done", "medium", -28, now - timedelta(days=20), 7),
            (4, "Create onboarding checklist templates", "Add reusable templates for department-specific onboarding.", "done", "low", -18, now - timedelta(days=12), 5),
            (4, "Publish HR analytics summary", "Finalize reporting cards for requests, SLA, and onboarding completion.", "done", "low", -10, now - timedelta(days=6), 4),
        ]

        tasks = []
        for project_index, title, description, status, priority, due_offset, completed_at, estimate in task_specs:
            task = Task.objects.create(
                project=projects[project_index],
                title=title,
                description=description,
                assignee=user,
                reporter=user,
                status=status,
                priority=priority,
                estimate_hours=Decimal(str(estimate)),
                due_date=today + timedelta(days=due_offset),
                completed_at=completed_at,
            )
            tasks.append(task)
        return tasks

    def _create_notifications(self, user, tasks):
        notifications = [
            ("Task due soon", "Implement ticket escalation workflow is due this week.", "warning", tasks[1].get_absolute_url(), False),
            ("Review requested", "Add renewal risk indicators is ready for review.", "info", tasks[2].get_absolute_url(), False),
            ("Blocked task", "Connect CRM attribution fields needs integration access.", "danger", tasks[11].get_absolute_url(), False),
            ("Project completed", "Internal HR Workflow System has been completed successfully.", "success", tasks[19].get_absolute_url(), True),
            ("New assignment", "Create data quality checks has been assigned to you.", "info", tasks[15].get_absolute_url(), False),
        ]

        for title, message, level, link, is_read in notifications:
            Notification.objects.create(
                recipient=user,
                title=title,
                message=message,
                level=level,
                link=link,
                is_read=is_read,
            )

    def _create_activity_logs(self, user, projects, tasks):
        for project in projects:
            ActivityLog.objects.create(
                actor=user,
                action="created",
                object_type="project",
                object_id=project.pk,
                metadata={
                    "seed_demo": True,
                    "object_name": project.name,
                    "message": f"Created project {project.name}",
                },
            )

        for task in tasks:
            action = "status_changed" if task.status != "done" else "updated"
            ActivityLog.objects.create(
                actor=user,
                action=action,
                object_type="task",
                object_id=task.pk,
                metadata={
                    "seed_demo": True,
                    "object_name": task.title,
                    "message": f"Updated task {task.title}",
                },
            )
