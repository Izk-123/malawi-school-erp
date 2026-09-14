from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('', views.StaffListView.as_view(), name='list'),
    path('dashboard/', views.StaffPortalDashboardView.as_view(), name='dashboard'),
    path('profile/', views.MyProfileView.as_view(), name='my_profile'),
    path('leave/', views.MyLeaveView.as_view(), name='my_leave'),
    path('leave/request/', views.RequestLeaveView.as_view(), name='request_leave'),
    path('leave/approval/', views.LeaveApprovalView.as_view(), name='leave_approval'),
    path('leave/<int:pk>/decide/', views.DecideLeaveView.as_view(), name='decide_leave'),
    path('clock/', views.ClockInOutView.as_view(), name='clock'),
    path('announcements/', views.AnnouncementListView.as_view(), name='announcements'),
    path('announcements/post/', views.PostAnnouncementView.as_view(), name='post_announcement'),
    path('tickets/', views.TicketListView.as_view(), name='tickets'),
    path('tickets/raise/', views.RaiseTicketView.as_view(), name='raise_ticket'),
    path('tickets/<int:pk>/resolve/', views.ResolveTicketView.as_view(), name='resolve_ticket'),
    path('payslips/', views.MyPayslipsView.as_view(), name='my_payslips'),
    path('payslips/<int:pk>/pdf/', views.PayslipPDFView.as_view(), name='payslip_pdf'),

    # Librarian
    path('library/books/', views.BookListView.as_view(), name='book_list'),
    path('library/books/add/', views.BookCreateView.as_view(), name='book_create'),
    path('library/loans/', views.LoanListView.as_view(), name='loan_list'),
    path('library/loans/issue/', views.IssueBookView.as_view(), name='issue_book'),
    path('library/loans/<int:pk>/return/', views.ReturnBookView.as_view(), name='return_book'),

    # Security
    path('security/visitors/', views.VisitorLogListView.as_view(), name='visitor_list'),
    path('security/visitors/log/', views.LogVisitorView.as_view(), name='log_visitor'),
    path('security/visitors/<int:pk>/sign-out/', views.SignOutVisitorView.as_view(), name='sign_out_visitor'),
    path('security/gate-passes/', views.GatePassListView.as_view(), name='gate_pass_list'),
    path('security/gate-passes/issue/', views.IssueGatePassView.as_view(), name='issue_gate_pass'),
    path('security/gate-passes/<int:pk>/mark/', views.MarkGatePassView.as_view(), name='mark_gate_pass'),

    # Nurse
    path('nurse/visits/', views.SickBayVisitListView.as_view(), name='sickbay_list'),
    path('nurse/visits/record/', views.RecordSickBayVisitView.as_view(), name='record_sickbay_visit'),
    path('nurse/medical-record/<int:student_id>/', views.MedicalRecordUpdateView.as_view(), name='medical_record'),
    path('nurse/stock/', views.MedicationStockListView.as_view(), name='medication_stock'),
    path('nurse/stock/add/', views.MedicationStockCreateView.as_view(), name='medication_stock_create'),
]
