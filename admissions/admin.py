from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    Applicant, ApplicantPriority, DocumentAttachment, Enquiry,
    EntranceExam, ExamAssignment, ExamMark, Interview, Offer, WaitlistEntry,
)


class ApplicantPriorityInline(TabularInline):
    model = ApplicantPriority
    extra = 0


class DocumentAttachmentInline(TabularInline):
    model = DocumentAttachment
    extra = 0
    readonly_fields = ('verified_at',)


class ExamMarkInline(TabularInline):
    model = ExamMark
    extra = 0


@admin.register(Enquiry)
class EnquiryAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('student_name', 'parent_name', 'guardian_phone', 'source',
                    'applying_for', 'status', 'enquiry_date')
    list_filter = ('source', 'status', 'applying_for')
    search_fields = ('student_name', 'parent_name', 'guardian_phone')
    readonly_fields = ('created_at', 'converted_at')


@admin.register(Applicant)
class ApplicantAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('applicant_code', 'full_name', 'guardian_phone', 'applying_for',
                    'status', 'composite_score', 'created_at')
    list_filter = ('status', 'gender', 'applying_for', 'boarding_preference')
    search_fields = ('applicant_code', 'full_name', 'guardian_phone', 'pslce_number')
    readonly_fields = ('applicant_code', 'created_at', 'updated_at',
                       'composite_score', 'priority_bonus')
    inlines = [ApplicantPriorityInline, DocumentAttachmentInline]


@admin.register(EntranceExam)
class EntranceExamAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('name', 'exam_date', 'venue', 'capacity', 'cutoff_score', 'is_published')
    list_filter = ('is_published', 'exam_date')


@admin.register(ExamAssignment)
class ExamAssignmentAdmin(ModelAdmin):
    list_display = ('applicant', 'session', 'seat_number', 'attended')
    list_filter = ('attended', 'session')
    inlines = [ExamMarkInline]


@admin.register(Interview)
class InterviewAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('applicant', 'interviewer', 'recommendation', 'conducted_at')
    list_filter = ('recommendation',)


@admin.register(Offer)
class OfferAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('applicant', 'status', 'issued_by', 'issued_at', 'response_deadline')
    list_filter = ('status',)


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(ModelAdmin):
    list_display = ('applicant', 'class_name', 'stream', 'position', 'added_at')
    list_filter = ('class_name', 'stream')
    ordering = ('class_name', 'stream', 'position')