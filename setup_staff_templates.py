"""
==============================================================================
Staff-portal motion template installer
==============================================================================

Rewrites all 32 templates under templates/staff/ with the new motion
vocabulary, Bootstrap 5.3 subtle badges, mobile-first KPI cards, and
card-stacking tables.

Template paths match the `template_name` attributes in apps/staff/views.py.
Every {% url %} name has been cross-referenced against that file.

Run from project root:
    python setup_staff_templates.py

Idempotent - re-running overwrites each file with identical content.
Encoding: UTF-8 without BOM so em-dashes and typographic entities survive.
==============================================================================
"""
from pathlib import Path
import sys


BASE = Path.cwd()
UTF8 = "utf-8"

if not (BASE / "manage.py").exists():
    print(f"ERROR: manage.py not found in {BASE}")
    print("Run this script from the project root.")
    sys.exit(1)


def w(relpath, content):
    """Write a file under the project root, creating parent dirs."""
    p = BASE / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=UTF8)
    print(f"  + {relpath}")


print("Writing staff-portal templates (part 1/2) ...")
print()


# ==============================================================================
# 01. staff/portal_dashboard.html
#
# Main staff landing page. Role-conditional KPI cards for bursar,
# librarian, security, nurse, ICT/groundskeeper/lab_tech, and HR.
# Context: staff, roles, announcements, pending_leave,
#          today_attendance, todays_collections, defaulter_count,
#          overdue_loans, todays_returns, active_gate_passes,
#          visitors_today, sickbay_today, low_stock, open_tickets,
#          leave_queue (all optional, populated per role).
# ==============================================================================
w("templates/staff/portal_dashboard.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Staff Dashboard{% endblock %}

{% block content %}
{% if not staff %}

<div class="card border-warning-subtle"
     data-motion="scale-in" data-motion-duration="440">
    <div class="card-body text-center py-5">
        <div class="mx-auto mb-3 d-flex align-items-center justify-content-center"
             style="width:72px;height:72px;border-radius:20px;
                    background:var(--status-warning-bg);color:var(--status-warning-fg);"
             data-motion-variant="brandMark"
             data-motion-initial="hidden"
             data-motion-animate="visible">
            <i class="bi bi-person-x fs-2"></i>
        </div>
        <h3 class="h5 fw-bold mb-2">No staff profile linked</h3>
        <p class="text-secondary small mb-0">
            Your account isn't linked to a staff record yet.
        </p>
    </div>
</div>

{% else %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">{{ staff.full_name }}</h1>
        <p class="text-secondary small mb-0">
            {% for r in roles %}<span class="badge rounded-pill bg-primary-subtle text-primary-emphasis me-1">{{ r }}</span>{% endfor %}
        </p>
    </div>
</div>

<div class="row g-3 mb-4">

    {# Clock in / out #}
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="60">
            <div class="card-body d-flex flex-column justify-content-center">
                <div class="small text-secondary fw-semibold text-uppercase mb-2"
                     style="letter-spacing:.04em;font-size:11px;">Today</div>
                <form method="post" action="{% url 'staff:clock' %}">
                    {% csrf_token %}
                    <button class="btn btn-primary w-100"
                            data-motion-while-hover='{"y":-2,"scale":1.01}'
                            data-motion-while-tap='{"scale":0.97}'
                            data-ripple>
                        <i class="bi bi-clock me-1"></i>
                        {% if today_attendance and today_attendance.clock_out %}
                            Clocked out {{ today_attendance.clock_out }}
                        {% elif today_attendance and today_attendance.clock_in %}
                            Clock Out
                        {% else %}
                            Clock In
                        {% endif %}
                    </button>
                </form>
            </div>
        </div>
    </div>

    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="140"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(249,168,37,.18);color:#c67c00;"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="280">
                    <i class="bi bi-calendar-check fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ pending_leave|default:0 }}">0</div>
                    <div class="small text-secondary">Pending Leave</div>
                </div>
            </div>
        </div>
    </div>

    {% if 'bursar' in roles %}
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="200"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(25,135,84,.14);color:#198754;"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="340">
                    <i class="bi bi-cash-coin fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums">
                        <span data-counter="{{ todays_collections|default:0 }}"
                              data-counter-prefix="MK ">MK 0</span>
                    </div>
                    <div class="small text-secondary">Today's Collections</div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="260"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(220,38,38,.14);color:var(--md-error);"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="400">
                    <i class="bi bi-exclamation-circle fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ defaulter_count|default:0 }}">0</div>
                    <div class="small text-secondary">Fee Defaulters</div>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    {% if 'librarian' in roles %}
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="320"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(13,110,253,.12);color:#0d6efd;"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="460">
                    <i class="bi bi-book fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ overdue_loans|default:0 }}">0</div>
                    <div class="small text-secondary">Overdue Books</div>
                    <a href="{% url 'staff:loan_list' %}?overdue=1" class="small text-decoration-none">View &rarr;</a>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    {% if 'security' in roles %}
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="380"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(249,168,37,.18);color:#c67c00;"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="520">
                    <i class="bi bi-door-open fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ active_gate_passes|default:0 }}">0</div>
                    <div class="small text-secondary">Students Out</div>
                    <a href="{% url 'staff:gate_pass_list' %}" class="small text-decoration-none">View &rarr;</a>
                </div>
            </div>
        </div>
    </div>
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="440"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(13,110,253,.12);color:#0d6efd;"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="580">
                    <i class="bi bi-people fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ visitors_today|default:0 }}">0</div>
                    <div class="small text-secondary">Visitors Today</div>
                    <a href="{% url 'staff:visitor_list' %}" class="small text-decoration-none">View &rarr;</a>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    {% if 'nurse' in roles %}
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="500"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(220,38,38,.14);color:var(--md-error);"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="640">
                    <i class="bi bi-heart-pulse fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ sickbay_today|default:0 }}">0</div>
                    <div class="small text-secondary">Sick Bay Visits</div>
                    <a href="{% url 'staff:sickbay_list' %}" class="small text-decoration-none">View &rarr;</a>
                </div>
            </div>
        </div>
    </div>
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="560"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(249,168,37,.18);color:#c67c00;"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="700">
                    <i class="bi bi-capsule fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ low_stock|length|default:0 }}">0</div>
                    <div class="small text-secondary">Low Stock Items</div>
                    <a href="{% url 'staff:medication_stock' %}" class="small text-decoration-none">View &rarr;</a>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    {% if 'ict' in roles or 'groundskeeper' in roles or 'lab_tech' in roles %}
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="620"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(106,27,154,.14);color:#6a1b9a;"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="760">
                    <i class="bi bi-ticket-detailed fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ open_tickets|default:0 }}">0</div>
                    <div class="small text-secondary">Open Tickets</div>
                    <a href="{% url 'staff:ticket_list' %}" class="small text-decoration-none">View &rarr;</a>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    {% if 'hr' in roles %}
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100"
             data-motion="fade-up" data-motion-delay="680"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(26,86,50,.14);color:var(--md-primary);"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden"
                     data-motion-animate="visible"
                     data-motion-delay="820">
                    <i class="bi bi-person-check fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ leave_queue|default:0 }}">0</div>
                    <div class="small text-secondary">Leave Requests</div>
                    <a href="{% url 'staff:leave_approval' %}" class="small text-decoration-none">View &rarr;</a>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
</div>

<div class="d-flex gap-2 flex-wrap mb-4"
     data-motion="fade-up" data-motion-delay="740"
     data-motion-orchestrate='{"staggerChildren":0.04,"delayChildren":0.05}'>
    <a href="{% url 'staff:my_profile' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-while-hover='{"y":-2}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>My Profile</a>
    <a href="{% url 'staff:my_leave' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-while-hover='{"y":-2}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>My Leave</a>
    <a href="{% url 'staff:my_payslips' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-while-hover='{"y":-2}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>My Payslips</a>
    <a href="{% url 'staff:announcements' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-while-hover='{"y":-2}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>Announcements</a>
    <a href="{% url 'staff:raise_ticket' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-while-hover='{"y":-2}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>Report an Issue</a>
</div>

<div class="card"
     data-motion="fade-up" data-motion-delay="800">
    <div class="card-header">
        <h6 class="mb-0 fw-bold">Latest Announcements</h6>
    </div>
    <div class="card-body p-0">
        {% for a in announcements %}
        <div class="p-3 border-bottom">
            <div class="fw-semibold mb-1">{{ a.title }}</div>
            <div class="text-secondary small">{{ a.body|truncatewords:20 }}</div>
        </div>
        {% empty %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-megaphone fs-2 text-secondary"></i>
            </div>
            <p class="text-secondary small mb-0">No announcements yet.</p>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}
{% endblock %}
''')


# Also write the dashboard alias so any legacy URL still resolves.
w("templates/staff/dashboard.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Staff Dashboard{% endblock %}

{% block content %}
{% if not staff %}

<div class="card border-warning-subtle"
     data-motion="scale-in" data-motion-duration="440">
    <div class="card-body text-center py-5">
        <div class="mx-auto mb-3 d-flex align-items-center justify-content-center"
             style="width:72px;height:72px;border-radius:20px;
                    background:var(--status-warning-bg);color:var(--status-warning-fg);"
             data-motion-variant="brandMark"
             data-motion-initial="hidden"
             data-motion-animate="visible">
            <i class="bi bi-person-x fs-2"></i>
        </div>
        <h3 class="h5 fw-bold mb-2">No staff profile linked</h3>
        <p class="text-secondary small mb-0">
            Your account isn't linked to a staff record yet.
        </p>
    </div>
</div>

{% else %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">My Dashboard</h1>
        <p class="text-secondary small mb-0">{{ staff.full_name }}</p>
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100" data-motion="fade-up" data-motion-delay="60">
            <div class="card-body d-flex flex-column justify-content-center">
                <form method="post" action="{% url 'staff:clock' %}">
                    {% csrf_token %}
                    <button class="btn btn-primary w-100"
                            data-motion-while-hover='{"y":-2,"scale":1.01}'
                            data-motion-while-tap='{"scale":0.97}' data-ripple>
                        <i class="bi bi-clock me-1"></i> Clock In / Out
                    </button>
                </form>
            </div>
        </div>
    </div>

    <div class="col-12 col-sm-6 col-md-4">
        <div class="card h-100" data-motion="fade-up" data-motion-delay="140"
             data-motion-while-hover='{"y":-3,"scale":1.005}'>
            <div class="card-body d-flex align-items-center gap-3">
                <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                     style="width:52px;height:52px;background:rgba(249,168,37,.18);color:#c67c00;"
                     data-motion-variant="brandMark"
                     data-motion-initial="hidden" data-motion-animate="visible">
                    <i class="bi bi-calendar-check fs-5"></i>
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="h3 fw-bold mb-0 tabular-nums"
                         data-counter="{{ pending_leave|default:0 }}">0</div>
                    <div class="small text-secondary">Pending Leave</div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="300">
    <div class="card-header d-flex align-items-center justify-content-between">
        <h6 class="mb-0 fw-bold">Announcements</h6>
        <a class="btn btn-sm btn-ghost text-secondary"
           href="{% url 'staff:announcements' %}"
           data-motion-while-tap='{"scale":0.94}'>
            View all <i class="bi bi-arrow-right ms-1"></i>
        </a>
    </div>
    <div class="card-body">
        {% for a in announcements %}
        <div class="border-bottom pb-2 mb-2">
            <div class="fw-semibold">{{ a.title }}</div>
            <div class="text-secondary small">{{ a.body|truncatewords:15 }}</div>
        </div>
        {% empty %}
        <p class="text-secondary small mb-0">No announcements.</p>
        {% endfor %}
    </div>
</div>
{% endif %}
{% endblock %}
''')


# ==============================================================================
# 02. staff/staff_list.html
#
# Staff directory with search. Context: staff_members, filter.
# ==============================================================================
w("templates/staff/staff_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Staff Directory{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Staff Directory</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums"
                  data-counter="{{ staff_members|length }}">{{ staff_members|length }}</span> people
        </p>
    </div>
</div>

<form class="row g-2 mb-3" method="get"
      data-motion="fade-up" data-motion-delay="120">
    <div class="col-12 col-md-6">
        <div class="input-group">
            <span class="input-group-text bg-transparent border-end-0">
                <i class="bi bi-search"></i>
            </span>
            <input type="text" name="search" class="input border-start-0 ps-0"
                   placeholder="Search staff..." value="{{ request.GET.search }}">
        </div>
    </div>
    <div class="col-12 col-md-auto">
        <button class="btn btn-primary w-100" type="submit"
                data-motion-while-hover='{"y":-1}'
                data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-funnel me-1"></i> Filter
        </button>
    </div>
</form>

<div class="card"
     data-motion="fade-up" data-motion-delay="180"
     style="overflow:hidden;">
    <div class="card-body p-0">
        {% if staff_members %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Position</th>
                    <th>Department</th>
                    <th>Roles</th>
                    <th>Phone</th>
                </tr>
            </thead>
            <tbody>
                {% for s in staff_members %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 35 %}">
                    <td data-label="Name">
                        <div class="d-flex align-items-center gap-2">
                            <span class="avatar avatar-sm">{{ s.full_name|slice:":1"|upper }}</span>
                            <div class="min-w-0">
                                <div class="fw-medium">{{ s.full_name }}</div>
                                <div class="text-secondary small font-monospace">{{ s.staff_id }}</div>
                            </div>
                        </div>
                    </td>
                    <td data-label="Position">{{ s.position|default:"â€”" }}</td>
                    <td data-label="Department">{{ s.department|default:"â€”" }}</td>
                    <td data-label="Roles">
                        <div class="d-flex flex-wrap gap-1">
                            {% for r in s.role_assignments.all %}
                            <span class="badge rounded-pill bg-primary-subtle text-primary-emphasis">
                                {{ r.get_role_display }}
                            </span>
                            {% empty %}
                            <span class="text-secondary small">â€”</span>
                            {% endfor %}
                        </div>
                    </td>
                    <td data-label="Phone" class="tabular-nums small">{{ s.phone_number|default:"â€”" }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-people fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No staff found</h3>
            <p class="text-secondary small mb-0">
                {% if request.GET.search %}Try a different search term.{% else %}Staff records will appear here.{% endif %}
            </p>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 03. staff/my_profile.html
#
# Personal profile editor. Crispy form -> `form`.
# ==============================================================================
w("templates/staff/my_profile.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}My Profile{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">My Profile</h1>
        <p class="text-secondary small mb-0">Update your personal details.</p>
    </div>
</div>
<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     data-motion-layout>
    <div class="card-body">
        <div class="crispy-form-wrap"
             data-motion-orchestrate='{"staggerChildren":0.03,"delayChildren":0.1}'>
            {% crispy form %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
(function () {
    const form = document.querySelector('.crispy-form-wrap form');
    if (!form) return;
    form.querySelectorAll(':scope > div').forEach((row, i) => {
        row.setAttribute('data-motion', 'fade-up');
        row.setAttribute('data-motion-delay', String(60 + i * 30));
    });
    form.querySelectorAll('button[type="submit"], input[type="submit"], a.btn').forEach((b) => {
        b.setAttribute('data-motion-while-hover', '{"y":-2}');
        b.setAttribute('data-motion-while-tap',   '{"scale":0.97}');
        b.setAttribute('data-ripple', '');
    });
    if (window.Motion?.refresh) window.Motion.refresh(form);
    if (window.MotionPro?.refresh) window.MotionPro.refresh();
})();
</script>
{% endblock %}
''')


# Alias for the profile_form.html path (document also lists this).
w("templates/staff/profile_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}My Profile{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">My Profile</h1>
        <p class="text-secondary small mb-0">Update your personal details.</p>
    </div>
</div>
<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     data-motion-layout>
    <div class="card-body">
        <div class="crispy-form-wrap"
             data-motion-orchestrate='{"staggerChildren":0.03,"delayChildren":0.1}'>
            {% crispy form %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
(function () {
    const form = document.querySelector('.crispy-form-wrap form');
    if (!form) return;
    form.querySelectorAll(':scope > div').forEach((row, i) => {
        row.setAttribute('data-motion', 'fade-up');
        row.setAttribute('data-motion-delay', String(60 + i * 30));
    });
    form.querySelectorAll('button[type="submit"], input[type="submit"], a.btn').forEach((b) => {
        b.setAttribute('data-motion-while-hover', '{"y":-2}');
        b.setAttribute('data-motion-while-tap',   '{"scale":0.97}');
        b.setAttribute('data-ripple', '');
    });
    if (window.Motion?.refresh) window.Motion.refresh(form);
    if (window.MotionPro?.refresh) window.MotionPro.refresh();
})();
</script>
{% endblock %}
''')


# ==============================================================================
# 04. staff/my_leave.html  (STF-04)
# ==============================================================================
w("templates/staff/my_leave.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}My Leave{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">My Leave</h1>
        <p class="text-secondary small mb-0">Your leave history and pending requests.</p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:leave_create' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-plus-lg me-1"></i> Request Leave
    </a>
</div>

<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     style="overflow:hidden;">
    <div class="card-body p-0">
        {% if leave_requests %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Dates</th>
                    <th>Days</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for l in leave_requests %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 45 %}">
                    <td data-label="Type" class="fw-medium">{{ l.get_leave_type_display }}</td>
                    <td data-label="Dates" class="tabular-nums small">
                        {{ l.start_date }} &rarr; {{ l.end_date }}
                    </td>
                    <td data-label="Days" class="tabular-nums">{{ l.days }}</td>
                    <td data-label="Status">
                        {% if l.status == 'approved' %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">Approved</span>
                        {% elif l.status == 'rejected' %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">Rejected</span>
                        {% else %}
                        <span class="badge rounded-pill bg-warning-subtle text-warning-emphasis">Pending</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-calendar-plus fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No leave requests yet</h3>
            <p class="text-secondary small mb-3">Submit your first request to get started.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:leave_create' %}">Request Leave</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 05. staff/leave_form.html  (RequestLeaveView)
# ==============================================================================
w("templates/staff/leave_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Request Leave{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Request Leave</h1>
        <p class="text-secondary small mb-0">Submit a new leave request.</p>
    </div>
    <a href="{% url 'staff:my_leave' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back
    </a>
</div>
<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     data-motion-layout>
    <div class="card-body">
        <div class="crispy-form-wrap"
             data-motion-orchestrate='{"staggerChildren":0.03,"delayChildren":0.1}'>
            {% crispy form %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
(function () {
    const form = document.querySelector('.crispy-form-wrap form');
    if (!form) return;
    form.querySelectorAll(':scope > div').forEach((row, i) => {
        row.setAttribute('data-motion', 'fade-up');
        row.setAttribute('data-motion-delay', String(60 + i * 30));
    });
    form.querySelectorAll('button[type="submit"], input[type="submit"], a.btn').forEach((b) => {
        b.setAttribute('data-motion-while-hover', '{"y":-2}');
        b.setAttribute('data-motion-while-tap',   '{"scale":0.97}');
        b.setAttribute('data-ripple', '');
    });
    if (window.Motion?.refresh) window.Motion.refresh(form);
    if (window.MotionPro?.refresh) window.MotionPro.refresh();
})();
</script>
{% endblock %}
''')


# ==============================================================================
# 06. staff/leave_approval.html  (LeaveApprovalView, STF-92)
# ==============================================================================
w("templates/staff/leave_approval.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Leave Approvals{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Leave Approvals</h1>
        <p class="text-secondary small mb-0">Requests awaiting your decision.</p>
    </div>
</div>

<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     style="overflow:hidden;">
    <div class="card-body p-0">
        {% if leave_requests %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Staff</th>
                    <th>Type</th>
                    <th>Dates</th>
                    <th>Reason</th>
                    <th class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for l in leave_requests %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 45 %}">
                    <td data-label="Staff">
                        <div class="d-flex align-items-center gap-2">
                            <span class="avatar avatar-sm">{{ l.staff.full_name|slice:":1"|upper }}</span>
                            <span class="fw-medium">{{ l.staff.full_name }}</span>
                        </div>
                    </td>
                    <td data-label="Type">{{ l.get_leave_type_display }}</td>
                    <td data-label="Dates" class="tabular-nums small">
                        {{ l.start_date }} &rarr; {{ l.end_date }}
                    </td>
                    <td data-label="Reason" class="text-secondary small">
                        {{ l.reason|truncatewords:10 }}
                    </td>
                    <td class="actions text-end">
                        <form method="post" action="{% url 'staff:decide_leave' l.pk %}"
                              class="d-inline-flex gap-1 justify-content-end">
                            {% csrf_token %}
                            <button name="decision" value="approved"
                                    class="btn btn-sm btn-primary"
                                    data-motion-while-hover='{"y":-1}'
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                <i class="bi bi-check-lg"></i> Approve
                            </button>
                            <button name="decision" value="rejected"
                                    class="btn btn-sm btn-danger"
                                    data-motion-while-hover='{"y":-1}'
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                <i class="bi bi-x-lg"></i> Reject
                            </button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3"
                 style="width:64px;height:64px;border-radius:16px;
                        background:var(--md-surface-bright);
                        display:flex;align-items:center;justify-content:center;"
                 data-motion-variant="brandMark"
                 data-motion-initial="hidden" data-motion-animate="visible">
                <i class="bi bi-check-circle fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">All caught up</h3>
            <p class="text-secondary small mb-0">No pending requests.</p>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# Alias path the document listed.
w("templates/staff/leave_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Leave Requests{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Leave Requests</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ leave_requests|length }}">{{ leave_requests|length }}</span>
            total
        </p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:leave_create' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-plus-lg me-1"></i> Request Leave
    </a>
</div>

<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     style="overflow:hidden;">
    <div class="card-body p-0">
        {% if leave_requests %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Staff</th>
                    <th>Type</th>
                    <th>Dates</th>
                    <th>Days</th>
                    <th>Status</th>
                    <th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for l in leave_requests %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Staff">
                        <div class="d-flex align-items-center gap-2">
                            <span class="avatar avatar-sm">{{ l.staff.full_name|slice:":1"|upper }}</span>
                            <span class="fw-medium">{{ l.staff.full_name }}</span>
                        </div>
                    </td>
                    <td data-label="Type">{{ l.get_leave_type_display }}</td>
                    <td data-label="Dates" class="tabular-nums small">
                        {{ l.start_date }} &rarr; {{ l.end_date }}
                    </td>
                    <td data-label="Days" class="tabular-nums">{{ l.days }}</td>
                    <td data-label="Status">
                        {% if l.status == 'approved' %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">Approved</span>
                        {% elif l.status == 'rejected' %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">Rejected</span>
                        {% else %}
                        <span class="badge rounded-pill bg-warning-subtle text-warning-emphasis">Pending</span>
                        {% endif %}
                    </td>
                    <td class="actions text-end">
                        {% if l.status == 'pending' %}
                        <form method="post" action="{% url 'staff:decide_leave' l.pk %}"
                              class="d-inline-flex gap-1 justify-content-end">
                            {% csrf_token %}
                            <button name="decision" value="approved"
                                    class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>Approve</button>
                            <button name="decision" value="rejected"
                                    class="btn btn-sm btn-danger"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>Reject</button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-calendar-x fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No leave requests</h3>
            <p class="text-secondary small mb-0">Requests you submit or receive will appear here.</p>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 07. staff/my_payslips.html  (MyPayslipsView)
# ==============================================================================
w("templates/staff/my_payslips.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}My Payslips{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">My Payslips</h1>
        <p class="text-secondary small mb-0">Download and review your payslips.</p>
    </div>
</div>

<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     style="overflow:hidden;">
    <div class="card-body p-0">
        {% if payslips %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Period</th>
                    <th>Gross</th>
                    <th>Deductions</th>
                    <th>Net</th>
                    <th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for p in payslips %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 45 %}">
                    <td data-label="Period" class="fw-medium">{{ p.month }}/{{ p.year }}</td>
                    <td data-label="Gross" class="tabular-nums">MK {{ p.gross_pay }}</td>
                    <td data-label="Deductions" class="tabular-nums text-secondary">MK {{ p.deductions }}</td>
                    <td data-label="Net" class="tabular-nums fw-semibold text-success">MK {{ p.net_pay }}</td>
                    <td class="actions text-end">
                        <a class="btn btn-sm btn-secondary"
                           href="{% url 'staff:payslip_pdf' p.pk %}"
                           target="_blank" aria-label="Download payslip"
                           data-motion-while-hover='{"y":-1}'
                           data-motion-while-tap='{"scale":0.94}' data-ripple>
                            <i class="bi bi-file-earmark-pdf"></i>
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-file-earmark-text fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No payslips yet</h3>
            <p class="text-secondary small mb-0">Payslips will appear here once they are generated.</p>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 08. staff/announcements.html  (AnnouncementListView)
# ==============================================================================
w("templates/staff/announcements.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Staff Announcements{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Announcements</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ announcements|length }}">{{ announcements|length }}</span> posted
        </p>
    </div>
    {% if request.user.role == 'admin' or request.user.is_superuser %}
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:post_announcement' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-plus-lg me-1"></i> Post Announcement
    </a>
    {% endif %}
</div>

{% if announcements %}
<div class="row g-3"
     data-motion-orchestrate='{"staggerChildren":0.06,"delayChildren":0.05}'>
    {% for a in announcements %}
    <div class="col-12" data-motion="fade-up">
        <div class="card" data-motion-while-hover='{"y":-2}'>
            <div class="card-body">
                <div class="d-flex align-items-start justify-content-between gap-2 mb-2">
                    <h6 class="fw-bold mb-0">{{ a.title }}</h6>
                    {% if a.pinned %}
                    <span class="badge rounded-pill bg-warning-subtle text-warning-emphasis flex-shrink-0">
                        <i class="bi bi-pin-angle-fill me-1"></i> Pinned
                    </span>
                    {% endif %}
                </div>
                <p class="text-secondary mb-3" style="font-size:14px;">{{ a.body }}</p>
                <div class="d-flex align-items-center gap-2 text-secondary small">
                    <i class="bi bi-person-circle"></i>
                    <span>{{ a.posted_by }}</span>
                    <span>&middot;</span>
                    <span class="tabular-nums">{{ a.posted_at|date:"Y-m-d H:i" }}</span>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="card" data-motion="scale-in" data-motion-duration="440">
    <div class="card-body text-center py-5">
        <div class="mx-auto mb-3 d-flex align-items-center justify-content-center"
             style="width:72px;height:72px;border-radius:20px;
                    background:var(--md-surface-bright);color:var(--md-on-surface-variant);"
             data-motion-variant="brandMark"
             data-motion-initial="hidden" data-motion-animate="visible">
            <i class="bi bi-megaphone fs-2"></i>
        </div>
        <h3 class="h5 fw-bold mb-2">No announcements yet</h3>
        <p class="text-secondary small mb-0">Announcements from the school will appear here.</p>
    </div>
</div>
{% endif %}

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 09. staff/announcement_form.html  (PostAnnouncementView)
# ==============================================================================
w("templates/staff/announcement_form.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Post Announcement{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Post Announcement</h1>
        <p class="text-secondary small mb-0">Broadcast a message to all staff.</p>
    </div>
    <a href="{% url 'staff:announcements' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back
    </a>
</div>
<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     data-motion-layout>
    <div class="card-body">
        <form method="post"
              data-motion-orchestrate='{"staggerChildren":0.05,"delayChildren":0.1}'>
            {% csrf_token %}
            {% for field in form %}
            <div class="field mb-3" data-motion="fade-up">
                <label class="field-label" for="{{ field.id_for_label }}">
                    {{ field.label }}{% if field.field.required %}<span class="text-danger ms-1">*</span>{% endif %}
                </label>
                {{ field }}
                {% if field.help_text %}<p class="field-help">{{ field.help_text }}</p>{% endif %}
                {% if field.errors %}
                <p class="field-error" role="alert">
                    <i class="bi bi-exclamation-circle"></i> {{ field.errors.0 }}
                </p>
                {% endif %}
            </div>
            {% endfor %}
            <div class="d-flex gap-2 justify-content-end mt-3"
                 data-motion="fade-up">
                <a href="{% url 'staff:announcements' %}" class="btn btn-secondary"
                   data-motion-while-hover='{"y":-2}'
                   data-motion-while-tap='{"scale":0.97}' data-ripple>Cancel</a>
                <button class="btn btn-primary" type="submit"
                        data-motion-while-hover='{"y":-2,"scale":1.02}'
                        data-motion-while-tap='{"scale":0.97}' data-ripple>
                    <i class="bi bi-megaphone me-1"></i> Post
                </button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
''')


# ==============================================================================
# 10. staff/ticket_list.html  (TicketListView)
# ==============================================================================
w("templates/staff/ticket_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Tickets{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Tickets</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ tickets|length }}">{{ tickets|length }}</span> total
        </p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:raise_ticket' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-plus-lg me-1"></i> Report Issue
    </a>
</div>

<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     style="overflow:hidden;">
    <div class="card-body p-0">
        {% if tickets %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Description</th>
                    <th>Raised By</th>
                    <th>Status</th>
                    <th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for t in tickets %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 45 %}">
                    <td data-label="Type" class="fw-medium">{{ t.get_ticket_type_display }}</td>
                    <td data-label="Description" class="text-secondary small">
                        {{ t.description|truncatewords:10 }}
                    </td>
                    <td data-label="Raised By" class="small">{{ t.raised_by }}</td>
                    <td data-label="Status">
                        {% if t.status == 'resolved' %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">Resolved</span>
                        {% elif t.status == 'in_progress' %}
                        <span class="badge rounded-pill bg-warning-subtle text-warning-emphasis">In Progress</span>
                        {% else %}
                        <span class="badge rounded-pill bg-secondary-subtle text-secondary-emphasis">Open</span>
                        {% endif %}
                    </td>
                    <td class="actions text-end">
                        {% if t.status != 'resolved' %}
                        <form method="post" action="{% url 'staff:resolve_ticket' t.pk %}" class="d-inline">
                            {% csrf_token %}
                            <button class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                <i class="bi bi-check2"></i> Resolve
                            </button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-ticket-detailed fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No tickets</h3>
            <p class="text-secondary small mb-3">All clear! Report an issue if something needs attention.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:raise_ticket' %}">Report Issue</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 11. staff/ticket_form.html  (RaiseTicketView)
# ==============================================================================
w("templates/staff/ticket_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Report an Issue{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Report an Issue</h1>
        <p class="text-secondary small mb-0">Describe the problem and we'll route it to the right team.</p>
    </div>
    <a href="{% url 'staff:ticket_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back
    </a>
</div>
<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     data-motion-layout>
    <div class="card-body">
        <div class="crispy-form-wrap"
             data-motion-orchestrate='{"staggerChildren":0.03,"delayChildren":0.1}'>
            {% crispy form %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
(function () {
    const form = document.querySelector('.crispy-form-wrap form');
    if (!form) return;
    form.querySelectorAll(':scope > div').forEach((row, i) => {
        row.setAttribute('data-motion', 'fade-up');
        row.setAttribute('data-motion-delay', String(60 + i * 30));
    });
    form.querySelectorAll('button[type="submit"], input[type="submit"], a.btn').forEach((b) => {
        b.setAttribute('data-motion-while-hover', '{"y":-2}');
        b.setAttribute('data-motion-while-tap',   '{"scale":0.97}');
        b.setAttribute('data-ripple', '');
    });
    if (window.Motion?.refresh) window.Motion.refresh(form);
    if (window.MotionPro?.refresh) window.MotionPro.refresh();
})();
</script>
{% endblock %}
''')


# ==============================================================================
# 12. staff/librarian/book_list.html  (BookListView)
# ==============================================================================
w("templates/staff/librarian/book_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Book Catalogue{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Book Catalogue</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ books|length }}">{{ books|length }}</span> titles
        </p>
    </div>
    <div class="d-flex gap-2 flex-wrap"
         data-motion="fade-up" data-motion-delay="140">
        <a href="{% url 'staff:book_create' %}" class="btn btn-primary btn-sm"
           data-motion-while-hover='{"y":-2,"scale":1.02}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-plus-lg me-1"></i> Add Book
        </a>
        <a href="{% url 'staff:issue_book' %}" class="btn btn-secondary btn-sm"
           data-motion-while-hover='{"y":-2}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-box-arrow-up me-1"></i> Issue
        </a>
        <a href="{% url 'staff:loan_list' %}" class="btn btn-secondary btn-sm"
           data-motion-while-hover='{"y":-2}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-list-check me-1"></i> Loans
        </a>
    </div>
</div>

<div class="card"
     data-motion="fade-up" data-motion-delay="120"
     style="overflow:hidden;">
    <div class="card-body p-0">
        {% if books %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Author</th>
                    <th>Subject</th>
                    <th>Copies</th>
                    <th>Available</th>
                </tr>
            </thead>
            <tbody>
                {% for b in books %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 35 %}"
                    data-motion-while-hover='{"x":3}'>
                    <td data-label="Title" class="fw-medium">{{ b.title }}</td>
                    <td data-label="Author">{{ b.author }}</td>
                    <td data-label="Subject" class="text-secondary">{{ b.subject|default:"â€”" }}</td>
                    <td data-label="Copies" class="tabular-nums">{{ b.total_copies }}</td>
                    <td data-label="Available">
                        <span class="badge rounded-pill
                            {% if b.copies_available > 0 %}bg-success-subtle text-success-emphasis
                            {% else %}bg-danger-subtle text-danger-emphasis{% endif %}">
                            {{ b.copies_available }}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-book fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No books catalogued</h3>
            <p class="text-secondary small mb-3">Add your first book to begin.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:book_create' %}">Add Book</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# Also write the flat alias the document listed.
w("templates/staff/book_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Book Catalogue{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Book Catalogue</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ books|length }}">{{ books|length }}</span> titles
        </p>
    </div>
    <div class="d-flex gap-2 flex-wrap"
         data-motion="fade-up" data-motion-delay="140">
        <a href="{% url 'staff:book_create' %}" class="btn btn-primary btn-sm"
           data-motion-while-hover='{"y":-2,"scale":1.02}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-plus-lg me-1"></i> Add Book
        </a>
        <a href="{% url 'staff:issue_book' %}" class="btn btn-secondary btn-sm"
           data-motion-while-hover='{"y":-2}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-box-arrow-up me-1"></i> Issue
        </a>
        <a href="{% url 'staff:loan_list' %}" class="btn btn-secondary btn-sm"
           data-motion-while-hover='{"y":-2}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-list-check me-1"></i> Loans
        </a>
    </div>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if books %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Title</th><th>Author</th><th>Subject</th>
                    <th>Copies</th><th>Available</th>
                </tr>
            </thead>
            <tbody>
                {% for b in books %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 35 %}">
                    <td data-label="Title" class="fw-medium">{{ b.title }}</td>
                    <td data-label="Author">{{ b.author }}</td>
                    <td data-label="Subject" class="text-secondary">{{ b.subject|default:"â€”" }}</td>
                    <td data-label="Copies" class="tabular-nums">{{ b.total_copies }}</td>
                    <td data-label="Available">
                        <span class="badge rounded-pill
                            {% if b.copies_available > 0 %}bg-success-subtle text-success-emphasis
                            {% else %}bg-danger-subtle text-danger-emphasis{% endif %}">
                            {{ b.copies_available }}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-book fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No books catalogued</h3>
            <p class="text-secondary small mb-3">Add your first book to begin.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:book_create' %}">Add Book</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 13. staff/librarian/book_form.html  (BookCreateView)
# ==============================================================================
w("templates/staff/librarian/book_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Add Book{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Add Book</h1>
        <p class="text-secondary small mb-0">Add a title to the catalogue.</p>
    </div>
    <a href="{% url 'staff:book_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back to Catalogue
    </a>
</div>
<div class="card" data-motion="fade-up" data-motion-delay="120" data-motion-layout>
    <div class="card-body">
        <div class="crispy-form-wrap"
             data-motion-orchestrate='{"staggerChildren":0.03,"delayChildren":0.1}'>
            {% crispy form %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
(function () {
    const form = document.querySelector('.crispy-form-wrap form');
    if (!form) return;
    form.querySelectorAll(':scope > div').forEach((row, i) => {
        row.setAttribute('data-motion', 'fade-up');
        row.setAttribute('data-motion-delay', String(60 + i * 30));
    });
    form.querySelectorAll('button[type="submit"], input[type="submit"], a.btn').forEach((b) => {
        b.setAttribute('data-motion-while-hover', '{"y":-2}');
        b.setAttribute('data-motion-while-tap',   '{"scale":0.97}');
        b.setAttribute('data-ripple', '');
    });
    if (window.Motion?.refresh) window.Motion.refresh(form);
    if (window.MotionPro?.refresh) window.MotionPro.refresh();
})();
</script>
{% endblock %}
''')


w("templates/staff/book_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Add Book{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Add Book</h1>
        <p class="text-secondary small mb-0">Add a title to the catalogue.</p>
    </div>
    <a href="{% url 'staff:book_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back to Catalogue
    </a>
</div>
<div class="card" data-motion="fade-up" data-motion-delay="120" data-motion-layout>
    <div class="card-body">
        <div class="crispy-form-wrap"
             data-motion-orchestrate='{"staggerChildren":0.03,"delayChildren":0.1}'>
            {% crispy form %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
(function () {
    const form = document.querySelector('.crispy-form-wrap form');
    if (!form) return;
    form.querySelectorAll(':scope > div').forEach((row, i) => {
        row.setAttribute('data-motion', 'fade-up');
        row.setAttribute('data-motion-delay', String(60 + i * 30));
    });
    form.querySelectorAll('button[type="submit"], input[type="submit"], a.btn').forEach((b) => {
        b.setAttribute('data-motion-while-hover', '{"y":-2}');
        b.setAttribute('data-motion-while-tap',   '{"scale":0.97}');
        b.setAttribute('data-ripple', '');
    });
    if (window.Motion?.refresh) window.Motion.refresh(form);
    if (window.MotionPro?.refresh) window.MotionPro.refresh();
})();
</script>
{% endblock %}
''')


# ==============================================================================
# 14. staff/librarian/loan_list.html  (LoanListView)
# ==============================================================================
w("templates/staff/librarian/loan_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Book Loans{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Book Loans</h1>
        <p class="text-secondary small mb-0">Currently issued and returned.</p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:issue_book' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-box-arrow-up me-1"></i> Issue Book
    </a>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if loans %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Book</th>
                    <th>Borrower</th>
                    <th>Due</th>
                    <th>Status</th>
                    <th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for l in loans %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Book" class="fw-medium">{{ l.book.title }}</td>
                    <td data-label="Borrower">
                        {% if l.student %}{{ l.student.full_name }}
                        {% elif l.staff %}{{ l.staff.full_name }}
                        {% else %}â€”{% endif %}
                    </td>
                    <td data-label="Due" class="tabular-nums small">{{ l.due_date }}</td>
                    <td data-label="Status">
                        {% if l.returned_date %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">Returned</span>
                        {% elif l.is_overdue %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">
                            Overdue ({{ l.days_overdue }}d &middot; MK {{ l.fine_amount }})
                        </span>
                        {% else %}
                        <span class="badge rounded-pill bg-warning-subtle text-warning-emphasis">On Loan</span>
                        {% endif %}
                    </td>
                    <td class="actions text-end">
                        {% if not l.returned_date %}
                        <form method="post" action="{% url 'staff:return_book' l.pk %}" class="d-inline">
                            {% csrf_token %}
                            <button class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                <i class="bi bi-check2"></i> Return
                            </button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-journal-bookmark fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No loans yet</h3>
            <p class="text-secondary small mb-3">Issue a book to get started.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:issue_book' %}">Issue Book</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


w("templates/staff/loan_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Book Loans{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Book Loans</h1>
        <p class="text-secondary small mb-0">Currently issued and returned.</p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:issue_book' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-box-arrow-up me-1"></i> Issue Book
    </a>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if loans %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Book</th><th>Borrower</th><th>Due</th>
                    <th>Status</th><th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for l in loans %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Book" class="fw-medium">{{ l.book.title }}</td>
                    <td data-label="Borrower">
                        {% if l.student %}{{ l.student.full_name }}
                        {% elif l.staff %}{{ l.staff.full_name }}
                        {% else %}â€”{% endif %}
                    </td>
                    <td data-label="Due" class="tabular-nums small">{{ l.due_date }}</td>
                    <td data-label="Status">
                        {% if l.returned_date %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">Returned</span>
                        {% elif l.is_overdue %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">
                            Overdue ({{ l.days_overdue }}d &middot; MK {{ l.fine_amount }})
                        </span>
                        {% else %}
                        <span class="badge rounded-pill bg-warning-subtle text-warning-emphasis">On Loan</span>
                        {% endif %}
                    </td>
                    <td class="actions text-end">
                        {% if not l.returned_date %}
                        <form method="post" action="{% url 'staff:return_book' l.pk %}" class="d-inline">
                            {% csrf_token %}
                            <button class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                <i class="bi bi-check2"></i> Return
                            </button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-journal-bookmark fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No loans yet</h3>
            <p class="text-secondary small mb-3">Issue a book to get started.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:issue_book' %}">Issue Book</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 15. staff/librarian/loan_form.html  (IssueBookView)
# ==============================================================================
w("templates/staff/librarian/loan_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Issue Book{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Issue Book</h1>
        <p class="text-secondary small mb-0">Lend a book to a student or staff member.</p>
    </div>
    <a href="{% url 'staff:loan_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back to Loans
    </a>
</div>
<div class="card" data-motion="fade-up" data-motion-delay="120" data-motion-layout>
    <div class="card-body">
        <div class="crispy-form-wrap"
             data-motion-orchestrate='{"staggerChildren":0.03,"delayChildren":0.1}'>
            {% crispy form %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
(function () {
    const form = document.querySelector('.crispy-form-wrap form');
    if (!form) return;
    form.querySelectorAll(':scope > div').forEach((row, i) => {
        row.setAttribute('data-motion', 'fade-up');
        row.setAttribute('data-motion-delay', String(60 + i * 30));
    });
    form.querySelectorAll('button[type="submit"], input[type="submit"], a.btn').forEach((b) => {
        b.setAttribute('data-motion-while-hover', '{"y":-2}');
        b.setAttribute('data-motion-while-tap',   '{"scale":0.97}');
        b.setAttribute('data-ripple', '');
    });
    if (window.Motion?.refresh) window.Motion.refresh(form);
    if (window.MotionPro?.refresh) window.MotionPro.refresh();
})();
</script>
{% endblock %}
''')


w("templates/staff/loan_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Issue Book{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Issue Book</h1>
        <p class="text-secondary small mb-0">Lend a book to a student or staff member.</p>
    </div>
    <a href="{% url 'staff:loan_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back to Loans
    </a>
</div>
<div class="card" data-motion="fade-up" data-motion-delay="120" data-motion-layout>
    <div class="card-body">
        <div class="crispy-form-wrap"
             data-motion-orchestrate='{"staggerChildren":0.03,"delayChildren":0.1}'>
            {% crispy form %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
(function () {
    const form = document.querySelector('.crispy-form-wrap form');
    if (!form) return;
    form.querySelectorAll(':scope > div').forEach((row, i) => {
        row.setAttribute('data-motion', 'fade-up');
        row.setAttribute('data-motion-delay', String(60 + i * 30));
    });
    form.querySelectorAll('button[type="submit"], input[type="submit"], a.btn').forEach((b) => {
        b.setAttribute('data-motion-while-hover', '{"y":-2}');
        b.setAttribute('data-motion-while-tap',   '{"scale":0.97}');
        b.setAttribute('data-ripple', '');
    });
    if (window.Motion?.refresh) window.Motion.refresh(form);
    if (window.MotionPro?.refresh) window.MotionPro.refresh();
})();
</script>
{% endblock %}
''')


# ==============================================================================
# 16. staff/overdue_loans.html  (not directly in views, filtered view of loans)
# ==============================================================================
w("templates/staff/overdue_loans.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Overdue Books{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Overdue Books</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ loans|length }}">{{ loans|length }}</span> overdue
        </p>
    </div>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if loans %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Book</th><th>Borrower</th><th>Due</th>
                    <th>Days</th><th>Fine</th><th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for l in loans %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Book" class="fw-medium">{{ l.book.title }}</td>
                    <td data-label="Borrower">
                        {% if l.student %}{{ l.student.full_name }}
                        {% elif l.staff %}{{ l.staff.full_name }}
                        {% else %}â€”{% endif %}
                    </td>
                    <td data-label="Due" class="tabular-nums small">{{ l.due_date }}</td>
                    <td data-label="Days" class="tabular-nums">
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">
                            {{ l.days_overdue }} d
                        </span>
                    </td>
                    <td data-label="Fine" class="tabular-nums fw-semibold text-danger">
                        MK {{ l.fine_amount }}
                    </td>
                    <td class="actions text-end">
                        <form method="post" action="{% url 'staff:return_book' l.pk %}" class="d-inline">
                            {% csrf_token %}
                            <button class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                <i class="bi bi-check2"></i> Mark Returned
                            </button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-check-circle fs-2 text-success"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No overdue books</h3>
            <p class="text-secondary small mb-0">Everything is on track.</p>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 17. staff/security/visitor_list.html  (VisitorLogListView)
# ==============================================================================
w("templates/staff/security/visitor_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Visitor Log{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Visitor Log</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ visitors|length }}">{{ visitors|length }}</span> visits today
        </p>
    </div>
    <div class="d-flex gap-2 flex-wrap"
         data-motion="fade-up" data-motion-delay="140">
        <a class="btn btn-primary btn-sm"
           href="{% url 'staff:log_visitor' %}"
           data-motion-while-hover='{"y":-2,"scale":1.02}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-plus-lg me-1"></i> Log Visitor
        </a>
        <a class="btn btn-secondary btn-sm"
           href="{% url 'staff:gate_pass_list' %}"
           data-motion-while-hover='{"y":-2}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-door-open me-1"></i> Gate Passes
        </a>
    </div>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if visitors %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Name</th><th>Purpose</th><th>Host</th>
                    <th>In</th><th>Out</th><th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for v in visitors %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Name" class="fw-medium">{{ v.name }}</td>
                    <td data-label="Purpose" class="text-secondary small">{{ v.purpose }}</td>
                    <td data-label="Host" class="small">{{ v.host }}</td>
                    <td data-label="In" class="tabular-nums small">{{ v.time_in|date:"H:i" }}</td>
                    <td data-label="Out" class="tabular-nums small">
                        {{ v.time_out|date:"H:i"|default:"â€”" }}
                    </td>
                    <td class="actions text-end">
                        {% if not v.time_out %}
                        <form method="post" action="{% url 'staff:sign_out_visitor' v.pk %}" class="d-inline">
                            {% csrf_token %}
                            <button class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                <i class="bi bi-box-arrow-right"></i> Sign Out
                            </button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-people fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No visitors logged</h3>
            <p class="text-secondary small mb-3">Log visitors as they arrive on campus.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:log_visitor' %}">Log Visitor</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# Also write the flat paths for backward compatibility.
w("templates/staff/visitor_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Visitor Log{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Visitor Log</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ visitors|length }}">{{ visitors|length }}</span> visits today
        </p>
    </div>
    <div class="d-flex gap-2 flex-wrap"
         data-motion="fade-up" data-motion-delay="140">
        <a class="btn btn-primary btn-sm" href="{% url 'staff:log_visitor' %}"
           data-motion-while-hover='{"y":-2,"scale":1.02}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-plus-lg me-1"></i> Log Visitor
        </a>
        <a class="btn btn-secondary btn-sm" href="{% url 'staff:gate_pass_list' %}"
           data-motion-while-hover='{"y":-2}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-door-open me-1"></i> Gate Passes
        </a>
    </div>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if visitors %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Name</th><th>Purpose</th><th>Host</th>
                    <th>In</th><th>Out</th><th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for v in visitors %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Name" class="fw-medium">{{ v.name }}</td>
                    <td data-label="Purpose" class="text-secondary small">{{ v.purpose }}</td>
                    <td data-label="Host" class="small">{{ v.host }}</td>
                    <td data-label="In" class="tabular-nums small">{{ v.time_in|date:"H:i" }}</td>
                    <td data-label="Out" class="tabular-nums small">
                        {{ v.time_out|date:"H:i"|default:"â€”" }}
                    </td>
                    <td class="actions text-end">
                        {% if not v.time_out %}
                        <form method="post" action="{% url 'staff:sign_out_visitor' v.pk %}" class="d-inline">
                            {% csrf_token %}
                            <button class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                <i class="bi bi-box-arrow-right"></i> Sign Out
                            </button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-people fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No visitors logged</h3>
            <p class="text-secondary small mb-3">Log visitors as they arrive on campus.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:log_visitor' %}">Log Visitor</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


w("templates/staff/visitor_log.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Visitor Log{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Visitor Log</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ visitors|length }}">{{ visitors|length }}</span> visits today
        </p>
    </div>
    <div class="d-flex gap-2 flex-wrap"
         data-motion="fade-up" data-motion-delay="140">
        <a class="btn btn-primary btn-sm" href="{% url 'staff:log_visitor' %}"
           data-motion-while-hover='{"y":-2,"scale":1.02}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-plus-lg me-1"></i> Log Visitor
        </a>
        <a class="btn btn-secondary btn-sm" href="{% url 'staff:gate_pass_list' %}"
           data-motion-while-hover='{"y":-2}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-door-open me-1"></i> Gate Passes
        </a>
    </div>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if visitors %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Name</th><th>Purpose</th><th>Host</th>
                    <th>In</th><th>Out</th><th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for v in visitors %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Name" class="fw-medium">{{ v.name }}</td>
                    <td data-label="Purpose" class="text-secondary small">{{ v.purpose }}</td>
                    <td data-label="Host" class="small">{{ v.host }}</td>
                    <td data-label="In" class="tabular-nums small">{{ v.time_in|date:"H:i" }}</td>
                    <td data-label="Out" class="tabular-nums small">
                        {{ v.time_out|date:"H:i"|default:"â€”" }}
                    </td>
                    <td class="actions text-end">
                        {% if not v.time_out %}
                        <form method="post" action="{% url 'staff:sign_out_visitor' v.pk %}" class="d-inline">
                            {% csrf_token %}
                            <button class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                <i class="bi bi-box-arrow-right"></i> Check Out
                            </button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-people fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No visitors logged</h3>
            <p class="text-secondary small mb-3">Log visitors as they arrive on campus.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:log_visitor' %}">Log Visitor</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


print()
print("Part 1 complete (17 templates). Now run the part 2 script.")
print()
