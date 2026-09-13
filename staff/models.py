from django.conf import settings
from django.db import models


class StaffMember(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='staff_profile',
    )
    staff_id = models.CharField(max_length=10, unique=True)
    full_name = models.CharField(max_length=150)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Staff Member'

    def __str__(self):
        return f'{self.full_name} - {self.position}'
