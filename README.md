# Hospital Management API (Django + Ninja)

This repository contains a Django-based backend API for a hospital management system.

The project exposes endpoints for authentication, patient management, and department management. It uses Django ORM models mapped to an existing MySQL database schema for hospital entities such as patients, doctors, appointments, billing, wards, and prescriptions.

## Project Structure

```text
hospital_management/
├── apidemo/
│   ├── db.sqlite3
│   ├── manage.py
│   └── apidemo/
│       ├── __init__.py
│       ├── admin.py
│       ├── api.py
│       ├── asgi.py
│       ├── models.py
│       ├── settings.py
│       ├── urls.py
│       └── wsgi.py
└── venv/
```

## Tech Stack

- Python
- Django
- Django Ninja (API layer)
- django-cors-headers
- MySQL (configured as primary DB)

## High-Level Architecture

- `apidemo/apidemo/models.py`: Database model layer (reverse-engineered from existing DB tables).
- `apidemo/apidemo/api.py`: API routes, request/response schemas, and authentication handlers.
- `apidemo/apidemo/urls.py`: Root URL routing (`/admin/`, `/api/`).
- `apidemo/apidemo/settings.py`: Project settings (apps, middleware, CORS, DB connection, etc.).
- `apidemo/manage.py`: Django management entry point.

## Database Model Overview

The app maps these core entities:

- `Patient`
- `Doctor`
- `Department`
- `Appointment`
- `Medicalrecord`
- `Prescription`
- `Prescriptiondetail`
- `Medicine`
- `Inpatient`
- `Ward`
- `Bill`
- `Staff`

Important notes:

- Most models are marked `managed = False`, meaning Django will not create/alter these tables via migrations by default.
- The schema appears to be generated from an already existing database (`inspectdb`-style output).

## API Overview

Base path: `/api/`

### Authentication

- `POST /api/auth/register`
  - Creates a Django user.
  - Payload: `{ "username": "...", "password": "..." }`

- `POST /api/auth/login`
  - Authenticates and creates Django session.
  - Payload: `{ "username": "...", "password": "..." }`

- `POST /api/auth/logout`
  - Logs out and clears session/csrf cookies.

Auth mechanism:

- Session-cookie based auth via custom `APIKeyCookie` class (`sessionid`).
- Some routes explicitly use `auth=None` (public), while others use the global API auth.

### Patients

- `GET /api/patients`
- `GET /api/patients/{patientid}`
- `POST /api/patients`
- `POST /api/patients/{patientid}`
- `PUT /api/patients/{patientid}`
- `PATCH /api/patients/{patientid}`
- `DELETE /api/patients/{patientid}`

### Departments

- `GET /api/department`
- `GET /api/department/{deptid}`
- `POST /api/department`
- `POST /api/department/{deptid}`

## CORS Configuration

Allowed frontend origins are configured for common local dev ports:

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:4173`
- `http://127.0.0.1:4173`

Credentials are enabled (`CORS_ALLOW_CREDENTIALS = True`), which is required for cookie-based auth from frontend clients.

## Local Setup

### 1. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install django django-ninja django-cors-headers mysqlclient
```

If `mysqlclient` fails to build on your machine, install system MySQL dev libraries first, then retry.

### 3. Configure database

The project currently expects a MySQL database in `apidemo/apidemo/settings.py`:

- Engine: `django.db.backends.mysql`
- Database: `HospitalManagementDB`
- Host: `localhost`
- Port: `3306`

Update credentials and host as needed for your local environment.

### 4. Run the server

```bash
cd apidemo
python manage.py runserver
```

Server default: `http://127.0.0.1:8000`

### 5. Access endpoints

- Admin: `http://127.0.0.1:8000/admin/`
- API root: `http://127.0.0.1:8000/api/`

## Development Notes

- Because models are unmanaged (`managed = False`), treat this project as API-first over an existing DB schema.
- If you plan to fully manage schema in Django, you would need to revisit model definitions and migration strategy.
- There are a few naming/style inconsistencies in responses and route naming (for example singular `department` path and typo-like response keys).

## Suggested Next Improvements

- Add a `requirements.txt` or `pyproject.toml` for reproducible setup.
- Move DB credentials to environment variables (`.env`) and remove secrets from source.
- Normalize endpoint naming and HTTP method usage for full REST consistency.
- Add automated tests for auth and CRUD endpoints.
- Add pagination/filtering for list endpoints.

## Push Protection (Avoid Unwanted Files)

This repository includes two protections:

- `.gitignore` to avoid tracking common unwanted files (`venv/`, `.env`, `*.sqlite3`, cache files, editor folders).
- A custom pre-push hook at `.githooks/pre-push` that blocks pushes if commit content includes typical sensitive/unnecessary files.

### Enable pre-push hook

If your project is already a Git repo:

```bash
chmod +x scripts/setup-hooks.sh
./scripts/setup-hooks.sh
```

If Git is not initialized yet:

```bash
git init
chmod +x scripts/setup-hooks.sh
./scripts/setup-hooks.sh
```

### What gets blocked

- Virtual environment folders (`venv/`, `.venv/`)
- Local env secrets (`.env`, `.env.*`)
- Local DB files (`db.sqlite3`)
- Python cache folders (`__pycache__/`)
- Staged additions in `apidemo/apidemo/settings.py` that look like hardcoded `PASSWORD` or `SECRET_KEY`

When blocked, fix by unstaging files and recommit only what is needed.

## License

No license file is currently included in this repository.
