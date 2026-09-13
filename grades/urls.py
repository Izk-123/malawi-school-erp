from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    path('', views.GradeListView.as_view(), name='list'),
    path('add/', views.GradeCreateView.as_view(), name='create'),
    path('<int:pk>/delete/', views.GradeDeleteView.as_view(), name='delete'),
    path('my-grades/', views.MyGradesView.as_view(), name='my_grades'),
]
