from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from simple_history.models import HistoricalRecords


class ExamSession(models.Model):
    """SY-22/23/24: a specific exam cycle (e.g. 'MSCE 2025'); students,
    grades, and reports reference whichever session is current."""
    name = models.CharField(max_length=100, unique=True)
    exam_year = models.PositiveIntegerField()
    is_current = models.BooleanField(default=False)
    date_effective = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-exam_year']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            # SY-23: only one session may be current at a time.
            ExamSession.objects.exclude(pk=self.pk).update(is_current=False)


class Subject(models.Model):
    """SY-01/02/03: an MSCE subject with its official MANEB code."""
    CORE_ELEMENTS = [
        ('sciences', 'Sciences'),
        ('languages', 'Languages'),
        ('humanities', 'Humanities'),
        ('technical', 'Technical/Vocational'),
        ('business', 'Business & Commerce'),
        ('maths', 'Mathematics'),
        ('arts', 'Creative Arts'),
    ]

    code = models.CharField(
        max_length=10, unique=True, db_index=True,
        validators=[RegexValidator(r'^M\d{3}$', 'Code must be in format M### (e.g., M131).')],
        help_text='MANEB subject code, e.g., M131 for Mathematics',
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CORE_ELEMENTS)
    is_elective = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'

    @property
    def paper_count(self):
        return self.papers.count()


class Paper(models.Model):
    """SY-06/07/08: a specific paper of a subject."""
    PAPER_TYPES = [
        ('theory', 'Theory'),
        ('practical', 'Practical'),
        ('coursework', 'Coursework'),
        ('oral', 'Oral/Aural'),
        ('project', 'Project'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='papers')
    number = models.CharField(max_length=10, help_text='e.g., I, II, III')
    title = models.CharField(max_length=150, blank=True, help_text="e.g., 'Theory paper'")
    paper_type = models.CharField(max_length=20, choices=PAPER_TYPES)
    duration_minutes = models.PositiveIntegerField(help_text='Duration in minutes')
    total_marks = models.PositiveIntegerField()
    description = models.TextField(blank=True, help_text='Rules/format from MANEB syllabus')

    class Meta:
        ordering = ['subject', 'number']
        unique_together = ('subject', 'number')

    def __str__(self):
        return f'{self.subject.code} Paper {self.number} ({self.paper_type})'


class SyllabusTopic(models.Model):
    """SY-10/11/12/13/14: hierarchical topic tree per subject."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    paper = models.ForeignKey(
        Paper, on_delete=models.SET_NULL, null=True, blank=True, related_name='topics',
        help_text='Paper(s) this topic is tested in',
    )
    core_element = models.CharField(max_length=150, blank=True, help_text="e.g., 'Functions and Graphs'")
    code = models.CharField(max_length=20, blank=True, db_index=True, help_text="Syllabus code like '3.3.1.1'")
    title = models.CharField(max_length=200)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtopics')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['subject', 'order', 'title']
        indexes = [
            models.Index(fields=['subject', 'is_active']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f'{self.code} {self.title}' if self.code else self.title


class AssessmentObjective(models.Model):
    """SY-15/16: a 'candidates should be able to...' statement under a topic."""
    topic = models.ForeignKey(SyllabusTopic, on_delete=models.CASCADE, related_name='objectives')
    text = models.TextField(help_text="e.g., 'find images of polynomial functions'")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['topic', 'order']

    def __str__(self):
        return self.text[:80]


class GradeDescriptor(models.Model):
    """SY-18/20/21: MANEB Pass / Credit / Distinction descriptors."""
    GRADE_CHOICES = [
        ('pass', 'Pass'),
        ('credit', 'Credit'),
        ('distinction', 'Distinction'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grade_descriptors')
    paper = models.ForeignKey(
        Paper, on_delete=models.SET_NULL, null=True, blank=True,
        help_text='Some subjects publish descriptors per paper',
    )
    grade_band = models.CharField(max_length=20, choices=GRADE_CHOICES)
    descriptor = models.TextField(help_text='The abilities candidates must demonstrate at this band')

    class Meta:
        ordering = ['subject', 'paper', 'grade_band']
        unique_together = ('subject', 'paper', 'grade_band')

    def __str__(self):
        return f'{self.subject.code} - {self.get_grade_band_display()}'


class ManebGradeScale(models.Model):
    """SY-19: Grades 1-9 -> Distinction/Credit/Pass/Fail, GCE 'O' equivalence."""
    grade_number = models.PositiveSmallIntegerField(unique=True)
    label = models.CharField(max_length=30, help_text='Distinction / Credit / Pass / Fail')
    gce_equivalent = models.BooleanField(default=False, help_text="Grades 1-6 are GCE 'O' Level equivalent")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['grade_number']

    def __str__(self):
        return f'Grade {self.grade_number} - {self.label}'

    @classmethod
    def for_score(cls, score):
        """Maps a numeric score to a MANEB grade band, used by GradeRecord.save()."""
        score = float(score)
        if score >= 90:
            number = 1
        elif score >= 80:
            number = 2
        elif score >= 70:
            number = 3
        elif score >= 60:
            number = 4
        elif score >= 55:
            number = 5
        elif score >= 50:
            number = 6
        elif score >= 45:
            number = 7
        elif score >= 40:
            number = 8
        else:
            number = 9
        return cls.objects.filter(grade_number=number).first()


class TopicCoverage(models.Model):
    """
    SY-17/36: lets a teacher mark a topic as covered for one of their
    classes, which powers the 'syllabus coverage tracker' (% taught).
    Kept at topic granularity rather than per-objective to keep the
    teacher-facing UI to one checklist per class instead of one per
    'candidates should be able to...' bullet.
    """
    topic = models.ForeignKey(SyllabusTopic, on_delete=models.CASCADE, related_name='coverage_records')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='topic_coverage')
    class_name = models.CharField(max_length=10)
    stream = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B')])
    is_covered = models.BooleanField(default=False)
    covered_on = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('topic', 'teacher', 'class_name', 'stream')

    def __str__(self):
        status = 'covered' if self.is_covered else 'pending'
        return f'{self.topic} - {self.class_name}{self.stream} - {status}'

    def clean(self):
        if self.teacher_id and self.topic_id:
            allowed = self.teacher.syllabus_subjects.filter(pk=self.topic.subject_id).exists()
            if not allowed:
                raise ValidationError("You can only mark coverage for a subject you're assigned to teach.")
