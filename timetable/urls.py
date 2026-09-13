from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    path('', views.TimetableListView.as_view(), name='list'),
    path('my-timetable/', views.MyTimetableView.as_view(), name='my_timetable'),
]
