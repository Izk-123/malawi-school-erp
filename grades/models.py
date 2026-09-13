from django.db import models


class GradeRecord(models.Model):
    EXAM_CHOICES = [
        ('Mid-Term', 'Mid-Term'),
        ('Final Exam', 'Final Exam'),
        ('Quiz', 'Quiz'),
        ('Assignment', 'Assignment'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='grade_records')
    subject = models.CharField(max_length=100)
    # SY-27: optional links into the syllabus app for MANEB-aligned,
    # topic-level analytics. Left nullable so existing grade entry (which
    # just free-types a subject name) keeps working unchanged; picking a
    # syllabus subject/topic is an enhancement, not a requirement, when
    # recording a grade.
    syllabus_subject = models.ForeignKey(
        'syllabus.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='grade_records',
    )
    syllabus_paper = models.ForeignKey(
        'syllabus.Paper', on_delete=models.SET_NULL, null=True, blank=True, related_name='grade_records',
    )
    syllabus_topic = models.ForeignKey(
        'syllabus.SyllabusTopic', on_delete=models.SET_NULL, null=True, blank=True, related_name='grade_records',
        help_text='Which syllabus topic was this assessment on?',
    )
    maneb_grade = models.ForeignKey(
        'syllabus.ManebGradeScale', on_delete=models.SET_NULL, null=True, blank=True,
        help_text='Auto-mapped MANEB grade (1-9) from the score.',
    )
    exam = models.CharField(max_length=20, choices=EXAM_CHOICES, default='Mid-Term')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=3, blank=True)
    recorded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    recorded_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_on']

    def __str__(self):
        return f'{self.student.full_name} - {self.subject} ({self.exam}): {self.score}%'

    @staticmethod
    def score_to_letter(score):
        score = float(score)
        if score >= 90:
            return 'A'
        if score >= 80:
            return 'A-'
        if score >= 75:
            return 'B+'
        if score >= 70:
            return 'B'
        if score >= 65:
            return 'B-'
        if score >= 60:
            return 'C+'
        if score >= 55:
            return 'C'
        if score >= 45:
            return 'D'
        if score >= 35:
            return 'E'
        return 'F'

    def save(self, *args, **kwargs):
        self.grade = self.score_to_letter(self.score)
        if not self.maneb_grade_id:
            from syllabus.models import ManebGradeScale
            self.maneb_grade = ManebGradeScale.for_score(self.score)
        super().save(*args, **kwargs)
        self.student.recompute_average_grade()
