from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    StaffMember, StaffRoleAssignment, LeaveRequest, StaffAttendance,
    StaffAnnouncement, StaffTicket, Payslip, Book, BookLoan, VisitorLog,
    GatePass, PatrolLog, MedicalRecord, SickBayVisit, MedicationStock,
)


class StaffRoleAssignmentInline(TabularInline):
    model = StaffRoleAssignment
    extra = 1


@admin.register(StaffMember)
class StaffMemberAdmin(ModelAdmin):
    list_display = ('staff_id', 'full_name', 'position', 'department', 'status')
    list_filter = ('department', 'status')
    search_fields = ('full_name', 'staff_id')
    inlines = [StaffRoleAssignmentInline]


@admin.register(LeaveRequest)
class LeaveRequestAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('staff', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('leave_type', 'status')


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(ModelAdmin):
    list_display = ('staff', 'date', 'clock_in', 'clock_out')
    list_filter = ('date',)


@admin.register(StaffAnnouncement)
class StaffAnnouncementAdmin(ModelAdmin):
    list_display = ('title', 'posted_by', 'posted_at', 'pinned')


@admin.register(StaffTicket)
class StaffTicketAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('ticket_type', 'raised_by', 'assigned_to', 'status', 'created_at')
    list_filter = ('ticket_type', 'status')


@admin.register(Payslip)
class PayslipAdmin(ModelAdmin):
    list_display = ('staff', 'month', 'year', 'gross_pay', 'net_pay')
    list_filter = ('year', 'month')


@admin.register(Book)
class BookAdmin(ModelAdmin):
    list_display = ('title', 'author', 'subject', 'total_copies', 'copies_available')
    search_fields = ('title', 'author', 'isbn')


@admin.register(BookLoan)
class BookLoanAdmin(ModelAdmin):
    list_display = ('book', 'borrower_name', 'issued_date', 'due_date', 'returned_date')
    list_filter = ('issued_date',)


@admin.register(VisitorLog)
class VisitorLogAdmin(ModelAdmin):
    list_display = ('name', 'purpose', 'host', 'time_in', 'time_out')


@admin.register(GatePass)
class GatePassAdmin(ModelAdmin):
    list_display = ('student', 'reason', 'status', 'time_out', 'time_in')
    list_filter = ('status',)


@admin.register(PatrolLog)
class PatrolLogAdmin(ModelAdmin):
    list_display = ('guard', 'checkpoint', 'timestamp')


@admin.register(MedicalRecord)
class MedicalRecordAdmin(ModelAdmin):
    list_display = ('student', 'updated_at')


@admin.register(SickBayVisit)
class SickBayVisitAdmin(ModelAdmin):
    list_display = ('student', 'nurse', 'visit_date', 'referred')
    list_filter = ('referred',)


@admin.register(MedicationStock)
class MedicationStockAdmin(ModelAdmin):
    list_display = ('name', 'quantity', 'reorder_level', 'expiry_date')
