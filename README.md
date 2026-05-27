# SchoolSys - Django Student Management System

SchoolSys is a Django-based student management system for schools and learning institutions. It is built around the same practical goal as many end-to-end Django student-management tutorials: replace manual student record keeping with a secure web application where authorized users can add, view, update, search, approve, and manage school data.

The project currently includes student and teacher profiles, role-based dashboards, student records, guardian information, departments, subjects, fees, fee collections, expenses, salaries, exams, events, timetables, library books, notifications, password reset, profile approval, live search suggestions, and export tools.

## Table of Contents

- [Project Purpose](#project-purpose)
- [Core Features](#core-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Application Modules](#application-modules)
- [Data Models](#data-models)
- [User Roles and Permissions](#user-roles-and-permissions)
- [Main Workflows](#main-workflows)
- [Search System](#search-system)
- [Notifications](#notifications)
- [Authentication and Password Reset](#authentication-and-password-reset)
- [Installation and Local Setup](#installation-and-local-setup)
- [Environment Variables](#environment-variables)
- [Database and Migrations](#database-and-migrations)
- [Static and Media Files](#static-and-media-files)
- [Important URLs](#important-urls)
- [Admin Panel](#admin-panel)
- [Security Notes](#security-notes)
- [Development Notes](#development-notes)
- [Known Limitations and Future Improvements](#known-limitations-and-future-improvements)

For production hosting, see [DEPLOYMENT_RENDER.md](DEPLOYMENT_RENDER.md).

## Project Purpose

Managing student information manually can become slow, inconsistent, and unsafe as a school grows. This project provides a structured Django application where school staff can manage academic and administrative records from one place.

The system is designed to:

- Store student records in a database instead of paper or spreadsheets.
- Keep guardian and contact information attached to each student.
- Support teacher records and class assignment data.
- Let administrators manage school entities such as departments, subjects, exams, events, timetables, fees, and books.
- Provide authentication so only authorized users can access protected pages.
- Separate access between administrators, students, and teachers.
- Give students and teachers dashboards that show information relevant to them.
- Allow profile submissions to be reviewed before becoming approved records.
- Provide searchable records with live suggestions.

## Core Features

### Student Management

Administrators can:

- Add new students.
- View all students.
- Open detailed student profiles.
- Edit student records.
- Delete student records.
- Approve or reject submitted student profiles.
- Export student data as XLS, DOCX, or PDF.

Student records include:

- First name and last name.
- Student ID.
- Gender.
- Date of birth.
- Class.
- Section.
- Religion.
- Joining date.
- Mobile number.
- Admission number.
- Profile image.
- Parent or guardian details.
- Present and permanent address.
- Approval status.

### Teacher Management

Administrators can:

- Add teachers.
- View teacher lists.
- Open teacher details.
- Edit teacher profiles.
- Delete teacher records.
- Approve or reject submitted teacher profiles.

Teacher records include:

- Teacher ID.
- Name.
- Gender.
- Date of birth.
- Mobile number.
- Joining date.
- Qualification.
- Experience.
- Username and email.
- Address details.
- Assigned class, subject, and section.
- Profile image.
- Approval status.

### Profile Completion and Approval

When a student or teacher creates an account, they are guided to complete their profile. Submitted profiles are marked as pending until an administrator approves or rejects them.

This makes the system safer than immediately trusting every public registration. It supports a workflow where:

1. A user registers as student or teacher.
2. The user completes a profile form.
3. Administrators review pending profiles.
4. Administrators approve or reject the profile.
5. The user receives a notification about the decision.

### Dashboards

The project has role-aware dashboards:

- Admin dashboard: school overview and management navigation.
- Student dashboard: fees, payments, events, library count, upcoming exams, and timetable.
- Teacher dashboard: assigned classes, subjects, events, and timetable entries.

### School Management Modules

The system also contains management pages for:

- Departments.
- Subjects.
- Holidays.
- Fees.
- Fee collections.
- Expenses.
- Salaries.
- Exams.
- Events.
- Timetable entries.
- Library books.

### Authentication

The authentication flow includes:

- Login by email.
- Registration for public student and teacher accounts.
- Logout.
- Password reset request.
- Password reset token expiry.
- Login activity tracking.
- Role assignment through groups.

### Live Search

The top navigation search bar supports:

- Search after submit.
- Live suggestions while typing.
- Token-based matching, so a query like `Tony W` can match `Tony Wangolo`.
- Searching across students, teachers, fees, exams, events, and library books.

### Notifications

Users receive notifications for account and profile events. The header displays the unread notification count and recent notifications.

Examples:

- Account created.
- Profile submitted.
- Profile approved.
- Profile rejected.
- Role updated.
- Student or teacher records changed.

## Technology Stack

- Python
- Django 6.0.2
- SQLite for local development
- Pillow for image uploads
- Django templates
- Bootstrap
- Font Awesome
- jQuery
- DataTables

The pinned Python dependencies are in `requirements.txt`:

```txt
Django==6.0.2
Pillow==12.0.0
dj-database-url==3.0.1
django-cloudinary-storage==0.3.0
gunicorn==23.0.0
psycopg[binary]==3.2.13
whitenoise==6.12.0
```

## Project Structure

```text
HOME/
├── HOME/                     # Django project package
│   ├── settings.py           # Project settings
│   ├── urls.py               # Root URL routing
│   ├── wsgi.py
│   ├── asgi.py
│   ├── static/               # CSS, JS, images, plugins
│   └── templates/            # Shared and app templates
│       ├── Home/             # Auth, dashboard, base templates
│       └── students/         # Student, teacher, and school pages
├── home_auth/                # Authentication, roles, notifications
├── school/                   # Main landing/admin dashboard routing
├── student/                  # Student, teacher, and school management logic
├── media/                    # Uploaded files in local development
├── manage.py
├── requirements.txt
├── .gitignore
├── .env                      # Local secrets, ignored by Git
└── .env.example              # Local sample env file with placeholder values
```

## Application Modules

### `HOME`

This is the Django project package. It contains global configuration and URL routing.

Important files:

- `HOME/settings.py`: database, templates, static files, media files, email settings, login settings.
- `HOME/urls.py`: connects the root app, student app, authentication app, admin panel, and media serving in debug mode.
- `HOME/templates/Home/base.html`: shared dashboard layout, header, sidebar, notifications, and live search.

### `home_auth`

This app handles authentication and account-related features.

Responsibilities:

- Register users.
- Log users in by email.
- Log users out.
- Assign roles using Django groups.
- Manage role updates by administrators.
- Track login activity.
- Create password reset requests.
- Send reset emails.
- Store and display notifications.

Important files:

- `home_auth/models.py`
- `home_auth/views.py`
- `home_auth/urls.py`
- `home_auth/notifications.py`
- `home_auth/context_processors.py`

### `student`

This app contains most of the school management functionality.

Responsibilities:

- Student CRUD.
- Teacher CRUD.
- Profile approval.
- Dashboards.
- Search.
- Exports.
- Departments.
- Subjects.
- Fees and fee collection.
- Expenses.
- Salaries.
- Exams.
- Events.
- Timetables.
- Library.

Important files:

- `student/models.py`
- `student/views.py`
- `student/urls.py`
- `student/admin.py`

### `school`

This app controls the root dashboard behavior. Its main view redirects users to the correct dashboard based on their role.

## Data Models

### `Parent`

Stores guardian information for a student.

Fields include:

- Father name.
- Father occupation.
- Father mobile.
- Father email.
- Mother name.
- Mother occupation.
- Mother mobile.
- Mother email.
- Present address.
- Permanent address.

### `Student`

Stores student profile and school information.

Relationships:

- One-to-one with a Django user account.
- One-to-one with `Parent`.

Important fields:

- `approval_status`: pending, approved, or rejected.
- `first_name`
- `last_name`
- `student_id`
- `gender`
- `date_of_birth`
- `student_class`
- `religion`
- `joining_date`
- `mobile_number`
- `admission_number`
- `section`
- `student_image`
- `slug`

### `Teacher`

Stores teacher profile information.

Relationships:

- One-to-one with a Django user account.

Important fields:

- `approval_status`
- `teacher_id`
- `name`
- `gender`
- `date_of_birth`
- `mobile`
- `joining_date`
- `qualification`
- `experience`
- `username`
- `email`
- `address`
- `city`
- `state`
- `zip_code`
- `country`
- `teacher_class`
- `subject`
- `section`
- `teacher_image`
- `slug`

### `Department`

Stores school departments.

Fields include:

- Department ID.
- Name.
- Head of department.
- Start date.
- Number of students.

### `Subject`

Stores subjects taught by the school.

Fields include:

- Subject ID.
- Name.
- Subject class.

### `Holiday`

Stores school holiday dates.

Fields include:

- Holiday ID.
- Name.
- Holiday type.
- Start date.
- End date.

### `Fee`

Stores fee definitions for classes.

Fields include:

- Fee ID.
- Name.
- Student class.
- Amount.
- Start date.
- End date.

### `FeeCollection`

Stores payment records from students.

Relationships:

- Many fee collections can belong to one student.
- A fee collection can optionally be linked to a fee.

Fields include:

- Receipt number.
- Student.
- Fee.
- Amount paid.
- Payment date.
- Status: paid, partial, unpaid.

### `Expense`

Stores school expense records.

Fields include:

- Expense ID.
- Title.
- Category.
- Amount.
- Expense date.
- Description.

### `Salary`

Stores teacher salary payment information.

Relationships:

- Many salaries can belong to one teacher.

Fields include:

- Salary ID.
- Teacher.
- Amount.
- Salary month.
- Payment date.
- Status.

### `Exam`

Stores exam scheduling information.

Fields include:

- Name.
- Student class.
- Subject.
- Fee.
- Start time.
- End time.
- Exam date.

### `Event`

Stores school events.

Fields include:

- Title.
- Event type.
- Start date.
- End date.
- Description.

### `TimeTableEntry`

Stores class timetable rows.

Relationships:

- A timetable entry can be assigned to a teacher.

Fields include:

- Day.
- Student class.
- Section.
- Subject.
- Teacher.
- Start time.
- End time.

### `Book`

Stores library book information.

Fields include:

- Book ID.
- Title.
- Author.
- Subject.
- Publisher.
- Quantity.
- Available copies.

### Authentication Models

The `home_auth` app also defines:

- `CustomUser`: a role-aware user model class.
- `LoginActivity`: login audit trail.
- `PasswordResetRequest`: reset token, expiry, and usage tracking.
- `Notification`: user notifications.

Important implementation note: the current `settings.py` does not explicitly set `AUTH_USER_MODEL`, so the running project may use Django's default `auth.User` unless this is changed before migrations are applied in a fresh database. The views are written defensively and use groups as the main role mechanism, so the app can still work with the default user model.

## User Roles and Permissions

The project uses three roles:

- `admin`
- `student`
- `teacher`

Roles are assigned through Django groups and, where available, role fields on the user model.

### Admin

Administrators can:

- Access the admin dashboard.
- Manage user roles.
- Review pending student and teacher profiles.
- Add, edit, delete, approve, and reject students.
- Add, edit, delete, approve, and reject teachers.
- Manage departments and subjects.
- Manage fee records and fee collections.
- Manage expenses and salaries.
- Manage exams, events, timetables, holidays, and library books.
- View notifications.

### Student

Students can:

- Register a student account.
- Complete a student profile.
- View their student dashboard.
- View class fees.
- View their fee collections/payments.
- View exams for their class.
- View timetable entries for their class and section.
- View events and library records.
- Search records available to their role.

### Teacher

Teachers can:

- Register a teacher account.
- Complete a teacher profile.
- View their teacher dashboard.
- View their timetable assignments.
- View school events, holidays, exams, and library records.
- Search records available to their role.

## Main Workflows

### Student Registration Workflow

1. A user opens the registration page.
2. They provide first name, last name, email, role, password, and password confirmation.
3. The system validates the password using Django password validators.
4. The account is created.
5. The selected role is applied.
6. The user is logged in.
7. The user is redirected to complete the student profile.
8. The submitted profile is marked as pending.
9. An administrator reviews and approves or rejects it.

### Teacher Registration Workflow

1. A user registers as a teacher.
2. The teacher role is applied.
3. The user completes a teacher profile.
4. The profile is marked as pending.
5. An administrator reviews and approves or rejects it.

### Admin-Created Student Workflow

1. An administrator opens the add student page.
2. The administrator enters student and guardian information.
3. The student is created with approved status.
4. Notifications are created for the administrator and other admins.

### Admin-Created Teacher Workflow

1. An administrator opens the add teacher page.
2. The administrator enters teacher profile information.
3. The system attempts to link the teacher profile to a user with the same email.
4. The teacher profile is created as approved.
5. Notifications are sent.

### Profile Approval Workflow

1. A student or teacher submits a profile.
2. The profile appears in Pending Approvals.
3. Admin clicks approve or reject.
4. The profile status changes.
5. A notification is created for the profile owner.

## Search System

The search system lives in `student/views.py` and uses Django `Q` objects.

It supports:

- Submitted searches through `/student/search/`.
- Live suggestions through `/student/search/suggestions/`.
- Token-based matching, so multi-word searches work better.

Examples:

- `Tony`
- `Tony W`
- `420`
- `Class 4`

The search currently checks:

- Students: first name, last name, student ID, admission number, class, section.
- Teachers: name, teacher ID, subject, class, section.
- Fees: name, fee ID, class.
- Exams: name, subject, class.
- Events: title, type, description.
- Library books: title, author, subject, book ID.

Results are limited per category to keep suggestions fast and readable.

## Notifications

Notifications are stored in the `Notification` model and made available globally through `home_auth.context_processors.notifications`.

The shared base template uses this context to display:

- Unread count.
- Recent notifications.
- Notification dropdown.
- Current user display name.
- Current user profile image when available.
- Current user role labels.

Notification routes include:

- View all notifications.
- Mark one notification as read.
- Mark all notifications as read.

## Authentication and Password Reset

Authentication is implemented in `home_auth/views.py`.

### Login

Users log in using email and password. Internally, the view finds the user by email and authenticates with the user's actual username.

### Registration

Public registration supports:

- Student accounts.
- Teacher accounts.

Admin accounts should be created through Django admin or by an existing administrator changing roles.

### Password Reset

The password reset flow:

1. User submits email.
2. If the account exists, a `PasswordResetRequest` is created.
3. A reset URL is emailed.
4. The token expires after one hour.
5. The token can only be used once.

Email settings are read from `.env`.

## Installation and Local Setup

These instructions assume Windows PowerShell because this project is being developed in that environment.

### 1. Clone the Repository

```powershell
git clone https://github.com/captainblair/schoolsys.git
cd schoolsys
```

If your project root is the `HOME` folder, enter it:

```powershell
cd HOME
```

### 2. Create a Virtual Environment

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If your environment is outside the project folder, use the path that matches your local setup.

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create a Local `.env`

The project loads environment variables from `.env` in the same directory as `manage.py`.

Create a local `.env` file:

```powershell
New-Item .env -ItemType File
```

Add values similar to:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com
```

Do not commit `.env`.

### 5. Apply Migrations

```powershell
python manage.py migrate
```

### 6. Create a Superuser

```powershell
python manage.py createsuperuser
```

### 7. Run the Development Server

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Environment Variables

The project reads local settings from `.env` when present. In production, set these values through the hosting provider's environment variable UI.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Use `True` locally and `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hostnames allowed by Django |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted HTTPS origins when needed |
| `DATABASE_URL` | Production database URL; local SQLite is used when empty |
| `CLOUDINARY_URL` | Cloudinary media storage URL for uploaded images |
| `EMAIL_BACKEND` | Django email backend |
| `EMAIL_HOST` | SMTP host |
| `EMAIL_PORT` | SMTP port |
| `EMAIL_USE_TLS` | Whether TLS is used |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password or app password |
| `DEFAULT_FROM_EMAIL` | Sender email address |

For Render deployment, see [DEPLOYMENT_RENDER.md](DEPLOYMENT_RENDER.md).

## Database and Migrations

The project uses SQLite by default for local development. If `DATABASE_URL` is set, Django uses that database instead, which is how the Render deployment connects to Postgres.

The local database file `db.sqlite3` is ignored by Git. This is important because a database can contain private user data, emails, passwords hashes, student records, guardian information, and operational school data.

## Static and Media Files

### Static Files

Static files are stored in:

```text
HOME/static/
```

This includes:

- CSS.
- JavaScript.
- Images.
- Bootstrap assets.
- Font Awesome assets.
- DataTables assets.

### Media Files

In local development, uploaded files are stored in:

```text
media/
```

Student images are uploaded to:

```text
media/student/
```

Teacher images are uploaded to:

```text
media/teacher/
```

In development, media files are served by `HOME/urls.py` when `DEBUG` is true. In production, set `CLOUDINARY_URL` so uploaded student and teacher images are stored in Cloudinary instead of Render's temporary filesystem.

## Important URLs

### Root and Dashboard

| URL | Purpose |
| --- | --- |
| `/` | Role-aware dashboard entry |
| `/admin/` | Django admin panel |

### Authentication

| URL | Purpose |
| --- | --- |
| `/authentication/login/` | Login |
| `/authentication/register/` | Register |
| `/authentication/logout/` | Logout |
| `/authentication/forgot-password/` | Request password reset |
| `/authentication/reset-password/<token>/` | Reset password |
| `/authentication/user-roles/` | Admin role management |
| `/authentication/notifications/` | User notifications |

### Student and Teacher

| URL | Purpose |
| --- | --- |
| `/student/students/` | Student list |
| `/student/students/add/` | Add student |
| `/student/students/view/<id>/` | Student detail |
| `/student/students/edit/<id>/` | Edit student |
| `/student/students/complete-profile/` | Student profile completion |
| `/student/students/dashboard/` | Student dashboard |
| `/student/teachers/` | Teacher list |
| `/student/teachers/add/` | Add teacher |
| `/student/teachers/view/<id>/` | Teacher detail |
| `/student/teachers/edit/<id>/` | Edit teacher |
| `/student/teachers/complete-profile/` | Teacher profile completion |
| `/student/teachers/dashboard/` | Teacher dashboard |
| `/student/approvals/` | Pending profile approvals |

### Management

| URL | Purpose |
| --- | --- |
| `/student/departments/` | Departments |
| `/student/subjects/` | Subjects |
| `/student/holiday/` | Holidays |
| `/student/fees/` | Fees |
| `/student/fees-collections/` | Fee collections |
| `/student/expenses/` | Expenses |
| `/student/salary/` | Salaries |
| `/student/exam/` | Exams |
| `/student/events/` | Events |
| `/student/time-table/` | Timetable |
| `/student/library/` | Library |

### Search

| URL | Purpose |
| --- | --- |
| `/student/search/` | Search results page |
| `/student/search/suggestions/` | Live search JSON suggestions |

## Admin Panel

The Django admin panel is available at:

```text
/admin/
```

Registered models include:

- Login activity.
- Password reset requests.
- Notifications.
- Parents.
- Students.
- Teachers.
- Departments.
- Subjects.
- Holidays.
- Fees.
- Fee collections.
- Expenses.
- Salaries.
- Exams.
- Events.
- Timetable entries.
- Books.

## Security Notes

### Environment Files

`.env` is ignored by Git in this repository.

It should never be committed because it can contain:

- Email credentials.
- API keys.
- Database passwords.
- Secret keys.
- Service tokens.

If secrets were ever pushed to GitHub, deleting the file from the latest commit is not enough. The values may still exist in Git history. Rotate exposed credentials immediately.

### Database File

`db.sqlite3` is ignored by Git because it can contain real user and school data.

### Passwords

The app uses Django's password hashing and validation. Plain-text passwords should never be stored.

### Debug Mode

`DEBUG=True` is fine for local development only. Set `DEBUG=False` in production.

### Secret Key

The production `SECRET_KEY` should come from environment variables. Render can generate it automatically when using `render.yaml`.

### Allowed Hosts

Production deployments must configure `ALLOWED_HOSTS`. The included `render.yaml` sets `.onrender.com` and the settings file also trusts Render's generated external hostname.

## Development Notes

### Run Checks

```powershell
python manage.py check
```

### Make Migrations

```powershell
python manage.py makemigrations
```

### Apply Migrations

```powershell
python manage.py migrate
```

### Start Server

```powershell
python manage.py runserver
```

### Create Superuser

```powershell
python manage.py createsuperuser
```

### Export Students

Student records can be downloaded in:

- XLS.
- DOCX.
- PDF.

Routes:

```text
/student/students/download/xls/
/student/students/download/docx/
/student/students/download/pdf/
```

## Known Limitations and Future Improvements

The project is functional for local development and learning, but several improvements would make it stronger for production.

Recommended improvements:

- Explicitly configure `AUTH_USER_MODEL` before starting a new production database if the custom user model should be used.
- Add automated tests for authentication, permissions, CRUD flows, profile approval, and search.
- Add pagination for large student, teacher, and management lists.
- Add stronger form validation and Django `ModelForm` usage.
- Add audit logs for create, update, delete, approve, and reject actions.
- Add role-specific UI cleanup so each user only sees actions they can actually perform.
- Add richer student academic records such as grades, attendance, and report cards.
- Add parent or guardian login if the school wants parent access.

## Summary

SchoolSys is a Django student management system designed to centralize school data and reduce manual record keeping. It supports authentication, role-aware access, student and teacher profile management, administrative CRUD pages, notifications, live search, and core school management modules.

It is a strong foundation for a school information system and can be extended with attendance, grading, parent access, reporting, and production deployment features.
