# Render Deployment Guide

This project is now prepared for deployment on Render with:

- Render Web Service for Django.
- Render Postgres for the database.
- WhiteNoise for static files.
- Cloudinary for uploaded student and teacher images.
- Gunicorn as the production WSGI server.
- Environment variables for secrets and production configuration.

## Files Added or Updated

```text
build.sh
render.yaml
requirements.txt
HOME/settings.py
.gitignore
```

## Why These Changes Are Needed

Render services use an ephemeral filesystem by default. That means files created by the running app are not reliable permanent storage across deploys. For this project:

- `db.sqlite3` must not be used in production.
- Uploaded images in `media/` must not be used as production storage.
- Static files should be collected during build and served through WhiteNoise.

The production setup is:

```text
Django on Render Web Service
Postgres on Render
Uploaded images on Cloudinary
Static files via WhiteNoise
Secrets in Render environment variables
```

## Deployment Option 1: Render Blueprint

The repo includes `render.yaml`, so you can deploy through a Render Blueprint.

1. Push the latest code to GitHub.
2. Open the Render Dashboard.
3. Go to **Blueprints**.
4. Click **New Blueprint Instance**.
5. Connect the GitHub repository.
6. Select this repo.
7. Apply the blueprint.

Render will create:

- A web service named `schoolsys`.
- A Postgres database named `schoolsys-db`.
- A generated `SECRET_KEY`.
- A `DATABASE_URL` connected to the Postgres database.

## Deployment Option 2: Manual Render Setup

If you prefer doing it manually:

1. Create a Render Postgres database.
2. Create a Render Web Service.
3. Connect the GitHub repo.
4. Set the build command:

```bash
bash build.sh
```

5. Set the start command:

```bash
gunicorn HOME.wsgi:application
```

6. Add the environment variables listed below.

## Required Environment Variables

Set these in the Render service environment.

```env
DEBUG=False
SECRET_KEY=generate-a-long-secret-key
ALLOWED_HOSTS=.onrender.com
DATABASE_URL=postgresql://...
```

Render can generate `SECRET_KEY` automatically when using the blueprint.

## Email Environment Variables

Required for password reset email:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com
```

For Gmail, use an app password, not your normal account password.

## Cloudinary Environment Variable

Create a Cloudinary account and copy your Cloudinary URL.

Set:

```env
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

With this set, uploaded student and teacher images will be stored in Cloudinary instead of Render's local filesystem.

## Build Script

`build.sh` runs:

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

This installs dependencies, prepares static files, and applies database migrations.

## After First Deploy

Create the production admin account from the Render Shell:

```bash
python manage.py createsuperuser
```

Then log in at:

```text
https://your-service-name.onrender.com/admin/
```

## Local Development Still Works

If no `DATABASE_URL` is set, the app uses local SQLite:

```text
db.sqlite3
```

If no Cloudinary variables are set, uploads use local media storage:

```text
media/
```

Both are ignored by Git.

## Production Safety Checklist

Before sharing the site:

- Confirm `DEBUG=False`.
- Confirm `.env`, `db.sqlite3`, and `media/` are not tracked by Git.
- Confirm `.env.example` contains placeholders only.
- Rotate any secrets that were previously pushed.
- Confirm Cloudinary upload works.
- Confirm password reset email works.
- Confirm student registration works.
- Confirm admin approval flow works.
- Confirm search suggestions work.
- Confirm `createsuperuser` was run on Render.

## Notes

Render's Django deployment guide recommends Postgres, WhiteNoise, a build script, and Gunicorn for Django services. The included configuration follows that pattern.
