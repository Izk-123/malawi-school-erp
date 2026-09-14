"""django-tables2: sortable, paginated Student list (ST-15/16/17/18)."""
import django_tables2 as tables
from .models import Student


class StudentTable(tables.Table):
    full_name = tables.Column(linkify=lambda record: record.get_absolute_url() if hasattr(record, 'get_absolute_url') else None)
    class_display = tables.Column(verbose_name='Class', order_by=('class_name', 'stream'))
    fee_status = tables.TemplateColumn(
        template_code='<span class="badge rounded-pill {% if value == "paid" %}bg-success-subtle text-success{% elif value == "due" %}bg-danger-subtle text-danger{% else %}bg-warning-subtle text-warning{% endif %}">{{ value }}</span>'
    )
    status = tables.TemplateColumn(
        template_code='<span class="badge rounded-pill bg-success-subtle text-success">{{ record.get_status_display }}</span>'
    )
    actions = tables.TemplateColumn(
        template_code='''
        <a class="btn btn-sm btn-outline-primary" href="{% url "students:detail" record.pk %}"><i class="bi bi-eye"></i></a>
        {% if record.can_edit_flag %}
        <a class="btn btn-sm btn-outline-secondary" href="{% url "students:update" record.pk %}"><i class="bi bi-pencil"></i></a>
        <a class="btn btn-sm btn-outline-danger" href="{% url "students:delete" record.pk %}"><i class="bi bi-trash"></i></a>
        {% endif %}
        ''',
        orderable=False, verbose_name='',
    )

    class Meta:
        model = Student
        template_name = 'django_tables2/bootstrap5.html'
        fields = ('student_id', 'full_name', 'class_display', 'guardian_name', 'attendance_percentage', 'fee_status', 'status')
        sequence = ('student_id', 'full_name', 'class_display', 'guardian_name', 'attendance_percentage', 'fee_status', 'status', 'actions')
        order_by = 'full_name'
