"""
Django settings for the Malawi School ERP project — PRODUCTION ONLY.

Assumptions this file makes:
  - PostgreSQL is the database (no sqlite fallback exists).
  - Redis is required for both Channels (WebSocket fan-out) and Celery.
  - The app sits behind Nginx terminating TLS, forwarding HTTP to Daphne.
  - A populated .env file exists next to manage.py.
  - Any required variable that is missing raises at import time — this is
    deliberate. A production app that silently falls back to a dev default
    is worse than one that refuses to boot.
"""
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================================================
# CORE — all REQUIRED (no insecure defaults)
# ==========================================================================
# SECRET_KEY has no default on purpose: if this is missing, Django must
# refuse to start rather than fall back to a well-known insecure string,
# which would make session cookies and CSRF tokens forgeable.
SECRET_KEY = config('SECRET_KEY')

# Hardcoded False — never rely on .env to disable debug in production.
# DEBUG=True in prod leaks tracebacks, settings, source snippets, and
# SQL to any visitor who triggers an exception.
DEBUG = False

# Required, no default. Django rejects requests whose Host header isn't
# listed here; this also mitigates Host-header injection attacks.
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# ==========================================================================
# APPLICATIONS
# ==========================================================================
INSTALLED_APPS = [
    # ---- Unfold admin theme (must be listed before django.contrib.admin) ----
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.import_export',

    # ---- Django core ----
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',      # naturaltime, intcomma, etc.

    # ---- Third-party ----
    'channels',                     # ASGI + WebSocket support
    'crispy_forms',                 # form rendering
    'crispy_bootstrap5',            # Bootstrap 5 template pack
    'import_export',                # CSV/Excel import/export on admin + views
    'simple_history',               # per-model audit trail
    'django_filters',               # querystring-based list filtering
    'axes',                         # login rate-limiting / lockout
    'djmoney',                      # MoneyField (MWK/USD/GBP/ZAR)
    'mptt',                         # hierarchical trees (syllabus topics)
    'django_tables2',               # server-side rendered tables

    # ---- Local apps ----
    'accounts',
    'students',
    'teachers',
    'staff',
    'attendance',
    'grades',
    'fees',
    'timetable',
    'reports',
    'notifications',
    'syllabus',
    'payments',
]

# ==========================================================================
# MIDDLEWARE
# ==========================================================================
MIDDLEWARE = [
    # SecurityMiddleware must come first so its headers apply to every
    # response and HTTPS redirects happen before anything else touches
    # the request.
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # simple_history uses the request to stamp history rows with the actor.
    'simple_history.middleware.HistoryRequestMiddleware',
    # AxesMiddleware MUST be last: it inspects the response after the view
    # has run so it can count failed login attempts correctly (AC-25/26).
    'axes.middleware.AxesMiddleware',
]

# AxesBackend first so it can short-circuit a locked-out account before
# ModelBackend even tries to verify the password.
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'config.urls'

# ==========================================================================
# TEMPLATES
# ==========================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.role_menu',   # role-based sidebar
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ==========================================================================
# DATABASE — PostgreSQL only. No sqlite fallback exists on purpose: a
# missing/misspelled DB_ENGINE must not silently put production data
# into a local file.
# ==========================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='5432'),
        # Reuse DB connections for 60s to cut per-request overhead under
        # Daphne; Django closes them cleanly on request teardown.
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            # Fail fast if the DB is unreachable instead of hanging a worker.
            'connect_timeout': 10,
        },
    }
}

# ==========================================================================
# AUTH — custom user model + redirects
# ==========================================================================
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

# ==========================================================================
# SESSIONS & COOKIES — full production hardening
# ==========================================================================
# 30-minute inactivity timeout (SESSION_SAVE_EVERY_REQUEST slides it forward).
SESSION_COOKIE_AGE = 60 * 30
SESSION_SAVE_EVERY_REQUEST = True

# HttpOnly: JS cannot read the session cookie (blocks XSS session theft).
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Secure: cookie is only sent over HTTPS. Hardcoded True — never let a
# missing env var downgrade this on a live site.
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Same for the CSRF cookie.
CSRF_COOKIE_SECURE = True
# HttpOnly stays False on the CSRF cookie: some front-end code may need
# to read the token from JS (e.g. for AJAX). The cookie is still
# origin-scoped and validated server-side.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# Scoping the CSRF cookie to the exact production domain avoids the
# subtle "cookie set on one host, POST sent to another" bug that can
# manifest as intermittent CSRF 403s.
CSRF_COOKIE_DOMAIN = config('CSRF_COOKIE_DOMAIN', default=None) or None

# Origins allowed to submit CSRF-protected POSTs (Django 4.0+ required
# this to be explicit; the scheme must be included). REQUIRED — no
# default, because an empty list breaks every login on HTTPS.
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=Csv())

# ==========================================================================
# HTTPS / PROXY — this is the real fix for "CSRF verification failed. 403"
#
# Nginx terminates TLS and forwards plain HTTP to Daphne, adding
# X-Forwarded-Proto: https. Without SECURE_PROXY_SSL_HEADER, Django
# sees the request as http, request.is_secure() is False, and the CSRF
# origin check fails — regardless of CSRF_TRUSTED_ORIGINS.
# ==========================================================================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Nginx already redirects HTTP→HTTPS at the edge; letting Django also
# redirect here would double-handle it and confuse clients behind the
# proxy, so leave False.
SECURE_SSL_REDIRECT = False

# HSTS: tell browsers to only ever use HTTPS for this domain for a year,
# including subdomains, and allow preloading into browser HSTS lists.
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Don't let browsers sniff a different content type than declared
# (blocks a class of MIME-confusion XSS).
SECURE_CONTENT_TYPE_NOSNIFF = True

# Only send the Referer header within the same origin.
SECURE_REFERRER_POLICY = 'same-origin'

# Isolate the browsing context from cross-origin openers (tab-napping,
# some XS-Leaks).
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Disallow the site being framed (clickjacking).
X_FRAME_OPTIONS = 'DENY'

# ==========================================================================
# PASSWORD POLICY (AC-13/14/15)
# ==========================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # Minimum length 8, mix of letters and numbers enforced below.
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'accounts.validators.LetterAndNumberValidator'},
    # Prevent reuse of the last 3 passwords (custom validator).
    {'NAME': 'accounts.validators.PasswordHistoryValidator',
     'OPTIONS': {'history_size': 3}},
]

# Default OFF in production: student/parent self-registration should be
# a deliberate opt-in, not an accidental opening on a live school system.
ENABLE_SELF_REGISTRATION = config('ENABLE_SELF_REGISTRATION', default=False, cast=bool)

# Password-reset links expire after 24 hours (Django default is 3 days).
PASSWORD_RESET_TIMEOUT = config('PASSWORD_RESET_TIMEOUT', default=60 * 60 * 24, cast=int)

# ==========================================================================
# ATTENDANCE (AT-04/16/19)
# ==========================================================================
ATTENDANCE_EDIT_WINDOW_HOURS = config('ATTENDANCE_EDIT_WINDOW_HOURS', default=24, cast=int)
ATTENDANCE_PAST_LIMIT_DAYS = config('ATTENDANCE_PAST_LIMIT_DAYS', default=7, cast=int)
ATTENDANCE_LOW_THRESHOLD = config('ATTENDANCE_LOW_THRESHOLD', default=80, cast=int)

# ==========================================================================
# django-money — multi-currency support, default Malawian Kwacha.
#
# Fee/payment monetary fields use MoneyField instead of DecimalField, so
# billing a foreign-currency bursary (USD/GBP/ZAR) is a value choice,
# not a schema migration. Do NOT change CURRENCY_CHOICES lightly: it is
# referenced by migrations and existing MoneyField rows.
# ==========================================================================
DEFAULT_CURRENCY = 'MWK'
CURRENCIES = ('MWK', 'USD', 'GBP', 'ZAR')
CURRENCY_CHOICES = [
    ('MWK', 'Malawian Kwacha'),
    ('USD', 'US Dollar'),
    ('GBP', 'British Pound'),
    ('ZAR', 'South African Rand'),
]

# ==========================================================================
# django-tables2 — default to Bootstrap 5 so tables match the rest of
# the UI without needing template_name on every Table subclass.
# ==========================================================================
DJANGO_TABLES2_TEMPLATE = 'django_tables2/bootstrap5.html'

# ==========================================================================
# PAYMENT GATEWAYS (FP-17/26) — pluggable.
#
# To add a new provider:
#   1. Write payments/gateways/<name>.py implementing PaymentGateway.
#   2. Register it in payments/registry.py.
#   3. Add a config block below.
# Nothing in fees/ or the parent portal needs to change.
# ==========================================================================
DEFAULT_PAYMENT_GATEWAY = config('DEFAULT_PAYMENT_GATEWAY', default='paychangu')
PAYMENT_GATEWAYS = {
    'paychangu': {
        'enabled': config('PAYCHANGU_ENABLED', default=True, cast=bool),
        'base_url': config('PAYCHANGU_BASE_URL', default='https://api.paychangu.com'),
        'secret_key': config('PAYCHANGU_SECRET_KEY', default=''),
        'webhook_secret': config('PAYCHANGU_WEBHOOK_SECRET', default=''),
        'timeout': config('PAYCHANGU_TIMEOUT', default=15, cast=int),
    },
}

# ==========================================================================
# django-axes — login throttling / lockout (AC-25/26, NFR rate-limiting)
# ==========================================================================
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 0.25                    # 15 minutes
AXES_LOCKOUT_PARAMETERS = [['username', 'ip_address']]
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False

# ==========================================================================
# INTERNATIONALIZATION
# ==========================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Blantyre'
USE_I18N = True
USE_TZ = True

# ==========================================================================
# STATIC & MEDIA
# Nginx serves these directly (see the nginx conf); collectstatic writes
# to STATIC_ROOT and the deploy script keeps that directory in sync.
# Leading slashes on URLs so relative page paths resolve correctly.
# ==========================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================================================
# CRISPY FORMS
# ==========================================================================
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ==========================================================================
# CHANNELS — Redis only.
#
# Daphne (WebSocket server) and Celery workers run as separate OS
# processes, so the in-memory layer cannot fan messages across them.
# Redis is required, not optional, in this file.
# ==========================================================================
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [config('REDIS_URL')],
        },
    },
}

# ==========================================================================
# CELERY — real broker, no eager mode.
#
# CELERY_TASK_ALWAYS_EAGER was useful in dev (tasks ran inline, no worker
# needed). In production it would block request/response cycles on slow
# external calls (SMS, PayChangu API), which is exactly what we want to
# avoid. Redis is the broker AND result backend.
# ==========================================================================
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_BROKER_URL = config('REDIS_URL')
CELERY_RESULT_BACKEND = config('REDIS_URL')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# ack a task only after it completes — a mid-task worker crash re-queues
# the job instead of silently dropping it.
CELERY_TASK_ACKS_LATE = True
# Give one task to one worker at a time; smoother for long SMS/HTTP tasks.
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# ==========================================================================
# IMPORT / EXPORT
# ==========================================================================
IMPORT_EXPORT_USE_TRANSACTIONS = True

# ==========================================================================
# DJANGO-UNFOLD ADMIN THEME
# ==========================================================================
UNFOLD = {
    'SITE_TITLE': 'Malawi School ERP',
    'SITE_HEADER': 'Malawi School ERP Admin',
    'SITE_SYMBOL': 'school',
    'SHOW_HISTORY': True,
}

# ==========================================================================
# EMAIL — SMTP (no console fallback in production).
#
# If EMAIL_HOST is left blank, password-reset emails will silently fail
# and be logged. Either fill in the SMTP vars in .env or temporarily set
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend — in
# which case emails land in `journalctl -u daphne-malawi-erp`.
# ==========================================================================
EMAIL_BACKEND = config('EMAIL_BACKEND',
                       default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL',
                            default='no-reply@school.pritechmw.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ==========================================================================
# SMS — Africa's Talking (used by notifications.tasks)
# ==========================================================================
AFRICASTALKING_USERNAME = config('AFRICASTALKING_USERNAME', default='')
AFRICASTALKING_API_KEY = config('AFRICASTALKING_API_KEY', default='')

# ==========================================================================
# LOGGING — console (captured by systemd/journald) + rotating file.
#
# The file log lets you grep long after journald has rotated; the console
# log is what `journalctl -u daphne-malawi-erp` shows. Both are useful.
# ==========================================================================
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'django.log'),
            'maxBytes': 10 * 1024 * 1024,       # 10 MB per file
            'backupCount': 5,                   # keep django.log.1 … .5
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        # Request errors (500s, CSRF failures) go to both sinks at ERROR.
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
