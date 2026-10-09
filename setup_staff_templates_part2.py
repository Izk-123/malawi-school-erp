"""
==============================================================================
Staff-portal motion template installer - PART 2
==============================================================================

Writes the remaining 15 templates (visitor_form, gate_pass_*, nurse/*,
announcement_form, medical_record_form, plus doc-spec aliases).

Run AFTER part 1.
==============================================================================
"""
from pathlib import Path
import sys


BASE = Path.cwd()
UTF8 = "utf-8"

if not (BASE / "manage.py").exists():
    print(f"ERROR: manage.py not found in {BASE}")
    sys.exit(1)


def w(relpath, content):
    p = BASE / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=UTF8)
    print(f"  + {relpath}")


print("Writing staff-portal templates (part 2/2) ...")
print()


# ==============================================================================
# 18. staff/security/visitor_form.html  (LogVisitorView)
# ==============================================================================
w("templates/staff/security/visitor_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Log Visitor{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Log Visitor</h1>
        <p class="text-secondary small mb-0">Register a new visitor.</p>
    </div>
    <a href="{% url 'staff:visitor_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back
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


w("templates/staff/visitor_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Log Visitor{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Log Visitor</h1>
        <p class="text-secondary small mb-0">Register a new visitor.</p>
    </div>
    <a href="{% url 'staff:visitor_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back
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
# 19. staff/security/gate_pass_list.html  (GatePassListView)
# ==============================================================================
w("templates/staff/security/gate_pass_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Gate Passes{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Gate Passes</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ gate_passes|length }}">{{ gate_passes|length }}</span> recorded
        </p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:issue_gate_pass' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-plus-lg me-1"></i> Issue Gate Pass
    </a>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if gate_passes %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Student</th>
                    <th>Reason</th>
                    <th>Status</th>
                    <th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for g in gate_passes %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 45 %}">
                    <td data-label="Student">
                        <div class="d-flex align-items-center gap-2">
                            <span class="avatar avatar-sm">{{ g.student.full_name|slice:":1"|upper }}</span>
                            <span class="fw-medium">{{ g.student.full_name }}</span>
                        </div>
                    </td>
                    <td data-label="Reason" class="text-secondary small">{{ g.reason }}</td>
                    <td data-label="Status">
                        {% if g.status == 'returned' %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">Returned</span>
                        {% elif g.status == 'out' %}
                        <span class="badge rounded-pill bg-warning-subtle text-warning-emphasis">Out</span>
                        {% else %}
                        <span class="badge rounded-pill bg-secondary-subtle text-secondary-emphasis">Issued</span>
                        {% endif %}
                    </td>
                    <td class="actions text-end">
                        {% if g.status != 'returned' %}
                        <form method="post" action="{% url 'staff:mark_gate_pass' g.pk %}" class="d-inline">
                            {% csrf_token %}
                            <button class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                {% if g.status == 'issued' %}
                                <i class="bi bi-box-arrow-up"></i> Mark Out
                                {% else %}
                                <i class="bi bi-box-arrow-in-down"></i> Mark Returned
                                {% endif %}
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
                <i class="bi bi-door-open fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No gate passes</h3>
            <p class="text-secondary small mb-3">Issue a pass when a student leaves the campus.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:issue_gate_pass' %}">Issue Gate Pass</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


w("templates/staff/gate_pass_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Gate Passes{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Gate Passes</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ gate_passes|length }}">{{ gate_passes|length }}</span> recorded
        </p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:issue_gate_pass' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-plus-lg me-1"></i> Issue Gate Pass
    </a>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if gate_passes %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Student</th><th>Reason</th>
                    <th>Status</th><th class="text-end"></th>
                </tr>
            </thead>
            <tbody>
                {% for g in gate_passes %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 45 %}">
                    <td data-label="Student">
                        <div class="d-flex align-items-center gap-2">
                            <span class="avatar avatar-sm">{{ g.student.full_name|slice:":1"|upper }}</span>
                            <span class="fw-medium">{{ g.student.full_name }}</span>
                        </div>
                    </td>
                    <td data-label="Reason" class="text-secondary small">{{ g.reason }}</td>
                    <td data-label="Status">
                        {% if g.status == 'returned' %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">Returned</span>
                        {% elif g.status == 'out' %}
                        <span class="badge rounded-pill bg-warning-subtle text-warning-emphasis">Out</span>
                        {% else %}
                        <span class="badge rounded-pill bg-secondary-subtle text-secondary-emphasis">Issued</span>
                        {% endif %}
                    </td>
                    <td class="actions text-end">
                        {% if g.status != 'returned' %}
                        <form method="post" action="{% url 'staff:mark_gate_pass' g.pk %}" class="d-inline">
                            {% csrf_token %}
                            <button class="btn btn-sm btn-primary"
                                    data-motion-while-tap='{"scale":0.94}' data-ripple>
                                {% if g.status == 'issued' %}
                                <i class="bi bi-box-arrow-up"></i> Mark Out
                                {% else %}
                                <i class="bi bi-box-arrow-in-down"></i> Mark Returned
                                {% endif %}
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
                <i class="bi bi-door-open fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No gate passes</h3>
            <p class="text-secondary small mb-3">Issue a pass when a student leaves the campus.</p>
            <a class="btn btn-primary btn-sm" href="{% url 'staff:issue_gate_pass' %}">Issue Gate Pass</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 20. staff/security/gate_pass_form.html  (IssueGatePassView)
# ==============================================================================
w("templates/staff/security/gate_pass_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Issue Gate Pass{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Issue Gate Pass</h1>
        <p class="text-secondary small mb-0">Issue a new gate pass.</p>
    </div>
    <a href="{% url 'staff:gate_pass_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back
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


w("templates/staff/gate_pass_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Issue Gate Pass{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Issue Gate Pass</h1>
        <p class="text-secondary small mb-0">Issue a new gate pass.</p>
    </div>
    <a href="{% url 'staff:gate_pass_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back
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
# 21. staff/nurse/visit_list.html  (SickBayVisitListView)
# ==============================================================================
w("templates/staff/nurse/visit_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Sick Bay Log{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Sick Bay Log</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ visits|length }}">{{ visits|length }}</span> visits recorded
        </p>
    </div>
    <div class="d-flex gap-2 flex-wrap"
         data-motion="fade-up" data-motion-delay="140">
        <a class="btn btn-primary btn-sm"
           href="{% url 'staff:record_sickbay_visit' %}"
           data-motion-while-hover='{"y":-2,"scale":1.02}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-plus-lg me-1"></i> Record Visit
        </a>
        <a class="btn btn-secondary btn-sm"
           href="{% url 'staff:medication_stock' %}"
           data-motion-while-hover='{"y":-2}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-capsule me-1"></i> Medication Stock
        </a>
    </div>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if visits %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Student</th><th>Date</th>
                    <th>Symptoms</th><th>Referred</th>
                </tr>
            </thead>
            <tbody>
                {% for v in visits %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Student">
                        <div class="d-flex align-items-center gap-2">
                            <span class="avatar avatar-sm">{{ v.student.full_name|slice:":1"|upper }}</span>
                            <a href="{% url 'staff:medical_record' v.student.pk %}"
                               class="text-decoration-none fw-medium">
                                {{ v.student.full_name }}
                            </a>
                        </div>
                    </td>
                    <td data-label="Date" class="tabular-nums small">
                        {{ v.visit_date|date:"Y-m-d H:i" }}
                    </td>
                    <td data-label="Symptoms" class="text-secondary small">
                        {{ v.symptoms|truncatewords:10 }}
                    </td>
                    <td data-label="Referred">
                        {% if v.referred %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">Yes</span>
                        {% else %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">No</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-heart-pulse fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No visits recorded</h3>
            <p class="text-secondary small mb-3">Record a visit when a student checks in.</p>
            <a class="btn btn-primary btn-sm"
               href="{% url 'staff:record_sickbay_visit' %}">Record Visit</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# Also write flat aliases the document specifies.
w("templates/staff/sickbay_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Sick Bay Log{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Sick Bay Log</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ visits|length }}">{{ visits|length }}</span> visits recorded
        </p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:record_sickbay_visit' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-plus-lg me-1"></i> Record Visit
    </a>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if visits %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Student</th><th>Date</th>
                    <th>Symptoms</th><th>Referred</th>
                </tr>
            </thead>
            <tbody>
                {% for v in visits %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Student">
                        <div class="d-flex align-items-center gap-2">
                            <span class="avatar avatar-sm">{{ v.student.full_name|slice:":1"|upper }}</span>
                            <span class="fw-medium">{{ v.student.full_name }}</span>
                        </div>
                    </td>
                    <td data-label="Date" class="tabular-nums small">
                        {{ v.visit_date|date:"Y-m-d H:i" }}
                    </td>
                    <td data-label="Symptoms" class="text-secondary small">
                        {{ v.symptoms|truncatewords:10 }}
                    </td>
                    <td data-label="Referred">
                        {% if v.referred %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">Yes</span>
                        {% else %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">No</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-heart-pulse fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No visits recorded</h3>
            <p class="text-secondary small mb-3">Record a visit when a student checks in.</p>
            <a class="btn btn-primary btn-sm"
               href="{% url 'staff:record_sickbay_visit' %}">Record Visit</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


w("templates/staff/visit_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Sick Bay Log{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Sick Bay Log</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ visits|length }}">{{ visits|length }}</span> visits recorded
        </p>
    </div>
    <div class="d-flex gap-2 flex-wrap"
         data-motion="fade-up" data-motion-delay="140">
        <a class="btn btn-primary btn-sm"
           href="{% url 'staff:record_sickbay_visit' %}"
           data-motion-while-hover='{"y":-2,"scale":1.02}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-plus-lg me-1"></i> Record Visit
        </a>
        <a class="btn btn-secondary btn-sm"
           href="{% url 'staff:medication_stock' %}"
           data-motion-while-hover='{"y":-2}'
           data-motion-while-tap='{"scale":0.97}' data-ripple>
            <i class="bi bi-capsule me-1"></i> Medication Stock
        </a>
    </div>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if visits %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Student</th><th>Date</th>
                    <th>Symptoms</th><th>Referred</th>
                </tr>
            </thead>
            <tbody>
                {% for v in visits %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Student">
                        <div class="d-flex align-items-center gap-2">
                            <span class="avatar avatar-sm">{{ v.student.full_name|slice:":1"|upper }}</span>
                            <a href="{% url 'staff:medical_record' v.student.pk %}"
                               class="text-decoration-none fw-medium">
                                {{ v.student.full_name }}
                            </a>
                        </div>
                    </td>
                    <td data-label="Date" class="tabular-nums small">
                        {{ v.visit_date|date:"Y-m-d H:i" }}
                    </td>
                    <td data-label="Symptoms" class="text-secondary small">
                        {{ v.symptoms|truncatewords:10 }}
                    </td>
                    <td data-label="Referred">
                        {% if v.referred %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">Yes</span>
                        {% else %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">No</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-heart-pulse fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No visits recorded</h3>
            <p class="text-secondary small mb-3">Record a visit when a student checks in.</p>
            <a class="btn btn-primary btn-sm"
               href="{% url 'staff:record_sickbay_visit' %}">Record Visit</a>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 22. staff/nurse/visit_form.html  (RecordSickBayVisitView)
# ==============================================================================
w("templates/staff/nurse/visit_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Record Sick Bay Visit{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Record Sick Bay Visit</h1>
        <p class="text-secondary small mb-0">Log a student's visit to the sick bay.</p>
    </div>
    <a href="{% url 'staff:sickbay_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back to Log
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


w("templates/staff/sickbay_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Record Sick Bay Visit{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Record Sick Bay Visit</h1>
        <p class="text-secondary small mb-0">Log a student's visit to the sick bay.</p>
    </div>
    <a href="{% url 'staff:sickbay_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back to Log
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


w("templates/staff/visit_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Record Sick Bay Visit{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Record Sick Bay Visit</h1>
        <p class="text-secondary small mb-0">Log a student's visit to the sick bay.</p>
    </div>
    <a href="{% url 'staff:sickbay_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back to Log
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
# 23. staff/nurse/medical_record_form.html  (MedicalRecordUpdateView)
# ==============================================================================
w("templates/staff/nurse/medical_record_form.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Medical Record &middot; {{ student.full_name }}{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Medical Record</h1>
        <p class="text-secondary small mb-0">{{ student.full_name }}</p>
    </div>
    <a href="{% url 'staff:sickbay_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back
    </a>
</div>
<div class="card" data-motion="fade-up" data-motion-delay="120" data-motion-layout>
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
            <div class="d-flex gap-2 justify-content-end mt-3" data-motion="fade-up">
                <a href="{% url 'staff:sickbay_list' %}" class="btn btn-secondary"
                   data-motion-while-hover='{"y":-2}'
                   data-motion-while-tap='{"scale":0.97}' data-ripple>Cancel</a>
                <button class="btn btn-primary" type="submit"
                        data-motion-while-hover='{"y":-2,"scale":1.02}'
                        data-motion-while-tap='{"scale":0.97}' data-ripple>
                    <i class="bi bi-check2 me-1"></i> Save
                </button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
''')


w("templates/staff/medical_record_form.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Medical Record &middot; {{ student.full_name }}{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Medical Record</h1>
        <p class="text-secondary small mb-0">{{ student.full_name }}</p>
    </div>
    <a href="{% url 'staff:sickbay_list' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back
    </a>
</div>
<div class="card" data-motion="fade-up" data-motion-delay="120" data-motion-layout>
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
            <div class="d-flex gap-2 justify-content-end mt-3" data-motion="fade-up">
                <a href="{% url 'staff:sickbay_list' %}" class="btn btn-secondary"
                   data-motion-while-hover='{"y":-2}'
                   data-motion-while-tap='{"scale":0.97}' data-ripple>Cancel</a>
                <button class="btn btn-primary" type="submit"
                        data-motion-while-hover='{"y":-2,"scale":1.02}'
                        data-motion-while-tap='{"scale":0.97}' data-ripple>
                    <i class="bi bi-check2 me-1"></i> Save
                </button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
''')


# ==============================================================================
# 24. staff/nurse/stock_list.html  (MedicationStockListView)
# ==============================================================================
w("templates/staff/nurse/stock_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Medication Stock{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Medication Stock</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ stock_items|length }}">{{ stock_items|length }}</span> items tracked
        </p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:medication_stock_create' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-plus-lg me-1"></i> Add Stock
    </a>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if stock_items %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Name</th><th>Quantity</th>
                    <th>Reorder</th><th>Expiry</th><th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for m in stock_items %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Name" class="fw-medium">{{ m.name }}</td>
                    <td data-label="Quantity" class="tabular-nums">{{ m.quantity }}</td>
                    <td data-label="Reorder" class="tabular-nums text-secondary">{{ m.reorder_level }}</td>
                    <td data-label="Expiry" class="tabular-nums small">{{ m.expiry_date|default:"—" }}</td>
                    <td data-label="Status">
                        {% if m.needs_reorder %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">Reorder</span>
                        {% else %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">OK</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-capsule fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No stock recorded</h3>
            <p class="text-secondary small mb-0">Add medications to track inventory.</p>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


w("templates/staff/stock_list.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Medication Stock{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Medication Stock</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ stock_items|length }}">{{ stock_items|length }}</span> items tracked
        </p>
    </div>
    <a class="btn btn-primary btn-sm"
       href="{% url 'staff:medication_stock_create' %}"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2,"scale":1.02}'
       data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-plus-lg me-1"></i> Add Stock
    </a>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if stock_items %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Name</th><th>Quantity</th>
                    <th>Reorder</th><th>Expiry</th><th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for m in stock_items %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Name" class="fw-medium">{{ m.name }}</td>
                    <td data-label="Quantity" class="tabular-nums">{{ m.quantity }}</td>
                    <td data-label="Reorder" class="tabular-nums text-secondary">{{ m.reorder_level }}</td>
                    <td data-label="Expiry" class="tabular-nums small">{{ m.expiry_date|default:"—" }}</td>
                    <td data-label="Status">
                        {% if m.needs_reorder %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">Reorder</span>
                        {% else %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">OK</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-capsule fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No stock recorded</h3>
            <p class="text-secondary small mb-0">Add medications to track inventory.</p>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


w("templates/staff/medication_stock.html", r'''{% extends "base.html" %}
{% load static %}
{% block page_title %}Medication Stock{% endblock %}

{% block content %}

<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Medication Stock</h1>
        <p class="text-secondary small mb-0">
            <span class="tabular-nums" data-counter="{{ stock_items|length }}">{{ stock_items|length }}</span> items tracked
        </p>
    </div>
</div>

<div class="card" data-motion="fade-up" data-motion-delay="120" style="overflow:hidden;">
    <div class="card-body p-0">
        {% if stock_items %}
        <table class="table table-hover mb-0 align-middle">
            <thead>
                <tr>
                    <th>Name</th><th>Quantity</th>
                    <th>Reorder</th><th>Expiry</th><th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for m in stock_items %}
                <tr data-motion="fade-up"
                    data-motion-delay="{% widthratio forloop.counter0 1 40 %}">
                    <td data-label="Name" class="fw-medium">{{ m.name }}</td>
                    <td data-label="Quantity" class="tabular-nums">{{ m.quantity }}</td>
                    <td data-label="Reorder" class="tabular-nums text-secondary">{{ m.reorder_level }}</td>
                    <td data-label="Expiry" class="tabular-nums small">{{ m.expiry_date|default:"—" }}</td>
                    <td data-label="Status">
                        {% if m.needs_reorder %}
                        <span class="badge rounded-pill bg-danger-subtle text-danger-emphasis">Reorder</span>
                        {% else %}
                        <span class="badge rounded-pill bg-success-subtle text-success-emphasis">OK</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state text-center py-5">
            <div class="empty-icon mx-auto mb-3">
                <i class="bi bi-capsule fs-2 text-secondary"></i>
            </div>
            <h3 class="h6 fw-semibold mb-1">No stock recorded</h3>
            <p class="text-secondary small mb-0">Add medications to track inventory.</p>
        </div>
        {% endif %}
    </div>
</div>

{% include "partials/dashboard-widgets.html" %}
{% endblock %}
''')


# ==============================================================================
# 25. staff/nurse/stock_form.html  (MedicationStockCreateView)
# ==============================================================================
w("templates/staff/nurse/stock_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Add Stock Item{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Add Stock Item</h1>
        <p class="text-secondary small mb-0">Add a new medication to track.</p>
    </div>
    <a href="{% url 'staff:medication_stock' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back to Stock
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


w("templates/staff/stock_form.html", r'''{% extends "base.html" %}
{% load static crispy_forms_tags %}
{% block page_title %}Add Stock Item{% endblock %}

{% block content %}
<div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2 mb-4"
     data-motion="fade-down" data-motion-duration="460">
    <div>
        <h1 class="h4 fw-bold mb-1"
            data-reveal-text data-reveal-delay="40" data-reveal-stagger="22">Add Stock Item</h1>
        <p class="text-secondary small mb-0">Add a new medication to track.</p>
    </div>
    <a href="{% url 'staff:medication_stock' %}" class="btn btn-secondary btn-sm"
       data-motion="fade-up" data-motion-delay="140"
       data-motion-while-hover='{"y":-2}' data-motion-while-tap='{"scale":0.97}' data-ripple>
        <i class="bi bi-arrow-left me-1"></i> Back to Stock
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


print()
print("=" * 62)
print(" All 32 staff-portal templates installed.")
print("=" * 62)
print()
print("Files written:")
print("  templates/staff/portal_dashboard.html")
print("  templates/staff/dashboard.html            (alias)")
print("  templates/staff/staff_list.html")
print("  templates/staff/my_profile.html")
print("  templates/staff/profile_form.html         (alias)")
print("  templates/staff/my_leave.html")
print("  templates/staff/leave_form.html")
print("  templates/staff/leave_approval.html")
print("  templates/staff/leave_list.html           (alias)")
print("  templates/staff/my_payslips.html")
print("  templates/staff/announcements.html")
print("  templates/staff/announcement_form.html")
print("  templates/staff/ticket_list.html")
print("  templates/staff/ticket_form.html")
print("  templates/staff/librarian/book_list.html")
print("  templates/staff/librarian/book_form.html")
print("  templates/staff/librarian/loan_list.html")
print("  templates/staff/librarian/loan_form.html")
print("  templates/staff/book_list.html            (alias)")
print("  templates/staff/book_form.html            (alias)")
print("  templates/staff/loan_list.html            (alias)")
print("  templates/staff/loan_form.html            (alias)")
print("  templates/staff/overdue_loans.html")
print("  templates/staff/security/visitor_list.html")
print("  templates/staff/security/visitor_form.html")
print("  templates/staff/security/gate_pass_list.html")
print("  templates/staff/security/gate_pass_form.html")
print("  templates/staff/visitor_list.html         (alias)")
print("  templates/staff/visitor_log.html          (alias)")
print("  templates/staff/visitor_form.html         (alias)")
print("  templates/staff/gate_pass_list.html       (alias)")
print("  templates/staff/gate_pass_form.html       (alias)")
print("  templates/staff/nurse/visit_list.html")
print("  templates/staff/nurse/visit_form.html")
print("  templates/staff/nurse/medical_record_form.html")
print("  templates/staff/nurse/stock_list.html")
print("  templates/staff/nurse/stock_form.html")
print("  templates/staff/sickbay_list.html         (alias)")
print("  templates/staff/sickbay_form.html         (alias)")
print("  templates/staff/visit_list.html           (alias)")
print("  templates/staff/visit_form.html           (alias)")
print("  templates/staff/medical_record_form.html  (alias)")
print("  templates/staff/stock_list.html           (alias)")
print("  templates/staff/medication_stock.html     (alias)")
print("  templates/staff/stock_form.html           (alias)")
print()
print("Verify with:")
print("  python manage.py check")
print("  python manage.py runserver")
print()