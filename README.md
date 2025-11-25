# Choosie Backend

A Django-based backend API for managing users, restaurants, and OTP authentication.

---

## Table of Contents

- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Project](#running-the-project)
- [API Endpoints](#api-endpoints)


---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/username/choosie_backend.git
cd choosie_backend
```
2. Create a virtual environment:
   
```bash
python -m venv venv
# Activate environment:
# On Linux/Mac
source venv/bin/activate
# On Windows
venv\Scripts\activate
```

## Install dependencies:

```bash
pip install -r requirements.txt
```
## Environment Variables
```bash
DEBUG=True
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (default is SQLite)
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

# Email configuration
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_email_password
EMAIL_USE_TLS=True
```
You can change the database by updating DATABASE_ENGINE, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, etc.


## Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

Create a superuser for admin access:
```bash
python manage.py createsuperuser
```
## Running the Project
```bash
python manage.py runserver
```


## API Endpoints

| Method       | Endpoint                                | Description                              | Auth Required     |
|--------------|-----------------------------------------|------------------------------------------|-------------------|
| `POST`       | `/api/auth/register/`                   | Register a new user                      | No                |
| `POST`       | `/api/auth/login/`                      | User login (returns token/session)       | No                |
| `POST`       | `/api/auth/password-reset-request/`     | Send OTP to registered email             | No                |
| `POST`       | `/api/auth/password-reset-verify/`      | Verify OTP & reset password              | No                |
| `POST`       | `/api/auth/'password/reset/`           | Reset password                           | No                |
| `GET`        | `/api/auth/password/change/`           | Change the user passowrd                 | No                |

### API Documentation
Interactive API docs powered by Swagger/OpenAPI:

- **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
- **ReDoc**: `http://127.0.0.1:8000/api/redoc/` *(if added)*

> Tip: Use `drf-yasg` or `drf-spectacular` to auto-generate beautiful docs

