from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsIndexView.as_view(), name='index'),
    path('export/csv/', views.export_students_csv, name='export_csv'),
]
