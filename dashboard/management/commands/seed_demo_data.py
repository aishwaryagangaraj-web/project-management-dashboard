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
        self.stdout.write(f"Created {len(projects)} projects, {len(tasks)} tasks, notifications, and activity logs.")

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
        Notification.objects.filter(recipient=user, title__startswith="[Demo]").delete()
        ActivityLog.objects.filter(actor=user, metadata__seed_demo=True).delete()

    def _create_projects(self, user):
        today = timezone.localdate()
        project_specs = [
            {
                "name": "AI Resume Analyzer",
                "slug": "demo-ai-resume-analyzer",
                "description": "AI-powered resume parser that scores candidates, extracts skills, and recommends matching job roles.",
                "status": "active",
                "priority": "critical",
                "start": today - timedelta(days=34),
                "due": today + timedelta(days=21),
                "budget": "72000.00",
            },
            {
                "name": "E-commerce Platform",
                "slug": "demo-e-commerce-platform",
                "description": "Full-stack storefront with product catalog, cart, checkout, payment integration, and order tracking.",
                "status": "active",
                "priority": "high",
                "start": today - timedelta(days=48),
                "due": today + timedelta(days=35),
                "budget": "95000.00",
            },
            {
                "name": "CRM Dashboard",
                "slug": "demo-crm-dashboard",
                "description": "Sales CRM dashboard for leads, deals, pipeline health, team performance, and revenue analytics.",
                "status": "planning",
                "priority": "medium",
                "start": today - timedelta(days=8),
                "due": today + timedelta(days=52),
                "budget": "56000.00",
            },
            {
                "name": "Portfolio Website",
                "slug": "demo-portfolio-website",
                "description": "Professional personal portfolio with project case studies, contact workflow, blog, and SEO optimization.",
                "status": "completed",
                "priority": "low",
                "start": today - timedelta(days=70),
                "due": today - timedelta(days=5),
                "budget": "18000.00",
            },
            {
                "name": "Smart Expense Tracker",
                "slug": "demo-smart-expense-tracker",
                "description": "Expense management app with category automation, monthly budgets, alerts, and spending analytics.",
                "status": "paused",
                "priority": "high",
                "start": today - timedelta(days=28),
                "due": today + timedelta(days=26),
                "budget": "44000.00",
            },
        ]

        projects = []
        for spec in project_specs:
            projects.append(
                Project.objects.create(
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
            )
        return projects

    def _create_tasks(self, user, projects):
        now = timezone.now()
        today = timezone.localdate()
        task_specs = [
            (0, "Build login API", "Implement secure authentication endpoints with validation and session handling.", "done", "high", -18, now - timedelta(days=13), 8),
            (0, "Create resume upload pipeline", "Accept PDF/DOCX resumes and store parsed files for AI processing.", "done", "high", -12, now - timedelta(days=9), 10),
            (0, "Integrate skills extraction model", "Extract skills, education, experience, and role recommendations from resumes.", "in_progress", "urgent", 5, None, 16),
            (0, "Create analytics chart", "Show resume score distribution, top skills, and candidate role matches.", "review", "medium", 10, None, 7),
            (1, "Design dashboard UI", "Create admin dashboard layouts for orders, revenue, products, and inventory.", "done", "high", -20, now - timedelta(days=14), 12),
            (1, "Build product catalog module", "Add product listing, filtering, categories, and product detail pages.", "in_progress", "high", 6, None, 14),
            (1, "Implement cart and checkout", "Build cart, checkout validation, shipping options, and payment handoff.", "todo", "urgent", 13, None, 18),
            (1, "Deploy application", "Configure production settings, static files, database, and Render deployment.", "todo", "high", 20, None, 6),
            (2, "Create leads pipeline view", "Build Kanban-style lead pipeline with deal value and stage filters.", "todo", "medium", 16, None, 9),
            (2, "Fix authentication bug", "Resolve login redirects and role-based dashboard access for CRM users.", "blocked", "urgent", 3, None, 5),
            (2, "Build sales performance cards", "Add revenue, conversion rate, active deals, and monthly targets cards.", "in_progress", "high", 9, None, 8),
            (2, "Create analytics chart", "Add pipeline value, deal status, and lead source charts using real data.", "todo", "medium", 18, None, 10),
            (3, "Design landing page", "Create hero, project showcase, skills, and contact sections.", "done", "medium", -42, now - timedelta(days=34), 8),
            (3, "Add project case studies", "Write and publish case study pages for portfolio projects.", "done", "low", -31, now - timedelta(days=25), 6),
            (3, "Optimize SEO metadata", "Add page titles, descriptions, sitemap, and structured metadata.", "done", "medium", -18, now - timedelta(days=16), 5),
            (3, "Deploy application", "Publish the portfolio and validate production performance.", "done", "low", -8, now - timedelta(days=6), 4),
            (4, "Build expense category rules", "Automatically classify expenses into food, travel, bills, shopping, and savings.", "done", "medium", -15, now - timedelta(days=10), 7),
            (4, "Create monthly budget alerts", "Notify users when spending approaches monthly category limits.", "in_progress", "high", 4, None, 8),
            (4, "Design spending insights dashboard", "Create charts for category trends, recurring expenses, and savings rate.", "review", "high", 11, None, 10),
            (4, "Fix authentication bug", "Correct account session handling and protected route redirects.", "blocked", "urgent", -1, None, 5),
        ]

        tasks = []
        for project_index, title, description, status, priority, due_offset, completed_at, estimate in task_specs:
            tasks.append(
                Task.objects.create(
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
            )
        return tasks

    def _create_notifications(self, user, tasks):
        notifications = [
            ("[Demo] Urgent bug blocked", "CRM Dashboard authentication bug is blocking QA sign-off.", "danger", tasks[9].get_absolute_url(), False),
            ("[Demo] Task due soon", "Smart Expense Tracker budget alerts are due this week.", "warning", tasks[17].get_absolute_url(), False),
            ("[Demo] Review requested", "AI Resume Analyzer analytics chart is ready for review.", "info", tasks[3].get_absolute_url(), False),
            ("[Demo] Deployment pending", "E-commerce Platform deployment task is waiting for production setup.", "warning", tasks[7].get_absolute_url(), False),
            ("[Demo] Project completed", "Portfolio Website has been completed and deployed.", "success", tasks[15].get_absolute_url(), True),
            ("[Demo] New assignment", "Product catalog module has been assigned to the demo admin.", "info", tasks[5].get_absolute_url(), False),
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
            action = "updated"
            if task.status in {"in_progress", "review", "blocked"}:
                action = "status_changed"
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
