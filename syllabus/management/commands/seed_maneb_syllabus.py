"""
SY-04/SY-40: seed the 22 official MSCE subjects, the MANEB grade scale,
and a starter topic tree for Mathematics and Biology.

Idempotent (SY: 'seeding command shall be idempotent') - uses
update_or_create throughout, so re-running never creates duplicates.

    python manage.py seed_maneb_syllabus
"""
from django.core.management.base import BaseCommand
from syllabus.models import (
    ExamSession, Subject, Paper, SyllabusTopic,
    AssessmentObjective, GradeDescriptor, ManebGradeScale,
)


SUBJECTS = [
    ('M132', 'Additional Mathematics', 'maths', True, 2),
    ('M012', 'Agriculture', 'sciences', True, 2),
    ('M021', 'Bible Knowledge', 'humanities', True, 2),
    ('M022', 'Biology', 'sciences', True, 2),
    ('M023', 'Business Studies', 'business', True, 2),
    ('M032', 'Chichewa', 'languages', False, 3),
    ('M038', 'Chemistry', 'sciences', True, 2),
    ('M034', 'Clothing and Textile', 'technical', True, 2),
    ('M039', 'Computer Studies', 'technical', True, 2),
    ('M015', 'Creative Arts', 'arts', True, 2),
    ('M052', 'English', 'languages', False, 3),
    ('M061', 'French', 'languages', True, 3),
    ('M073', 'Geography', 'humanities', True, 2),
    ('M081', 'History', 'humanities', True, 2),
    ('M082', 'Home Economics', 'technical', True, 2),
    ('M131', 'Mathematics', 'maths', False, 2),
    ('M133', 'Metalwork', 'technical', True, 2),
    ('M164', 'Physics', 'sciences', True, 2),
    ('M182', 'Religious and Moral Education', 'humanities', True, 1),
    ('M199', 'Social Affairs', 'humanities', False, 2),
    ('M201', 'Technical Drawing', 'technical', True, 2),
    ('M231', 'Woodwork', 'technical', True, 2),
]

MANEB_GRADE_SCALE = [
    (1, 'Distinction', True, 'Highest achievement'),
    (2, 'Distinction', True, ''),
    (3, 'Credit', True, ''),
    (4, 'Credit', True, ''),
    (5, 'Credit', True, ''),
    (6, 'Credit', True, ''),
    (7, 'Pass', False, ''),
    (8, 'Pass', False, ''),
    (9, 'Fail', False, 'Did not meet minimum standard'),
]

# A starter topic tree for the two core science/maths subjects mentioned
# in the spec, so the browse/analytics views have real data to show.
# Extend this dict with more subjects/topics as MANEB syllabus content
# is transcribed - the seeder is idempotent so it's safe to keep adding.
TOPIC_TREES = {
    'M131': [  # Mathematics
        ('3.3.1', 'Functions and Graphs', [
            ('3.3.1.1', 'Functions', ['find images of polynomial functions', 'sketch graphs of simple functions']),
            ('3.3.1.2', 'Cartesian Geometry', ['find the gradient and equation of a straight line']),
        ]),
        ('3.3.3', 'Trigonometry', [
            ('3.3.3.1', 'Trigonometric Ratios', ['solve problems involving sine, cosine and tangent ratios']),
        ]),
        ('3.3.4', 'Calculus', [
            ('3.3.4.2', 'Differentiation', ['find derivatives of polynomial functions']),
            ('3.3.4.3', 'Integration', ['find indefinite and definite integrals of polynomial functions']),
        ]),
    ],
    'M022': [  # Biology
        ('4.1.1', 'Cell Biology', [
            ('4.1.1.1', 'Cell Structure', ['identify structures of plant and animal cells']),
            ('4.1.1.2', 'Cell Division', ['describe the stages of mitosis and meiosis']),
        ]),
        ('4.2.1', 'Genetics', [
            ('4.2.1.1', 'Inheritance', ['solve monohybrid genetic crosses']),
        ]),
    ],
}


class Command(BaseCommand):
    help = 'Seed MANEB MSCE syllabus data into the database (idempotent).'

    def handle(self, *args, **options):
        self.stdout.write('Seeding MANEB grade scale...')
        for num, label, gce, desc in MANEB_GRADE_SCALE:
            ManebGradeScale.objects.update_or_create(
                grade_number=num, defaults={'label': label, 'gce_equivalent': gce, 'description': desc},
            )

        self.stdout.write('Creating exam session...')
        ExamSession.objects.update_or_create(
            name='MSCE 2025', defaults={'exam_year': 2025, 'is_current': True},
        )

        self.stdout.write('Seeding subjects & papers...')
        subjects_by_code = {}
        for code, name, cat, elective, num_papers in SUBJECTS:
            subject, _ = Subject.objects.update_or_create(
                code=code, defaults={'name': name, 'category': cat, 'is_elective': elective},
            )
            subjects_by_code[code] = subject
            for i in range(1, num_papers + 1):
                Paper.objects.update_or_create(
                    subject=subject, number=self._roman(i),
                    defaults={
                        'paper_type': 'theory' if i == 1 else 'practical',
                        'duration_minutes': 120,
                        'total_marks': 100,
                    },
                )
            # SY-18: minimal grade descriptors per subject.
            for band, text in [
                ('pass', f'Candidates show a basic understanding of {name} concepts.'),
                ('credit', f'Candidates apply {name} concepts to solve familiar problems.'),
                ('distinction', f'Candidates apply {name} concepts to solve unfamiliar, complex problems.'),
            ]:
                GradeDescriptor.objects.update_or_create(
                    subject=subject, paper=None, grade_band=band, defaults={'descriptor': text},
                )

        self.stdout.write('Seeding starter topic trees (Mathematics, Biology)...')
        for code, topic_groups in TOPIC_TREES.items():
            subject = subjects_by_code.get(code)
            if not subject:
                continue
            for order, (parent_code, parent_title, children) in enumerate(topic_groups):
                parent_topic, _ = SyllabusTopic.objects.update_or_create(
                    subject=subject, code=parent_code, defaults={'title': parent_title, 'order': order, 'parent': None},
                )
                for child_order, (child_code, child_title, objectives) in enumerate(children):
                    child_topic, _ = SyllabusTopic.objects.update_or_create(
                        subject=subject, code=child_code,
                        defaults={'title': child_title, 'order': child_order, 'parent': parent_topic},
                    )
                    for obj_order, obj_text in enumerate(objectives):
                        AssessmentObjective.objects.update_or_create(
                            topic=child_topic, text=obj_text, defaults={'order': obj_order},
                        )

        self.stdout.write(self.style.SUCCESS('Syllabus seeded successfully.'))

    @staticmethod
    def _roman(n):
        return {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}.get(n, str(n))
