# ProjectFlow

ProjectFlow is a Django-based project management dashboard built for portfolio, interview, and production-style demonstrations. It combines RBAC, Kanban, calendar scheduling, comments, attachments, reminders, exports, analytics, and a JWT-backed API in one workspace.

Live demo: https://project-management-dashboard-j8ih.onrender.com

## What It Includes

- Authentication with registration, login, logout, profile, and avatar upload
- Role-based access control for Admin, Project Manager, and Team Member
- Projects with owner and member management
- Tasks with statuses, priorities, due dates, Kanban, calendar, comments, and files
- Notifications, activity logs, analytics, and dashboard quick links
- Automatic demo data seeding for empty deployments on Render
- Dark/light theme with persisted preference
- PDF export for project, task, and analytics reports
- REST API with JWT auth and Swagger docs
- Landing page, architecture diagram page, custom error pages, and responsive UI polish

## Screenshots

Use the generated preview asset in the repo:

```md
![ProjectFlow dashboard preview](static/images/dashboard-preview.png)
```

Recommended screenshots for the README:

- Landing page
- Dashboard
- Kanban board
- Calendar view
- Task detail with comments and attachments
- Analytics and PDF export
- API docs

## Architecture

The application is split into focused Django apps:

- `accounts` for authentication, profiles, avatars, and role helpers
- `projects` for project CRUD and membership
- `tasks` for task workflow, Kanban, calendar, comments, and attachments
- `notifications` for in-app alerts and email reminders
- `analytics` for charts and overview data
- `reports` for PDF generation
- `api` for JWT-authenticated REST endpoints
- `dashboard` for the landing page, dashboard shell, and architecture page

See the architecture page in the app at `/architecture/`.

## API

The REST API is mounted at `/api/` and includes:

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/profile/`
- `PATCH /api/auth/profile/`
- CRUD for projects and tasks
- Task comments and file upload endpoints
- Notifications list and mark-read endpoints
- Analytics stats endpoint
- Swagger docs at `/api/docs/`

## Tech Stack

- Python 3
- Django
- Django REST Framework
- JWT authentication
- drf-spectacular
- ReportLab
- Chart.js
- HTML, CSS, JavaScript
- WhiteNoise
- Gunicorn
- PostgreSQL on Render

## Local Setup

```bash
git clone https://github.com/aishwaryagangaraj-web/project-management-dashboard.git
cd project-management-dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver 8001
```

Open:

```text
http://127.0.0.1:8001/
```

## Demo Credentials

The deployment seeds demo data automatically when the database is empty.

```text
Username: aishwarya
Password: Aishu@123
Email: aishwaryagangaraj@gmail.com
```

## Render Deployment

This project is configured to run on Render without shell access.

Build command:

```bash
bash build.sh
```

Start command:

```bash
gunicorn project_management_dashboard.wsgi:application
```

Required environment variables:

```env
SECRET_KEY=replace-me
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DATABASE_URL=your-postgres-url
CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com
SITE_URL=https://your-app.onrender.com
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=ProjectFlow <no-reply@your-app.com>
```

## Key Pages

- `/` landing page for anonymous visitors
- `/dashboard/` authenticated overview
- `/projects/`
- `/tasks/`
- `/tasks/kanban/`
- `/tasks/calendar/`
- `/analytics/`
- `/reports/analytics/`
- `/api/docs/`
- `/architecture/`

## Notes

- Demo data is only created when the database is empty, so Render restarts do not duplicate records.
- Email reminders are wired to Django's email backend and support SMTP environment variables.
- Custom 404 and 500 pages are included for production use.

## Author

Developed by Aishwarya Gangaraj.

GitHub: https://github.com/aishwaryagangaraj-web
