"""Custom password validators referenced from settings.AUTH_PASSWORD_VALIDATORS."""
import re
import hashlib

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class LetterAndNumberValidator:
    """AC-13: passwords must mix letters and numbers."""

    def validate(self, password, user=None):
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            raise ValidationError(
                _('Your password must contain both letters and numbers.'),
                code='password_no_letter_number',
            )

    def get_help_text(self):
        return _('Your password must contain both letters and numbers.')


class PasswordHistoryValidator:
    """AC-15: prevent reuse of the user's last N passwords."""

    def __init__(self, history_size=3):
        self.history_size = history_size

    def validate(self, password, user=None):
        if not user or not user.pk:
            return
        from .models import PasswordHistory
        from django.contrib.auth.hashers import check_password

        recent = PasswordHistory.objects.filter(user=user).order_by('-created_at')[:self.history_size]
        for entry in recent:
            if check_password(password, entry.password_hash):
                raise ValidationError(
                    _('You cannot reuse one of your last %(count)d passwords.'),
                    code='password_reused',
                    params={'count': self.history_size},
                )

    def get_help_text(self):
        return _('Your password cannot match any of your last %(count)d passwords.') % {'count': self.history_size}
