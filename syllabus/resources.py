"""SY-37/38/39: CSV import/export of subjects and topics."""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Subject, SyllabusTopic


class SubjectResource(resources.ModelResource):
    class Meta:
        model = Subject
        fields = ('code', 'name', 'category', 'is_elective', 'is_active')
        export_order = fields
        import_id_fields = ('code',)


class SyllabusTopicResource(resources.ModelResource):
    subject_code = fields.Field(attribute='subject', column_name='subject_code', widget=ForeignKeyWidget(Subject, 'code'))

    class Meta:
        model = SyllabusTopic
        fields = ('code', 'title', 'subject_code', 'core_element', 'order', 'is_active')
        export_order = fields
