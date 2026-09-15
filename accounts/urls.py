from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Dashboard & auth
    path('', views.dashboard, name='dashboard'),
    path('login/', views.SchoolLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),

    # Live-validation endpoints (used by profile edit)
    path('api/check-email/', views.check_email, name='check_email'),

    # Email verification (AC-07c/e)
    path('verify-email/pending/', views.verify_email_pending, name='verify_email_pending'),
    path('verify-email/resend/', views.resend_email, name='resend_email'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),

    # Phone verification (AC-07c/e)
    path('phone/request/', views.phone_request, name='phone_request'),
    path('phone/confirm/', views.phone_confirm, name='phone_confirm'),

    # Password change (logged in) & reset (forgotten password)
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.SchoolPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', views.SchoolPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', views.SchoolPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Self-service profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),

    # Admin user management
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/toggle-active/', views.UserToggleActiveView.as_view(), name='user_toggle_active'),
    path('users/<int:pk>/unlock/', views.UserUnlockView.as_view(), name='user_unlock'),
]