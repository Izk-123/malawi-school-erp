from import_export import resources
from import_export.results import RowResult
from .models import Student


class StudentResource(resources.ModelResource):
    """ST-26/27/28: CSV/Excel import & export with row-by-row error reporting
    (django-import-export surfaces per-row errors automatically via
    `result.row_errors()` / `result.invalid_rows` in the admin UI)."""

    class Meta:
        model = Student
        fields = (
            'student_id', 'full_name', 'gender', 'date_of_birth', 'guardian_name',
            'guardian_phone', 'class_name', 'stream', 'status', 'fees_total', 'fees_paid',
        )
        export_order = fields
        import_id_fields = ('student_id',)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        # ST-27: basic required-field validation with a clear error per row.
        required = ['full_name', 'gender', 'date_of_birth', 'class_name']
        missing = [f for f in required if not row.get(f)]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}")
