# Peace CDA - Community Finance Platform

A full-stack web app for Peace CDA to track member financial records, levy contributions, payments, and credits.

## Stack
Backend: Python, Django, Django REST Framework, SimpleJWT, Celery
Frontend: React 19, Vite, Tailwind CSS v4, TanStack Query, Recharts
Database: SQLite (dev), PostgreSQL (production)

## Features
- Member portal - login and view own levies, payments, credits
- Levy templates - bulk-assign any future project levy
- Auto payment allocation - excess becomes member credit
- Notifications - SMS (Termii) + Email (SendGrid) + in-app
- Monthly debt reminders via Celery Beat
- Financial Secretary protection - add-only permissions + audit log
- Analytics - top contributors, defaulters, collection rate

## Run Locally
### Backend
  cd community
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py runserver

### Frontend
  cd peacecda-portal
  npm install
  npm run dev

Open http://localhost:5173
