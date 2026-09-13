from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from accounts.mixins import RoleRequiredMixin
from .models import StaffMember


class StaffListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = StaffMember
    template_name = 'staff/staff_list.html'
    context_object_name = 'staff_members'
    allowed_roles = ['admin', 'staff']
