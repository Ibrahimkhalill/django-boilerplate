# Django Boilerplate ⚡

**Production-ready, clean & minimal Django + DRF starter template**  
Perfect for quickly bootstrapping any backend project with secure user authentication, OTP system, email setup, and API documentation.

Ideal for MVPs, SaaS backends, mobile app APIs, freelance projects, or learning.

---

## Features

- User Registration & Login
- Secure OTP-based Password Reset (via Email)
- Email configuration ready (SMTP)
- Custom User Model support ready
- REST API with Django REST Framework
- Swagger / ReDoc API documentation support
- Admin panel with superuser
- SQLite by default (easy switch to PostgreSQL)
- Clean project structure
- Ready for deployment

---

## Table of Contents

- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Project](#running-the-project)
- [API Endpoints](#api-endpoints)
- [API Documentation](#api-documentation)
- [Production Tips](#production-tips)
- [License](#license)

---

## Installation

```bash
git clone https://github.com/yourusername/django-boilerplate.git
cd django-boilerplate
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

| Method | Endpoint                            | Description                        |
| ------ | ----------------------------------- | ---------------------------------- |
| `POST` | `/api/auth/register/`               | Register a new user                |
| `POST` | `/api/auth/login/`                  | User login (returns token/session) |
| `POST` | `/api/auth//otp/create_otp/`        | New otp create                     |
| `POST` | `/api/auth//otp/verify_otp/`        | Verify otp for signup              |
| `POST` | `/api/auth/password-reset-request/` | Send OTP to registered email       |
| `POST` | `/api/auth/password-reset-verify/`  | Verify OTP & reset password        |
| `POST` | `/api/auth/password/reset/`         | Reset password                     |
| `GET`  | `/api/auth/password/change/`        | Change the user passowrd           |

### API Documentation

Interactive API docs powered by Swagger/OpenAPI:

- **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
- **ReDoc**: `http://127.0.0.1:8000/api/redoc/` _(if added)_

> Tip: Use `drf-yasg` or `drf-spectacular` to auto-generate beautiful docs
