"""Run the TCM expiry sweep from the shell.

Useful when:
  - you're developing on Windows and Celery beat isn't running
  - you want to replay a sweep after fixing a delivery problem
  - a cron-driven deployment runs the command directly instead of beat

The task is idempotent, so running this twice in a day is a no-op the
second time (the audit check in ``_reminder_already_sent`` filters out
already-notified (teacher, window) pairs).
"""
from django.core.management.base import BaseCommand

from teachers.tasks import send_tcm_expiry_reminders


class Command(BaseCommand):
    help = (
        'Send TCM license expiry reminders (60/30/7-day windows) and '
        'email the day\'s HR digest. Safe to run repeatedly.'
    )

    def handle(self, *args, **options):
        result = send_tcm_expiry_reminders()
        count = result.get('reminders_sent', 0)
        self.stdout.write(self.style.SUCCESS(
            f'TCM sweep complete — {count} reminder(s) sent.'
        ))