from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        FEE_DUE = 'fee_due', 'Fee Due'
        LOW_ATTENDANCE = 'low_attendance', 'Low Attendance'
        GRADE_PUBLISHED = 'grade_published', 'Grade Published'
        ANNOUNCEMENT = 'announcement', 'Announcement'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient} - {self.message[:40]}'
