"""
AC-16/17: create one Django Group per role and grant it the model
permissions appropriate for that role. Users are auto-added to their role's
group by the `sync_role_group` signal in accounts/signals.py; this command
just needs to (re)run whenever permissions should be recalculated, e.g.
after adding a new app/model.

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


class Command(BaseCommand):
    help = 'Sync Django Groups/permissions to match each role (AC-16/17).'

    def handle(self, *args, **options):
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
            self.stdout.write(self.style.SUCCESS(f'{role}: {len(perms)} permissions assigned to group.'))

        # Make sure every existing user is in their role's group.
        for user in User.objects.all():
            group, _ = Group.objects.get_or_create(name=user.role)
            user.groups.set([group])

        self.stdout.write(self.style.SUCCESS('Done.'))
