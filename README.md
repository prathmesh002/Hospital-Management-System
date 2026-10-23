# Hospital Management System — Django edition

A conversion of the PHP/MySQL "Hospital-Management-System-PHP" project to **Python 3 + Django**.
Same three portals (patient, doctor, admin) and the same public landing page, rebuilt on Django's
ORM, forms, auth and templates. The original Clip-Two / Bootstrap look is kept; the three duplicated
copies of the asset bundle (≈45 MB) are collapsed into one `static/` folder.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate                              # initial migrations for accounts and core are included
python manage.py seed_demo                             # optional demo data + demo logins
python manage.py runserver
```

Run the tests with `python manage.py test`. If you later change a model, create a new migration with
`python manage.py makemigrations` before running `migrate`.

| Who      | Login page            | Demo login (from `seed_demo` – demo only!)  |
|----------|-----------------------|----------------------------------------------|
| Patient  | `/hms/login/`         | `patient@example.com` / `Patient@12345`      |
| Doctor   | `/hms/doctor/login/`  | `doctor@example.com` / `Doctor@12345`        |
| Admin    | `/hms/admin/login/`   | `admin` / `Admin@12345`                      |

Landing page: `/`. Django's own admin: `/django-admin/` (create a real admin with
`python manage.py createsuperuser` — it is automatically given the hospital *admin* role).

## Configuration (environment variables)

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`True`/`False`), `DJANGO_ALLOWED_HOSTS`, `DJANGO_TIME_ZONE`
(default `Asia/Kolkata`, as in the PHP code). Database: SQLite by default; set `DB_ENGINE=mysql` plus
`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (and `pip install mysqlclient`) for MySQL.
Password-reset e-mail prints to the console by default; set `EMAIL_BACKEND`/`EMAIL_HOST`/… for SMTP.
For production also run `python manage.py collectstatic` and serve `/static/` (e.g. WhiteNoise or nginx).

## How the PHP code maps to Django

| PHP                                   | Django                                                                 |
|---------------------------------------|------------------------------------------------------------------------|
| `users`, `doctors` (login), `admin`   | one `accounts.User` model with a `role` (patient / doctor / admin)     |
| `doctors` (profile)                   | `core.Doctor` (one-to-one with the user)                               |
| `doctorSpecilization`                 | `core.Specialization`                                                  |
| `tblpatient` / `tblmedicalhistory`    | `core.PatientRecord` / `core.MedicalHistory`                           |
| `appointment`                         | `core.Appointment` (`user_status` / `doctor_status` kept)              |
| `tblcontactus` / `tblpage`            | `core.ContactQuery` / `core.SitePage`                                  |
| `userlog` + `doctorslog`              | `accounts.LoginLog` (with a `role` column)                             |
| `index.php`                           | `core` app → `templates/core/index.html`                               |
| `hms/*.php`                           | `patients` app, URLs under `/hms/`                                     |
| `hms/doctor/*.php`                    | `doctors` app, URLs under `/hms/doctor/`                               |
| `hms/admin/*.php`                     | `adminpanel` app, URLs under `/hms/admin/`                             |
| `include/header|sidebar|footer.php`   | `templates/portal/base.html` + one `_sidebar.html` per role            |

## Deliberate behaviour changes (all security/integrity fixes)

* **Passwords**: PHP used unsalted MD5 (and plain text for the admin). Django uses PBKDF2.
* **No SQL injection**: every query goes through the ORM; output is auto-escaped (no XSS).
* **Forgot password**: the PHP page let anyone who knew a person's name + e-mail set a new password.
  It is replaced by Django's e-mailed one-time link (`/hms/password-reset/`) for all roles.
* **Cancel / delete** actions are POST + CSRF-protected buttons (PHP used plain GET links).
* **Booking**: the fee comes from the doctor record, not from the browser; past dates and
  double-booking the same doctor/time are rejected.
* **Patients can only open their own medical-history file** (the PHP page accepted any `viewid`).
* Deleting a specialization that still has doctors is refused instead of leaving orphaned text.
* Deleting a doctor keeps the patient files they created (the link is simply cleared).
* The PHP `admin/registration.php` (unlinked, broken copy of the patient sign-up) was not ported.

Also fixed after review: a doctor-role login without a doctor profile is signed out with a message instead of
crashing; changing a patient's e-mail also updates the login username and the linked patient files; appointment
times earlier today are rejected; `DJANGO_SECRET_KEY` is required when `DJANGO_DEBUG=False`.

Kept as in the PHP app: doctors can search for, view and edit **any** patient file; a patient's
login is linked to patient files by matching e-mail address. Because e-mail addresses are not verified at
sign-up, anyone who registers with someone else's address can read that person's patient file - add e-mail
verification before using this with real data.

## Importing data from the old MySQL database

There was no `.sql` file in the zip, so column names were inferred from the PHP queries.

```bash
pip install PyMySQL
python manage.py import_legacy --host localhost --user root --password "" --database hms
```

Old MD5 hashes are stored as `legacy_md5$$…` and are **automatically re-hashed with PBKDF2 the next time
each user logs in**. Session logs are not imported. Run it against an empty database and check the
counts it prints. Review the command (`accounts/management/commands/import_legacy.py`) against your real
schema before using it on production data.

## Layout

```
hms_project/   settings, root urls
accounts/      User model, login/logout/register/password reset, LoginLog, legacy-MD5 hasher, import_legacy
core/          shared models, landing page, forms, seed_demo, tests
patients/      patient portal      doctors/   doctor portal      adminpanel/   admin portal
templates/     portal/ (layouts, partials), accounts/, core/, patients/, doctors/, adminpanel/
static/        vendor/ (Bootstrap etc.), portal/ (Clip-Two assets), site/ (landing-page assets)
```
