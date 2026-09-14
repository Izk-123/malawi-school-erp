import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class StaffMember(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='staff_profile',
    )
    staff_id = models.CharField(max_length=10, unique=True)
    full_name = models.CharField(max_length=150)
    position = models.CharField(max_length=100, help_text='Free-text job title, e.g. "Senior Bursar".')
    department = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    # STF-03: self-service profile fields.
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    next_of_kin = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Staff Member'

    def __str__(self):
        return f'{self.full_name} - {self.position}'

    def has_role(self, role_code):
        return self.role_assignments.filter(role=role_code).exists()

    @property
    def role_codes(self):
        return list(self.role_assignments.values_list('role', flat=True))


class StaffRoleAssignment(models.Model):
    """
    STF-10: 'support multiple roles per staff member'. A plain
    Staff.position free-text field can't be queried/branched on for
    dashboard routing, so each duty-specific role a staff member holds
    (they can hold more than one, e.g. Teacher + Sports Master) gets its
    own row here. `staff/context_processors.py` uses this to pick which
    dashboard widgets to show.
    """
    class Role(models.TextChoices):
        BURSAR = 'bursar', 'Bursar / Accounts Clerk'
        LIBRARIAN = 'librarian', 'Librarian'
        SECRETARY = 'secretary', 'Secretary / Registry Clerk'
        SECURITY = 'security', 'Security Guard'
        NURSE = 'nurse', 'Nurse / Matron'
        ICT = 'ict', 'ICT Officer / Lab Assistant'
        GROUNDSKEEPER = 'groundskeeper', 'Groundskeeper / Caretaker'
        COOK = 'cook', 'Cook / Catering Staff'
        LAB_TECH = 'lab_tech', 'Lab Technician'
        BOARDING_MASTER = 'boarding_master', 'Boarding Master / Mistress'
        SPORTS_MASTER = 'sports_master', 'Sports Master / Mistress'
        CHAPLAIN = 'chaplain', 'Chaplain / Counsellor'
        HR = 'hr', 'HR Officer'
        PROCUREMENT = 'procurement', 'Procurement Officer'
        DRIVER = 'driver', 'Driver / Transport Officer'

    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.CharField(max_length=20, choices=Role.choices)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ('staff', 'role')

    def __str__(self):
        return f'{self.staff.full_name} - {self.get_role_display()}'


class LeaveRequest(models.Model):
    """STF-04/92: leave request + approval workflow."""
    class LeaveType(models.TextChoices):
        ANNUAL = 'annual', 'Annual Leave'
        SICK = 'sick', 'Sick Leave'
        MATERNITY = 'maternity', 'Maternity Leave'
        PATERNITY = 'paternity', 'Paternity Leave'
        COMPASSIONATE = 'compassionate', 'Compassionate Leave'
        UNPAID = 'unpaid', 'Unpaid Leave'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=15, choices=LeaveType.choices, default=LeaveType.ANNUAL)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='leave_approvals',
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.staff.full_name} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})'

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1


class StaffAttendance(models.Model):
    """STF-07: staff clock in/out."""
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=datetime.date.today)
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ('staff', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.staff.full_name} - {self.date}'


class StaffAnnouncement(models.Model):
    """STF-08: shared staff-only announcements board."""
    title = models.CharField(max_length=200)
    body = models.TextField()
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-pinned', '-posted_at']

    def __str__(self):
        return self.title


class StaffTicket(models.Model):
    """
    STF-09 (incident/observation reports) generalised into a single
    ticket model shared by every 'report something to admin' workflow:
    security incidents, maintenance/groundskeeper jobs, ICT support
    tickets, and lab-technician equipment/safety reports (STF-38, 53, 59,
    63, 72, 74). Rather than four near-identical bespoke models, one
    ticket type differentiates the workflow while sharing status,
    assignment, and photo-attachment handling. A role that grows enough
    ticket-specific fields to outgrow this (e.g. Librarian's fines,
    Security's visitor log) gets its own dedicated model instead - see
    `Book`/`BookLoan` and `VisitorLog`/`GatePass` below for that pattern.
    """
    class TicketType(models.TextChoices):
        INCIDENT = 'incident', 'General Incident/Observation'
        MAINTENANCE = 'maintenance', 'Maintenance Request'
        ICT = 'ict', 'ICT Support'
        LAB_SAFETY = 'lab_safety', 'Lab Safety/Equipment'
        SECURITY = 'security', 'Security Incident'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'

    ticket_type = models.CharField(max_length=15, choices=TicketType.choices, default=TicketType.INCIDENT)
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='tickets_raised',
    )
    assigned_to = models.ForeignKey(
        StaffMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_assigned',
    )
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    photo = models.ImageField(upload_to='staff_tickets/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_ticket_type_display()}] {self.description[:50]}'


class Payslip(models.Model):
    """
    STF-05: minimal payslip record so staff have something to view/
    download. Deliberately NOT a full payroll engine (PAYE bands,
    pension, statutory deductions) - that's the same Part B 'finance'
    scope already deferred in the fees/payments round. This just stores
    a computed gross/deductions/net per month so `Payslip` PDFs work
    today; wire in real payroll rules here when that module is built.
    """
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='payslips')
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('staff', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f'{self.staff.full_name} - {self.month}/{self.year}'


# ============================================================
# Librarian portal (STF-21 to STF-28)
# ============================================================

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    isbn = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    total_copies = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f'{self.title} - {self.author}'

    @property
    def copies_on_loan(self):
        return self.loans.filter(returned_date__isnull=True).count()

    @property
    def copies_available(self):
        return self.total_copies - self.copies_on_loan


class BookLoan(models.Model):
    """STF-22/23/25: issue/return + overdue fines. Borrower can be a
    student or a staff member (STF-24: students auto-enrolled, staff
    opt-in) - exactly one of the two should be set."""
    FINE_PER_DAY = 100  # MK, flat rate for the prototype

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, null=True, blank=True, related_name='book_loans')
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, null=True, blank=True, related_name='book_loans')
    issued_date = models.DateField(default=datetime.date.today)
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    is_lost = models.BooleanField(default=False)
    fine_paid = models.BooleanField(default=False)
    issued_by = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, related_name='loans_issued')

    class Meta:
        ordering = ['-issued_date']

    def __str__(self):
        borrower = self.student.full_name if self.student else (self.staff.full_name if self.staff else 'Unknown')
        return f'{self.book.title} -> {borrower}'

    @property
    def borrower_name(self):
        return self.student.full_name if self.student else (self.staff.full_name if self.staff else 'Unknown')

    @property
    def is_overdue(self):
        return not self.returned_date and datetime.date.today() > self.due_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (datetime.date.today() - self.due_date).days

    @property
    def fine_amount(self):
        end = self.returned_date or datetime.date.today()
        overdue_days = max((end - self.due_date).days, 0)
        return overdue_days * self.FINE_PER_DAY


# ============================================================
# Security portal (STF-36 to STF-42)
# ============================================================

class VisitorLog(models.Model):
    name = models.CharField(max_length=150)
    id_number = models.CharField(max_length=50, blank=True)
    purpose = models.CharField(max_length=200)
    host = models.CharField(max_length=150, blank=True, help_text='Who they are visiting.')
    vehicle_plate = models.CharField(max_length=20, blank=True)
    time_in = models.DateTimeField(default=timezone.now)
    time_out = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-time_in']

    def __str__(self):
        return f'{self.name} - {self.time_in:%Y-%m-%d %H:%M}'


class GatePass(models.Model):
    """STF-37/40: students leaving early, or day/boarder movement."""
    class Status(models.TextChoices):
        ISSUED = 'issued', 'Issued'
        OUT = 'out', 'Out'
        RETURNED = 'returned', 'Returned'

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='gate_passes')
    reason = models.CharField(max_length=200)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='gate_passes_approved',
    )
    issued_by = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, related_name='gate_passes_issued')
    time_out = models.DateTimeField(null=True, blank=True)
    time_in = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ISSUED)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'{self.student.full_name} - {self.reason} ({self.status})'


class PatrolLog(models.Model):
    guard = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='patrol_logs')
    checkpoint = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.guard.full_name} @ {self.checkpoint} ({self.timestamp:%H:%M})'


# ============================================================
# Nurse / Matron portal (STF-43 to STF-51)
# ============================================================

class MedicalRecord(models.Model):
    """STF-44: one per student - allergies/chronic conditions/immunisations."""
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='medical_record')
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    immunisation_notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Medical record - {self.student.full_name}'


class SickBayVisit(models.Model):
    """STF-43/45/47: sick bay visit; referral triggers a parent notification."""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='sickbay_visits')
    nurse = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, related_name='sickbay_visits_handled')
    visit_date = models.DateTimeField(auto_now_add=True)
    symptoms = models.TextField()
    treatment = models.TextField(blank=True)
    medicine_dispensed = models.CharField(max_length=200, blank=True)
    referred = models.BooleanField(default=False)
    referral_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f'{self.student.full_name} - {self.visit_date:%Y-%m-%d}'


class MedicationStock(models.Model):
    """STF-46/49: medication + first aid supply stock with reorder alerts."""
    name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.quantity} in stock)'

    @property
    def needs_reorder(self):
        return self.quantity <= self.reorder_level
