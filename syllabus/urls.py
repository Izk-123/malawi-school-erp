from django.urls import path
from . import views

app_name = 'syllabus'

urlpatterns = [
    path('', views.SubjectListView.as_view(), name='subject_list'),
    path('browse/', views.SyllabusBrowseView.as_view(), name='browse'),
    path('grade-scale/', views.GradeScaleView.as_view(), name='grade_scale'),
    path('export/', views.SubjectExportView.as_view(), name='export'),
    path('my-subjects/', views.MySubjectsView.as_view(), name='my_subjects'),
    path('topic/<int:topic_id>/toggle-coverage/', views.ToggleTopicCoverageView.as_view(), name='toggle_coverage'),
    path('performance/', views.TopicPerformanceView.as_view(), name='topic_performance'),
    path('subject/<int:pk>/', views.SubjectDetailView.as_view(), name='subject_detail'),
    path('paper/<int:pk>/', views.PaperDetailView.as_view(), name='paper_detail'),
]
