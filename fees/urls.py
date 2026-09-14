from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.FeeListView.as_view(), name='list'),
    path('pay/', views.RecordPaymentView.as_view(), name='pay'),
    path('my-fees/', views.MyFeesView.as_view(), name='my_fees'),
    path('receipt/<int:pk>/', views.ReceiptView.as_view(), name='receipt'),
    path('receipt/<int:pk>/pdf/', views.ReceiptPDFView.as_view(), name='receipt_pdf'),
    path('reverse/<int:pk>/', views.ReversePaymentView.as_view(), name='reverse'),
    path('reports/ageing/', views.AgeingReportView.as_view(), name='ageing_report'),
    path('reports/defaulters/', views.DefaultersReportView.as_view(), name='defaulters_report'),
    path('reports/daily-collection/', views.DailyCollectionReportView.as_view(), name='daily_collection'),
    path('reports/export/', views.ExportTransactionsView.as_view(), name='export_transactions'),
]
