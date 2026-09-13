"""
Django settings for the Malawi School ERP project.

Development defaults target Windows 10 + SQLite + in-memory Channels layer
(no Redis required to get started). Flip the env vars in `.env` to move
towards a production-like setup (PostgreSQL, Redis, Celery worker, etc).
"""
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# --------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    # Unfold must come before django.contrib.admin
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.import_export',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third-party
    'channels',
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',
    'simple_history',
    'django_filters',
    'axes',

    # Local apps
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

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    # Must be the last middleware (AC-25/26: lockout after failed logins).
    'axes.middleware.AxesMiddleware',
]

AUTHENTICATION_BACKENDS = [
    # AxesBackend must be first so it can block a login before ModelBackend runs.
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'config.urls'

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
                'accounts.context_processors.role_menu',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# --------------------------------------------------------------------------
# Database - SQLite for development. Swap to Postgres via env vars for prod.
# --------------------------------------------------------------------------
if config('DB_ENGINE', default='sqlite') == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='malawi_school_erp'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --------------------------------------------------------------------------
# Custom user model with roles
# --------------------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

# AC: session security - 30 min inactivity timeout, HttpOnly always,
# Secure cookies once served over HTTPS in production.
SESSION_COOKIE_AGE = 60 * 30
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # AC-13: minimum length 8, mix of letters and numbers.
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'accounts.validators.LetterAndNumberValidator'},
    # AC-15: prevent reuse of the last 3 passwords.
    {'NAME': 'accounts.validators.PasswordHistoryValidator', 'OPTIONS': {'history_size': 3}},
]

# AC-02: allow Students/Parents to self-register (Admin creates Teacher/Staff accounts).
ENABLE_SELF_REGISTRATION = config('ENABLE_SELF_REGISTRATION', default=True, cast=bool)

# AC-14: password reset links expire after 24 hours (Django default is 3 days).
PASSWORD_RESET_TIMEOUT = config('PASSWORD_RESET_TIMEOUT', default=60 * 60 * 24, cast=int)

# --------------------------------------------------------------------------
# Attendance (AT-04/AT-16/AT-19): edit windows and alert threshold.
# --------------------------------------------------------------------------
ATTENDANCE_EDIT_WINDOW_HOURS = config('ATTENDANCE_EDIT_WINDOW_HOURS', default=24, cast=int)
ATTENDANCE_PAST_LIMIT_DAYS = config('ATTENDANCE_PAST_LIMIT_DAYS', default=7, cast=int)
ATTENDANCE_LOW_THRESHOLD = config('ATTENDANCE_LOW_THRESHOLD', default=80, cast=int)

# --------------------------------------------------------------------------
# Payment gateways (FP-17/26): pluggable, PayChangu enabled by default.
# Add a new provider by writing a payments.gateways.<name>.<Name>Gateway
# class implementing PaymentGateway, registering it in
# payments/registry.py, and adding its own block here - no other code
# needs to change.
# --------------------------------------------------------------------------
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
# and provide the throttling asked for in the non-functional requirements.
# --------------------------------------------------------------------------
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 0.25  # 15 minutes
AXES_LOCKOUT_PARAMETERS = [['username', 'ip_address']]
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False

# --------------------------------------------------------------------------
# Internationalization
# --------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Blantyre'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static & media files
# --------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------------------
# Crispy forms
# --------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# --------------------------------------------------------------------------
# Channels
# In-memory layer is enough for a single-process dev server: no Redis
# needed to get started. Set CHANNEL_LAYER_BACKEND=redis (and REDIS_URL)
# once you need multi-process / multi-worker fan-out (e.g. behind Daphne
# with several instances, or once Celery workers need to push events too).
# --------------------------------------------------------------------------
if config('CHANNEL_LAYER_BACKEND', default='memory') == 'redis':
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [config('REDIS_URL', default='redis://127.0.0.1:6379/0')],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# --------------------------------------------------------------------------
# Celery
# Defaults to "eager" mode for development on Windows: tasks run
# synchronously in-process, so no broker/worker is required at all.
# Set CELERY_ALWAYS_EAGER=False and provide a REDIS_URL to run a real
# `celery -A config worker --pool=solo` worker.
# --------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = config('CELERY_ALWAYS_EAGER', default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# --------------------------------------------------------------------------
# Import/Export
# --------------------------------------------------------------------------
IMPORT_EXPORT_USE_TRANSACTIONS = True

# --------------------------------------------------------------------------
# django-unfold admin theme
# --------------------------------------------------------------------------
UNFOLD = {
    'SITE_TITLE': 'Malawi School ERP',
    'SITE_HEADER': 'Malawi School ERP Admin',
    'SITE_SYMBOL': 'school',
    'SHOW_HISTORY': True,
}

# --------------------------------------------------------------------------
# Email (console backend for dev; swap to SMTP/Africa's Talking in prod)
# --------------------------------------------------------------------------
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='no-reply@mzuzusec.mw')

# SMS gateway placeholders (Africa's Talking / Twilio) - used by notifications.tasks
AFRICASTALKING_USERNAME = config('AFRICASTALKING_USERNAME', default='sandbox')
AFRICASTALKING_API_KEY = config('AFRICASTALKING_API_KEY', default='')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
