"""
Django settings for the Malawi School ERP project — PRODUCTION.

This file assumes:
  - PostgreSQL database (required, no sqlite fallback)
  - Redis for Channels + Celery broker (required)
  - Behind Nginx terminating TLS, forwarding to Daphne over HTTP
  - .env is present and populated; missing required vars raise an error
"""
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Core — all REQUIRED, no insecure defaults
# --------------------------------------------------------------------------
SECRET_KEY = config('SECRET_KEY')           # raises if missing
DEBUG = False                               # hardcoded — never True in prod
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# --------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------
INSTALLED_APPS = [
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

    'channels',
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',
    'simple_history',
    'django_filters',
    'axes',
    'djmoney',
    'mptt',
    'django_tables2',

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
    'axes.middleware.AxesMiddleware',
]

AUTHENTICATION_BACKENDS = [
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
# Database — PostgreSQL only
# --------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# --------------------------------------------------------------------------
# Custom user model + auth redirects
# --------------------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

# --------------------------------------------------------------------------
# Sessions & cookies — full production hardening
# --------------------------------------------------------------------------
SESSION_COOKIE_AGE = 60 * 30
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False         # must stay False so JS can read it if needed
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_DOMAIN = config('CSRF_COOKIE_DOMAIN', default=None) or None
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=Csv())

# --------------------------------------------------------------------------
# HTTPS / proxy — THIS is what fixes the "CSRF verification failed" 403
# behind Nginx: Nginx terminates TLS and forwards HTTP to Daphne, but
# sends X-Forwarded-Proto: https. Without this setting Django thinks the
# request is plain HTTP, request.is_secure() is False, and CSRF fails.
# --------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_SSL_REDIRECT = False          # Nginx already redirects HTTP→HTTPS; leave False here
SECURE_HSTS_SECONDS = 31536000       # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# --------------------------------------------------------------------------
# Password policy
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'accounts.validators.LetterAndNumberValidator'},
    {'NAME': 'accounts.validators.PasswordHistoryValidator', 'OPTIONS': {'history_size': 3}},
]

ENABLE_SELF_REGISTRATION = config('ENABLE_SELF_REGISTRATION', default=False, cast=bool)
PASSWORD_RESET_TIMEOUT = config('PASSWORD_RESET_TIMEOUT', default=60 * 60 * 24, cast=int)

# --------------------------------------------------------------------------
# Attendance
# --------------------------------------------------------------------------
ATTENDANCE_EDIT_WINDOW_HOURS = config('ATTENDANCE_EDIT_WINDOW_HOURS', default=24, cast=int)
ATTENDANCE_PAST_LIMIT_DAYS = config('ATTENDANCE_PAST_LIMIT_DAYS', default=7, cast=int)
ATTENDANCE_LOW_THRESHOLD = config('ATTENDANCE_LOW_THRESHOLD', default=80, cast=int)

# --------------------------------------------------------------------------
<<<<<<< HEAD
# django-money: multi-currency support, defaulting to Malawian Kwacha.
# Fee/payment monetary fields use MoneyField instead of DecimalField so a
# school billing in USD (e.g. international MSCE candidates) or accepting
# a foreign-currency bursary is a currency choice, not a schema change.
# --------------------------------------------------------------------------
DEFAULT_CURRENCY = 'MWK'
CURRENCIES = ('MWK', 'USD', 'GBP', 'ZAR')
CURRENCY_CHOICES = [('MWK', 'Malawian Kwacha'), ('USD', 'US Dollar'), ('GBP', 'British Pound'), ('ZAR', 'South African Rand')]

# django-tables2: default to the Bootstrap 5 template so tables match the
# rest of the UI without specifying template_name on every Table class.
DJANGO_TABLES2_TEMPLATE = 'django_tables2/bootstrap5.html'

# --------------------------------------------------------------------------
# Payment gateways (FP-17/26): pluggable, PayChangu enabled by default.
# Add a new provider by writing a payments.gateways.<name>.<Name>Gateway
# class implementing PaymentGateway, registering it in
# payments/registry.py, and adding its own block here - no other code
# needs to change.
=======
# Payment gateways
>>>>>>> 25f846ebbdae8b235709d68c4e6c205b47256c0c
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

# --------------------------------------------------------------------------
# django-axes (login throttling / lockout)
# --------------------------------------------------------------------------
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 0.25
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
# Static & media
# --------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------------------
# Crispy forms
# --------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# --------------------------------------------------------------------------
# Channels — Redis only (Daphne and Celery run in separate processes)
# --------------------------------------------------------------------------
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [config('REDIS_URL')],
        },
    },
}

# --------------------------------------------------------------------------
# Celery — real broker, no eager mode
# --------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_BROKER_URL = config('REDIS_URL')
CELERY_RESULT_BACKEND = config('REDIS_URL')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

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
# Email — SMTP (no console fallback)
# --------------------------------------------------------------------------
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='no-reply@school.pritechmw.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

AFRICASTALKING_USERNAME = config('AFRICASTALKING_USERNAME', default='')
AFRICASTALKING_API_KEY = config('AFRICASTALKING_API_KEY', default='')

# --------------------------------------------------------------------------
# Logging — file + console (Nginx/systemd capture console)
# --------------------------------------------------------------------------
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
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
