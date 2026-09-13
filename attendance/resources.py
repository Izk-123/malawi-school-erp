"""AT-11/AT-25: CSV/Excel export of attendance data."""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from students.models import Student
from .models import AttendanceRecord


class AttendanceResource(resources.ModelResource):
    student_name = fields.Field(attribute='student', column_name='Student', widget=ForeignKeyWidget(Student, 'full_name'))
    student_id = fields.Field(attribute='student', column_name='Student ID', widget=ForeignKeyWidget(Student, 'student_id'))

    class Meta:
        model = AttendanceRecord
        fields = ('student_id', 'student_name', 'date', 'class_name_at_time', 'stream_at_time', 'status', 'marked_by')
        export_order = fields
