from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='list'),
    path('add/', views.StudentCreateView.as_view(), name='create'),
    path('promote/', views.PromoteStudentsView.as_view(), name='promote'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='delete'),
    path('<int:pk>/archive/', views.StudentArchiveView.as_view(), name='archive'),
    path('<int:pk>/guardians/add/', views.GuardianContactCreateView.as_view(), name='guardian_add'),
    path('my-children/', views.MyChildrenView.as_view(), name='my_children'),
]
