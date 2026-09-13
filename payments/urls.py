from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pay/<int:student_id>/', views.InitiatePaymentView.as_view(), name='initiate'),
    path('return/<str:reference>/', views.PaymentReturnView.as_view(), name='return'),
    path('webhook/<str:gateway_name>/', views.PaymentWebhookView.as_view(), name='webhook'),
]
