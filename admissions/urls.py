from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
    path('', views.AdmissionsDashboardView.as_view(), name='dashboard'),

    # Enquiry
    path('enquiries/', views.EnquiryListView.as_view(), name='enquiry_list'),
    path('enquiries/new/', views.EnquiryCreateView.as_view(), name='enquiry_create'),
    path('enquiries/<int:pk>/', views.EnquiryDetailView.as_view(), name='enquiry_detail'),
    path('enquiries/<int:pk>/edit/', views.EnquiryUpdateView.as_view(), name='enquiry_update'),
    path('enquiries/<int:pk>/convert/', views.ConvertEnquiryView.as_view(), name='enquiry_convert'),

    # Applicant
    path('applicants/', views.ApplicantListView.as_view(), name='applicant_list'),
    path('applicants/new/', views.ApplicantCreateView.as_view(), name='applicant_create'),
    path('applicants/<int:pk>/', views.ApplicantDetailView.as_view(), name='applicant_detail'),
    path('applicants/<int:pk>/edit/', views.ApplicantUpdateView.as_view(), name='applicant_update'),
    path('applicants/<int:pk>/documents/', views.ApplicantUploadDocumentView.as_view(), name='applicant_upload_document'),
    path('applicants/<int:pk>/priority/', views.ApplicantAddPriorityView.as_view(), name='applicant_add_priority'),

    # Exam
    path('exams/', views.ExamSessionListView.as_view(), name='exam_session_list'),
    path('exams/new/', views.ExamSessionCreateView.as_view(), name='exam_session_create'),
    path('exams/<int:pk>/', views.ExamSessionDetailView.as_view(), name='exam_session_detail'),
    path('exams/<int:pk>/assign/', views.AssignExamView.as_view(), name='exam_assign'),
    path('exams/<int:pk>/publish/', views.PublishExamResultsView.as_view(), name='exam_publish'),
    path('exams/assignments/<int:assignment_id>/mark/', views.RecordExamMarkView.as_view(), name='exam_record_mark'),

    # Interview
    path('applicants/<int:pk>/interview/', views.RecordInterviewView.as_view(), name='record_interview'),

    # Offer
    path('applicants/<int:pk>/offer/issue/', views.IssueOfferView.as_view(), name='issue_offer'),
    path('applicants/<int:pk>/offer/accept/', views.AcceptOfferView.as_view(), name='accept_offer'),
    path('applicants/<int:pk>/offer/decline/', views.DeclineOfferView.as_view(), name='decline_offer'),

    # Admit
    path('applicants/<int:pk>/admit/', views.AdmitApplicantView.as_view(), name='admit'),

    # Waitlist
    path('waitlist/', views.WaitlistView.as_view(), name='waitlist'),
    path('applicants/<int:pk>/waitlist/add/', views.AddToWaitlistView.as_view(), name='waitlist_add'),
]