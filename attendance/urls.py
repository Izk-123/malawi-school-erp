from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('mark/', views.MarkAttendanceView.as_view(), name='mark'),
    path('mark/all-present/', views.MarkAllPresentView.as_view(), name='mark_all_present'),
    path('undo/', views.UndoLastMarkView.as_view(), name='undo'),
    path('summary/', views.AttendanceSummaryView.as_view(), name='summary'),
    path('history/', views.TeacherAttendanceHistoryView.as_view(), name='history'),
    path('admin-summary/', views.AdminAttendanceSummaryView.as_view(), name='admin_summary'),
    path('export/', views.AttendanceExportView.as_view(), name='export'),
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my_attendance'),
    path('child/<int:pk>/attendance/', views.ChildAttendanceView.as_view(), name='child_attendance'),
]
