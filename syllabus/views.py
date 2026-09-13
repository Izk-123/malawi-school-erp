from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Avg, Count, Prefetch
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView, DetailView

from accounts.mixins import RoleRequiredMixin
from teachers.models import Teacher
from .models import Subject, Paper, SyllabusTopic, ManebGradeScale, TopicCoverage
from .filters import SubjectFilter, TopicFilter
from .resources import SubjectResource


class SubjectListView(LoginRequiredMixin, ListView):
    """SY-30/32: browse subjects, filterable by category/elective status.
    Read-only for everyone; editing happens in /admin/ (SY-41)."""
    model = Subject
    template_name = 'syllabus/subject_list.html'
    context_object_name = 'subjects'
    paginate_by = 30

    def get_queryset(self):
        qs = Subject.objects.filter(is_active=True).prefetch_related('papers')
        self.filterset = SubjectFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filterset
        return ctx


class SubjectDetailView(LoginRequiredMixin, DetailView):
    """SY-33: papers, topic tree, and grade descriptors in one view."""
    model = Subject
    template_name = 'syllabus/subject_detail.html'
    context_object_name = 'subject'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['papers'] = self.object.papers.all()
        ctx['topics'] = (
            self.object.topics.filter(parent__isnull=True, is_active=True)
            .prefetch_related(
                Prefetch('subtopics', queryset=SyllabusTopic.objects.filter(is_active=True)),
                'objectives',
            )
        )
        ctx['descriptors'] = self.object.grade_descriptors.all()
        return ctx


class PaperDetailView(LoginRequiredMixin, DetailView):
    model = Paper
    template_name = 'syllabus/paper_detail.html'
    context_object_name = 'paper'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['topics'] = self.object.topics.filter(is_active=True).prefetch_related('objectives')
        return ctx


class SyllabusBrowseView(LoginRequiredMixin, ListView):
    """SY-30/31: browse/search topics across subjects."""
    model = SyllabusTopic
    template_name = 'syllabus/browse.html'
    context_object_name = 'topics'
    paginate_by = 50

    def get_queryset(self):
        qs = SyllabusTopic.objects.filter(parent__isnull=True, is_active=True).select_related('subject', 'paper')
        self.filterset = TopicFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filterset
        ctx['subjects'] = Subject.objects.filter(is_active=True)
        return ctx


class GradeScaleView(LoginRequiredMixin, ListView):
    model = ManebGradeScale
    template_name = 'syllabus/grade_scale.html'
    context_object_name = 'grades'


class SubjectExportView(LoginRequiredMixin, RoleRequiredMixin, View):
    """SY-37: export the subject list to CSV."""
    allowed_roles = ['admin']

    def get(self, request):
        dataset = SubjectResource().export(Subject.objects.all())
        response = HttpResponse(dataset.csv, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="maneb_subjects.csv"'
        return response


class MySubjectsView(LoginRequiredMixin, RoleRequiredMixin, View):
    """SY-17/26: a teacher's syllabus subjects, with a topic-coverage
    checklist per class they're assigned to teach that subject in."""
    allowed_roles = ['teacher']

    def get(self, request):
        teacher = Teacher.objects.filter(user=request.user).first()
        if not teacher:
            return render(request, 'syllabus/my_subjects.html', {'teacher': None})
        subjects = teacher.syllabus_subjects.prefetch_related('topics')
        class_pairs = teacher.classes_taught_list()
        coverage_lookup = {
            (c.topic_id, c.class_name, c.stream): c
            for c in TopicCoverage.objects.filter(teacher=teacher)
        }
        subject_data = []
        for subject in subjects:
            topics = list(subject.topics.filter(is_active=True))
            for class_name, stream in class_pairs:
                covered_count = 0
                annotated_topics = []
                for t in topics:
                    coverage = coverage_lookup.get((t.id, class_name, stream))
                    is_covered = bool(coverage and coverage.is_covered)
                    if is_covered:
                        covered_count += 1
                    annotated_topics.append({'topic': t, 'is_covered': is_covered})
                subject_data.append({
                    'subject': subject, 'class_name': class_name, 'stream': stream,
                    'topics': annotated_topics,
                    'covered': covered_count, 'total': len(topics),
                    'percentage': round(covered_count / len(topics) * 100) if topics else 0,
                })
        return render(request, 'syllabus/my_subjects.html', {'teacher': teacher, 'subject_data': subject_data})


class ToggleTopicCoverageView(LoginRequiredMixin, RoleRequiredMixin, View):
    """SY-17: teachers mark a topic covered/pending for one of their classes."""
    allowed_roles = ['teacher']

    def post(self, request, topic_id):
        import datetime
        teacher = Teacher.objects.filter(user=request.user).first()
        topic = SyllabusTopic.objects.filter(pk=topic_id).first()
        class_name = request.POST.get('class_name')
        stream = request.POST.get('stream')
        if not (teacher and topic and class_name and stream):
            messages.error(request, 'Could not update coverage - missing information.')
            return redirect('syllabus:my_subjects')

        coverage, _ = TopicCoverage.objects.get_or_create(
            topic=topic, teacher=teacher, class_name=class_name, stream=stream,
        )
        coverage.is_covered = not coverage.is_covered
        coverage.covered_on = datetime.date.today() if coverage.is_covered else None
        coverage.full_clean()
        coverage.save()
        return redirect('syllabus:my_subjects')


class TopicPerformanceView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """SY-34/35: topic-level average score & attempt count for a subject,
    flagging anything below the MANEB pass threshold (40%)."""
    template_name = 'syllabus/topic_performance.html'
    context_object_name = 'topics'
    allowed_roles = ['admin', 'teacher']
    PASS_THRESHOLD = 40

    def get_queryset(self):
        subject_id = self.request.GET.get('subject')
        if not subject_id:
            return SyllabusTopic.objects.none()
        return (
            SyllabusTopic.objects.filter(is_active=True, subject_id=subject_id)
            .annotate(avg_score=Avg('grade_records__score'), attempts=Count('grade_records'))
            .filter(attempts__gte=1)
            .order_by('avg_score')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['subjects'] = Subject.objects.filter(is_active=True)
        ctx['selected_subject'] = self.request.GET.get('subject')
        ctx['pass_threshold'] = self.PASS_THRESHOLD
        return ctx
