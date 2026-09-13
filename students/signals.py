"""ST-34: notify administrators when key student data is missing."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Student


@receiver(post_save, sender=Student)
def notify_missing_guardian_phone(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.guardian_phone:
        return
    from notifications.tasks import notify_admins_missing_data
    notify_admins_missing_data.delay(
        instance.id, f'New student {instance.full_name} ({instance.student_id}) has no guardian phone number on file.'
    )
