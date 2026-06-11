# Project Management Dashboard

A professional Django-based Project Management Dashboard for tracking projects, tasks, deadlines, notifications, activity logs, and analytics from a single workspace.

Live Demo: https://project-management-dashboard-j8ih.onrender.com

## Project Overview

This project is designed as a portfolio-ready full-stack Django application. It includes authentication, project and task management, dashboard analytics, notifications, activity tracking, responsive UI, and production deployment configuration for Render.

The dashboard is built to resemble a modern SaaS productivity tool, with a dark sidebar, top navigation, statistic cards, Chart.js visualizations, professional tables, badges, progress bars, and polished authentication pages.

## Features

- User authentication with login, registration, logout, and protected routes
- Project CRUD with owner-based access control
- Task CRUD with status, priority, due dates, and assignee tracking
- Mark task as completed workflow
- Project progress tracking based on completed tasks
- Search and filters for projects and tasks
- Status, priority, and due date badges
- Dashboard statistic cards for projects and tasks
- Chart.js analytics for task status and project progress
- Notifications with unread count and mark-as-read flow
- Activity logs for project and task events
- Demo data seeding command for populated dashboards
- Responsive SaaS-style UI
- Render deployment setup with Gunicorn, WhiteNoise, and environment-based settings

## Screenshots

Add screenshots here after deployment or local testing.

Suggested screenshots:

- Login page
- Dashboard command center
- Project list
- Project detail page
- Task list
- Analytics page

Example:

```md
![Dashboard Screenshot](screenshots/dashboard.png)
```

## Tech Stack

- Python
- Django
- SQLite for local development
- PostgreSQL support for production
- Chart.js
- HTML5
- CSS3
- JavaScript
- Gunicorn
- WhiteNoise
- dj-database-url
- python-decouple
- Render

## Installation

Clone the repository:

```bash
git clone https://github.com/aishwaryagangaraj-web/project-management-dashboard.git
cd project-management-dashboard
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

For local development, you can keep SQLite by leaving `DATABASE_URL` empty or removing it from `.env`.

Run migrations:

```bash
python manage.py migrate
```

Create demo data:

```bash
python manage.py seed_demo_data
```

Run the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Demo user created by the seed command:

```text
Username: demo_admin
Password: demo12345
```

## Deployment

Live deployment:

https://project-management-dashboard-j8ih.onrender.com

The project is configured for Render deployment.

Build command:

```bash
bash build.sh
```

Start command:

```bash
gunicorn project_management_dashboard.wsgi:application
```

Required Render environment variables:

```env
SECRET_KEY=your-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=project-management-dashboard-j8ih.onrender.com
DATABASE_URL=your-render-postgres-url
CSRF_TRUSTED_ORIGINS=https://project-management-dashboard-j8ih.onrender.com
```

Static files are handled with WhiteNoise.

## Folder Structure

```text
project_management_dashboard/
|-- accounts/                      # Authentication and profile logic
|-- analytics/                     # Activity logs and analytics app
|-- dashboard/                     # Dashboard views and demo data command
|   `-- management/commands/
|       `-- seed_demo_data.py
|-- notifications/                 # Notification models, views, and context processor
|-- projects/                      # Project models, forms, views, and URLs
|-- tasks/                         # Task models, forms, views, and URLs
|-- project_management_dashboard/  # Core Django settings, URLs, WSGI/ASGI
|-- static/                        # CSS and JavaScript assets
|-- templates/                     # Shared and app templates
|-- media/                         # User-uploaded media
|-- build.sh                       # Render build script
|-- requirements.txt               # Python dependencies
|-- .env.example                   # Environment variable template
`-- manage.py
```

## Future Improvements

- Add team invitations and role-based permissions
- Add comments and file attachments for tasks
- Add Kanban board view
- Add calendar view for deadlines
- Add email notifications
- Add REST API using Django REST Framework
- Add automated tests for major workflows
- Add pagination and advanced sorting for large datasets
- Add project export reports as PDF or CSV

## Author

Developed by Aishwarya Gangaraj.

GitHub: https://github.com/aishwaryagangaraj-web

Live Demo: https://project-management-dashboard-j8ih.onrender.com
