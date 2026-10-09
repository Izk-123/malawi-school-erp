"""Inclusion tag for the HR dashboard TCM widget.

Self-contained: it does its own permission check and its own queries, so
it can be dropped onto any dashboard template with ``{% tcm_status_widget %}``
without any view or context-processor wiring.

Query budget: two round-trips total — one aggregate for the counts, one
for the "needs attention" list (capped at ``ATTENTION_LIMIT``).
"""
import datetime

from django import template
from django.db.models import Count, Q
from django.utils import timezone

from ..models import Teacher


register = template.Library()


# How many teachers to list in the "needs attention" table. Anything
# beyond this is what the admin TCM filter is for.
ATTENTION_LIMIT = 8

# The horizon used for the "expiring soon" bucket. Matches the widest
# reminder window in teachers.tasks so the widget and the sweep agree on
# what counts as urgent.
EXPIRY_HORIZON_DAYS = 60

# Roles/groups allowed to see the widget.
_VIEWER_GROUPS = ('hr_officer', 'head_teacher')


@register.inclusion_tag('teachers/widgets/tcm_status.html', takes_context=True)
def tcm_status_widget(context):
    request = context.get('request')
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'visible': False}

    if not _can_view(user):
        return {'visible': False}

    today = timezone.localdate()
    horizon = today + datetime.timedelta(days=EXPIRY_HORIZON_DAYS)

    active = Teacher.objects.filter(status=Teacher.Status.ACTIVE)

    # -- Counts (one aggregate query) --------------------------------------
    renewable = Q(tcm_status__in=[
        Teacher.TCMStatus.REGISTERED, Teacher.TCMStatus.PROVISIONAL,
    ])

    counts = active.aggregate(
        total=Count('pk'),
        valid=Count('pk', filter=(
            renewable
            & Q(tcm_license_expiry__gt=horizon)
        )),
        expiring_soon=Count('pk', filter=(
            renewable
            & Q(tcm_license_expiry__gte=today)
            & Q(tcm_license_expiry__lte=horizon)
        )),
        expired=Count('pk', filter=(
            Q(tcm_status=Teacher.TCMStatus.EXPIRED)
            | (renewable & Q(tcm_license_expiry__lt=today))
        )),
        not_registered=Count('pk', filter=Q(
            tcm_status=Teacher.TCMStatus.NOT_REGISTERED,
        )),
        suspended=Count('pk', filter=Q(
            tcm_status=Teacher.TCMStatus.SUSPENDED,
        )),
        # Data-entry gap: marked as registered but no expiry on file, so
        # the daily sweep can't see them.
        missing_expiry=Count('pk', filter=(
            renewable & Q(tcm_license_expiry__isnull=True)
        )),
    )

    blocked = counts['expired'] + counts['not_registered'] + counts['suspended']

    # -- Attention list (one query, capped) --------------------------------
    # Priority: expired / suspended first, then soonest-to-expire among
    # the renewable set, then the unregistered / missing-expiry tail.
    attention_qs = (
        active
        .filter(
            Q(tcm_status__in=[
                Teacher.TCMStatus.EXPIRED,
                Teacher.TCMStatus.SUSPENDED,
                Teacher.TCMStatus.NOT_REGISTERED,
            ])
            | Q(tcm_status__in=[
                Teacher.TCMStatus.REGISTERED,
                Teacher.TCMStatus.PROVISIONAL,
              ], tcm_license_expiry__lte=horizon)
            | Q(tcm_status__in=[
                Teacher.TCMStatus.REGISTERED,
                Teacher.TCMStatus.PROVISIONAL,
              ], tcm_license_expiry__isnull=True)
        )
        .only(
            'id', 'teacher_id', 'full_name', 'tcm_status',
            'tcm_license_expiry', 'subject',
        )
        .order_by('tcm_license_expiry', 'full_name')[:ATTENTION_LIMIT]
    )

    attention = [_row(t, today) for t in attention_qs]

    return {
        'visible': True,
        'counts': counts,
        'blocked': blocked,
        'attention': attention,
        'horizon_days': EXPIRY_HORIZON_DAYS,
        'attention_limit': ATTENTION_LIMIT,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _can_view(user):
    if user.is_superuser:
        return True
    if getattr(user, 'role', None) == 'admin':
        return True
    return user.groups.filter(name__in=_VIEWER_GROUPS).exists()


def _row(teacher, today):
    """Shape one teacher for the widget's attention table."""
    status = teacher.tcm_status
    days = None
    if teacher.tcm_license_expiry:
        days = (teacher.tcm_license_expiry - today).days

    # Traffic-light: red = can't teach, amber = act now, grey = record gap.
    if status in (Teacher.TCMStatus.EXPIRED, Teacher.TCMStatus.SUSPENDED):
        tone = 'danger'
        note = teacher.get_tcm_status_display()
    elif status == Teacher.TCMStatus.NOT_REGISTERED:
        tone = 'muted'
        note = 'Not registered'
    elif days is None:
        tone = 'muted'
        note = 'No expiry on file'
    elif days < 0:
        tone = 'danger'
        note = f'Expired {abs(days)} day(s) ago'
    elif days == 0:
        tone = 'warning'
        note = 'Expires today'
    elif days <= 30:
        tone = 'warning'
        note = f'Expires in {days} day(s)'
    else:
        tone = 'info'
        note = f'Expires in {days} day(s)'

    return {
        'teacher': teacher,
        'tone': tone,
        'note': note,
    }