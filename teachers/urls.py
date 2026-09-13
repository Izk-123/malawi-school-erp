from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.TeacherListView.as_view(), name='list'),
    path('add/', views.TeacherCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TeacherDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.TeacherUpdateView.as_view(), name='update'),
    path('my-classes/', views.MyClassesView.as_view(), name='my_classes'),
    path('my-profile/', views.TeacherProfileView.as_view(), name='my_profile'),
    path('roster/<str:class_name>/<str:stream>/', views.ClassRosterView.as_view(), name='class_roster'),
]
