"""
Seeds the database with the same demo data used by the original static
prototype (Mzuzu Secondary School), so `runserver` gives you something to
click around immediately.

    python manage.py seed_demo_data
"""
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from students.models import Student
from teachers.models import Teacher, ClassAssignment
from staff.models import StaffMember
from attendance.models import AttendanceRecord
from grades.models import GradeRecord
from fees.models import FeeTransaction
from timetable.models import TimetablePeriod

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data matching the original HTML prototype.'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo users & records...')

        admin_user, _ = User.objects.get_or_create(
            username='admin', defaults={'role': 'admin', 'is_superuser': True, 'is_staff': True}
        )
        admin_user.set_password('admin123')
        admin_user.save()

        teacher_user, _ = User.objects.get_or_create(username='jkamanga', defaults={'role': 'teacher'})
        teacher_user.set_password('teacher123')
        teacher_user.save()

        parent_user, _ = User.objects.get_or_create(username='mrsphiri', defaults={'role': 'parent'})
        parent_user.set_password('parent123')
        parent_user.save()

        student_user, _ = User.objects.get_or_create(username='cbanda', defaults={'role': 'student'})
        student_user.set_password('student123')
        student_user.save()

        staff_user, _ = User.objects.get_or_create(username='cmoyo', defaults={'role': 'staff'})
        staff_user.set_password('staff123')
        staff_user.save()

        teacher, _ = Teacher.objects.get_or_create(
            teacher_id='TCH001', defaults={
                'user': teacher_user, 'full_name': 'Mr. John Kamanga', 'subject': 'Mathematics',
                'qualification': 'BSc Education', 'phone_number': '+265 981 111 222',
                'email': 'jkamanga@mzuzusec.mw',
            }
        )
        for cls, stream in [('Form 3', 'A'), ('Form 4', 'A'), ('Form 4', 'B')]:
            ClassAssignment.objects.get_or_create(teacher=teacher, class_name=cls, stream=stream, subject='Mathematics')

        Teacher.objects.get_or_create(teacher_id='TCH002', defaults={
            'full_name': 'Mrs. Grace Mwansa', 'subject': 'English', 'qualification': 'BA Literature',
            'phone_number': '+265 982 222 333', 'email': 'gmwansa@mzuzusec.mw',
        })
        Teacher.objects.get_or_create(teacher_id='TCH003', defaults={
            'full_name': 'Mr. Peter Banda', 'subject': 'Physics', 'qualification': 'BSc Physics',
            'phone_number': '+265 983 333 444', 'email': 'pbanda@mzuzusec.mw',
        })

        StaffMember.objects.get_or_create(staff_id='STF001', defaults={
            'user': staff_user, 'full_name': 'Mrs. Chisomo Moyo', 'position': 'Bursar',
            'department': 'Finance', 'phone_number': '+265 980 123 456', 'email': 'cmoyo@mzuzusec.mw',
        })
        StaffMember.objects.get_or_create(staff_id='STF002', defaults={
            'full_name': 'Mr. William Kachingwe', 'position': 'Librarian',
            'department': 'Library', 'phone_number': '+265 981 234 567', 'email': 'wkachingwe@mzuzusec.mw',
        })

        students_data = [
            ('STU001', student_user, 'Chikondi Banda', 'Male', '2007-05-12', 'Mr. Banda', '+265 991 234 567', 'Form 3', 'A', 45000, 120000, 92, 'B+'),
            ('STU002', None, 'Thandiwe Phiri', 'Female', '2007-08-23', 'Mrs. Phiri', '+265 992 345 678', 'Form 3', 'A', 80000, 120000, 88, 'A-'),
            ('STU003', None, 'Mphatso Chirwa', 'Male', '2008-01-15', 'Mr. Chirwa', '+265 993 456 789', 'Form 2', 'B', 30000, 110000, 75, 'C+'),
            ('STU004', None, 'Tamanda Mbewe', 'Female', '2006-11-30', 'Mrs. Mbewe', '+265 994 567 890', 'Form 4', 'A', 100000, 130000, 95, 'A'),
        ]
        created_students = {}
        for sid, user, name, gender, dob, guardian, phone, cls, stream, paid, total, att, grade in students_data:
            student, _ = Student.objects.get_or_create(student_id=sid, defaults={
                'user': user, 'full_name': name, 'gender': gender,
                'date_of_birth': datetime.date.fromisoformat(dob), 'guardian_name': guardian,
                'guardian_phone': phone, 'class_name': cls, 'stream': stream,
                'fees_paid': paid, 'fees_total': total, 'attendance_percentage': att,
                'average_grade': grade, 'address': 'Mzuzu, Malawi',
            })
            created_students[sid] = student

        created_students['STU002'].guardians.add(parent_user)

        GradeRecord.objects.get_or_create(
            student=created_students['STU001'], subject='Mathematics', exam='Mid-Term',
            defaults={'score': 78}
        )
        FeeTransaction.objects.get_or_create(
            student=created_students['STU001'], date=datetime.date(2025, 5, 15), amount=25000,
            defaults={'method': 'Mobile Money', 'receipt_no': 'RCP-2025-001'}
        )
        AttendanceRecord.objects.get_or_create(
            student=created_students['STU001'], date=datetime.date(2025, 6, 9),
            defaults={'status': 'present'}
        )
        TimetablePeriod.objects.get_or_create(
            day='Monday', start_time=datetime.time(7, 30), end_time=datetime.time(8, 15),
            subject='Mathematics', teacher=teacher, class_name='Form 3', stream='A',
        )

        self.stdout.write(self.style.SUCCESS(
            'Done. Login as admin/admin123, jkamanga/teacher123, cbanda/student123, '
            'mrsphiri/parent123, or cmoyo/staff123.'
        ))
