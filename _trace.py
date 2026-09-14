import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
from django.apps import apps
from django.conf import settings

for entry in settings.INSTALLED_APPS:
    print(f'Trying: {entry}')
    try:
        from django.apps.config import AppConfig
        AppConfig.create(entry)
        print(f'  OK: {entry}')
    except Exception as e:
        print(f'  FAIL: {entry} -> {type(e).__name__}: {e}')
        raise