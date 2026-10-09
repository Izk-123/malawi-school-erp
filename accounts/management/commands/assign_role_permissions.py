"""
AC-16/17: create one Django Group per role and grant it the model
permissions appropriate for that role. Users are auto-added to their role's
group by the `sync_role_group` signal in accounts/signals.py; this command
just needs to (re)run whenever permissions should be recalculated, e.g.
after adding a new app/model.

Governance ("Who Should Create Accounts?"): this command ALSO creates the
three account-creation groups — `registry_clerk`, `hr_officer`,
`head_teacher` — which grant the account-creation permissions declared in
`User.Meta.permissions`. A user's role group grants portal access; one of
these creator groups grants authority to create accounts on top. Only a
Head Teacher (or superuser) should be in `head_teacher`; the other two are
delegated by the Head Teacher via the admin.

    python manage.py assign_role_permissions
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from accounts.models import User
from students.models import Student
from teachers.models import Teacher, ClassAssignment
from staff.models import (
    StaffMember, LeaveRequest, StaffAttendance, StaffAnnouncement, StaffTicket, Payslip,
    Book, BookLoan, VisitorLog, GatePass, PatrolLog, MedicalRecord, SickBayVisit, MedicationStock,
)
from attendance.models import AttendanceRecord
from grades.models import GradeRecord
from fees.models import FeeStructure, FeeTransaction, Discount
from payments.models import PaymentTransaction
from timetable.models import TimetablePeriod
from notifications.models import Notification
from syllabus.models import (
    ExamSession, Subject, Paper, SyllabusTopic, AssessmentObjective,
    GradeDescriptor, ManebGradeScale, TopicCoverage,
)


# role -> {model: [actions]}, actions subset of add/change/delete/view
ROLE_PERMISSIONS = {
    User.Role.ADMIN: {
        Student: ['add', 'change', 'delete', 'view'],
        Teacher: ['add', 'change', 'delete', 'view'],
        ClassAssignment: ['add', 'change', 'delete', 'view'],
        StaffMember: ['add', 'change', 'delete', 'view'],
        AttendanceRecord: ['add', 'change', 'delete', 'view'],
        GradeRecord: ['add', 'change', 'delete', 'view'],
        FeeStructure: ['add', 'change', 'delete', 'view'],
        FeeTransaction: ['add', 'change', 'delete', 'view'],
        Discount: ['add', 'change', 'delete', 'view'],
        PaymentTransaction: ['view'],
        TimetablePeriod: ['add', 'change', 'delete', 'view'],
        Notification: ['view'],
        # SY: only admins may create/edit/archive the syllabus structure.
        ExamSession: ['add', 'change', 'delete', 'view'],
        Subject: ['add', 'change', 'delete', 'view'],
        Paper: ['add', 'change', 'delete', 'view'],
        SyllabusTopic: ['add', 'change', 'delete', 'view'],
        AssessmentObjective: ['add', 'change', 'delete', 'view'],
        GradeDescriptor: ['add', 'change', 'delete', 'view'],
        ManebGradeScale: ['add', 'change', 'delete', 'view'],
        TopicCoverage: ['view'],
        LeaveRequest: ['add', 'change', 'delete', 'view'],
        StaffAttendance: ['add', 'change', 'delete', 'view'],
        StaffAnnouncement: ['add', 'change', 'delete', 'view'],
        StaffTicket: ['add', 'change', 'delete', 'view'],
        Payslip: ['add', 'change', 'delete', 'view'],
        Book: ['add', 'change', 'delete', 'view'],
        BookLoan: ['add', 'change', 'delete', 'view'],
        VisitorLog: ['add', 'change', 'delete', 'view'],
        GatePass: ['add', 'change', 'delete', 'view'],
        PatrolLog: ['add', 'change', 'delete', 'view'],
        MedicalRecord: ['add', 'change', 'delete', 'view'],
        SickBayVisit: ['add', 'change', 'delete', 'view'],
        MedicationStock: ['add', 'change', 'delete', 'view'],
    },
    User.Role.TEACHER: {
        Student: ['view'],
        AttendanceRecord: ['add', 'change', 'view'],
        GradeRecord: ['add', 'change', 'view'],
        TimetablePeriod: ['view'],
        Notification: ['view'],
        # SY: read-only on syllabus structure; can mark their own coverage.
        Subject: ['view'],
        Paper: ['view'],
        SyllabusTopic: ['view'],
        AssessmentObjective: ['view'],
        GradeDescriptor: ['view'],
        ManebGradeScale: ['view'],
        TopicCoverage: ['add', 'change', 'view'],
    },
    User.Role.STUDENT: {
        GradeRecord: ['view'],
        FeeTransaction: ['view'],
        TimetablePeriod: ['view'],
        Notification: ['view'],
        Subject: ['view'],
        Paper: ['view'],
        SyllabusTopic: ['view'],
        GradeDescriptor: ['view'],
        ManebGradeScale: ['view'],
    },
    User.Role.PARENT: {
        Student: ['view'],
        GradeRecord: ['view'],
        FeeTransaction: ['view'],
        PaymentTransaction: ['add', 'view'],
        AttendanceRecord: ['view'],
        Notification: ['view'],
        Subject: ['view'],
        SyllabusTopic: ['view'],
        ManebGradeScale: ['view'],
    },
    User.Role.STAFF: {
        StaffMember: ['change', 'view'],
        LeaveRequest: ['add', 'change', 'view'],
        StaffAttendance: ['add', 'change', 'view'],
        StaffAnnouncement: ['add', 'view'],
        StaffTicket: ['add', 'change', 'view'],
        Payslip: ['view'],
        Book: ['add', 'change', 'view'],
        BookLoan: ['add', 'change', 'view'],
        VisitorLog: ['add', 'change', 'view'],
        GatePass: ['add', 'change', 'view'],
        PatrolLog: ['add', 'view'],
        MedicalRecord: ['add', 'change', 'view'],
        SickBayVisit: ['add', 'view'],
        MedicationStock: ['add', 'change', 'view'],
        TimetablePeriod: ['view'],
        Notification: ['view'],
        Subject: ['view'],
        SyllabusTopic: ['view'],
    },
}


# ---------------------------------------------------------------------------
# Account-creation groups (governance doc §2)
#
# The three creators a typical Malawi secondary school needs. Expressed as
# Groups holding the User-model permissions declared in
# accounts/models.User.Meta.permissions. `services.can_create_account_for`
# is the single enforcement point — it checks both the master
# `create_account` gate and the purpose-specific permission (plus the
# high-privilege gate for admin/bursar/auditor).
# ---------------------------------------------------------------------------
ACCOUNT_CREATION_GROUPS = {
    # Registry Clerk / Secretary: students + parents.
    'registry_clerk': [
        'create_account',
        'create_student_account',
        'create_parent_account',
    ],
    # HR Officer / Deputy Head (Admin): teachers + non-teaching staff.
    'hr_officer': [
        'create_account',
        'create_teacher_account',
        'create_staff_account',
    ],
    # Head Teacher: everything, including high-privilege and approval.
    'head_teacher': [
        'create_account',
        'create_student_account',
        'create_parent_account',
        'create_teacher_account',
        'create_staff_account',
        'create_admin_account',
        'create_bursar_account',
        'create_auditor_account',
        'create_high_privilege_account',
        'approve_account_creation',
    ],
}


def _grant_user_perms(group, codenames):
    """Attach User-model permissions by codename to a Group.

    Permissions declared in `User.Meta.permissions` are created by Django
    during `migrate`; the `get_or_create` here is a belt-and-braces in case
    the command runs before a migration that adds a new codename."""
    ct = ContentType.objects.get_for_model(User)
    perms = []
    for code in codenames:
        short = code.split('.', 1)[1] if '.' in code else code
        perm, _ = Permission.objects.get_or_create(
            codename=short,
            content_type=ct,
            defaults={'name': short.replace('_', ' ').title()},
        )
        perms.append(perm)
    group.permissions.add(*perms)
    return perms


class Command(BaseCommand):
    help = 'Sync Django Groups/permissions to match each role (AC-16/17) and the account-creation matrix.'

    def handle(self, *args, **options):
        # ------------------------------------------------------------------
        # 1. Role groups: portal-level model permissions.
        # ------------------------------------------------------------------
        for role, model_perms in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role)
            perms = []
            for model, actions in model_perms.items():
                ct = ContentType.objects.get_for_model(model)
                for action in actions:
                    codename = f'{action}_{model._meta.model_name}'
                    perm, _ = Permission.objects.get_or_create(
                        codename=codename, content_type=ct,
                        defaults={'name': f'Can {action} {model._meta.verbose_name}'},
                    )
                    perms.append(perm)
            group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(
                f'{role}: {len(perms)} permissions assigned to group.'
            ))

        # ------------------------------------------------------------------
        # 2. Account-creation groups (governance doc §2).
        # ------------------------------------------------------------------
        for group_name, codenames in ACCOUNT_CREATION_GROUPS.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            perms = _grant_user_perms(group, codenames)
            self.stdout.write(self.style.SUCCESS(
                f'{group_name}: {len(perms)} account-creation permissions assigned.'
            ))

        # ------------------------------------------------------------------
        # 3. Make sure every existing user is in at least their role group.
        #    NOTE: `.add()`, not `.set()` — the post_save signal on User
        #    also uses `.add()` so that a Registry Clerk's account-creation
        #    group survives re-runs of this command.
        # ------------------------------------------------------------------
        for user in User.objects.all():
            group, _ = Group.objects.get_or_create(name=user.role)
            user.groups.add(group)

        self.stdout.write(self.style.SUCCESS('Done.'))