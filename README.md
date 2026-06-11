# Project Management Dashboard

Advanced Django project scaffold with built-in authentication, SQLite, app-level URLs, shared templates, static assets, and media support.

## Apps

- `accounts`
- `dashboard`
- `projects`
- `tasks`
- `notifications`
- `analytics`

## Setup

Python is required before these commands can run.

```powershell
cd C:\Users\HP\Desktop\folders\codetech\project_management_dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Then open `http://127.0.0.1:8000/`.
