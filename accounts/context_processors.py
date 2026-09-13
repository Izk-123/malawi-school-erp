"""Exposes the correct sidebar menu for the logged-in user's role to every template."""

ROLE_MENUS = {
    'admin': [
        {'url': 'accounts:dashboard', 'icon': 'bi-speedometer2', 'label': 'Dashboard'},
        {'url': 'students:list', 'icon': 'bi-people', 'label': 'Students'},
        {'url': 'teachers:list', 'icon': 'bi-person-video3', 'label': 'Teachers'},
        {'url': 'staff:list', 'icon': 'bi-people', 'label': 'Staff'},
        {'url': 'attendance:mark', 'icon': 'bi-clipboard-check', 'label': 'Mark Attendance'},
        {'url': 'attendance:admin_summary', 'icon': 'bi-bar-chart-steps', 'label': 'Attendance Summary'},
        {'url': 'grades:list', 'icon': 'bi-journal-text', 'label': 'Grades & Exams'},
        {'url': 'fees:list', 'icon': 'bi-cash-coin', 'label': 'Fees & Payments'},
        {'url': 'timetable:list', 'icon': 'bi-calendar-week', 'label': 'Timetable'},
        {'url': 'reports:index', 'icon': 'bi-graph-up', 'label': 'Reports'},
        {'url': 'syllabus:subject_list', 'icon': 'bi-journal-bookmark', 'label': 'MANEB Syllabus'},
        {'url': 'syllabus:topic_performance', 'icon': 'bi-bar-chart-line', 'label': 'Topic Performance'},
        {'url': 'accounts:user_list', 'icon': 'bi-person-gear', 'label': 'User Management'},
        {'url': 'accounts:profile', 'icon': 'bi-person-circle', 'label': 'My Profile'},
    ],
    'teacher': [
        {'url': 'accounts:dashboard', 'icon': 'bi-speedometer2', 'label': 'Dashboard'},
        {'url': 'teachers:my_classes', 'icon': 'bi-easel', 'label': 'My Classes'},
        {'url': 'attendance:mark', 'icon': 'bi-clipboard-check', 'label': 'Mark Attendance'},
        {'url': 'attendance:history', 'icon': 'bi-clock-history', 'label': 'Attendance History'},
        {'url': 'grades:list', 'icon': 'bi-journal-text', 'label': 'Grade Entry'},
        {'url': 'syllabus:my_subjects', 'icon': 'bi-journal-bookmark', 'label': 'My Syllabus'},
        {'url': 'syllabus:topic_performance', 'icon': 'bi-bar-chart-line', 'label': 'Topic Performance'},
        {'url': 'timetable:list', 'icon': 'bi-calendar-week', 'label': 'My Timetable'},
        {'url': 'reports:index', 'icon': 'bi-graph-up', 'label': 'Reports'},
        {'url': 'teachers:my_profile', 'icon': 'bi-person-circle', 'label': 'My Profile'},
    ],
    'student': [
        {'url': 'accounts:dashboard', 'icon': 'bi-speedometer2', 'label': 'Dashboard'},
        {'url': 'attendance:my_attendance', 'icon': 'bi-clipboard-check', 'label': 'My Attendance'},
        {'url': 'grades:my_grades', 'icon': 'bi-journal-text', 'label': 'My Grades'},
        {'url': 'fees:my_fees', 'icon': 'bi-cash-coin', 'label': 'My Fees'},
        {'url': 'timetable:my_timetable', 'icon': 'bi-calendar-week', 'label': 'My Timetable'},
        {'url': 'syllabus:subject_list', 'icon': 'bi-journal-bookmark', 'label': 'Syllabus'},
        {'url': 'accounts:profile', 'icon': 'bi-person-circle', 'label': 'My Profile'},
    ],
    'parent': [
        {'url': 'accounts:dashboard', 'icon': 'bi-speedometer2', 'label': 'Dashboard'},
        {'url': 'students:my_children', 'icon': 'bi-people', 'label': 'My Children'},
        {'url': 'fees:list', 'icon': 'bi-cash-coin', 'label': 'Fees & Payments'},
        {'url': 'attendance:summary', 'icon': 'bi-clipboard-check', 'label': 'Attendance'},
        {'url': 'grades:list', 'icon': 'bi-journal-text', 'label': 'Grades'},
        {'url': 'accounts:profile', 'icon': 'bi-person-circle', 'label': 'My Profile'},
    ],
    'staff': [
        {'url': 'accounts:dashboard', 'icon': 'bi-speedometer2', 'label': 'Dashboard'},
        {'url': 'staff:list', 'icon': 'bi-people', 'label': 'Staff Directory'},
        {'url': 'timetable:list', 'icon': 'bi-calendar-week', 'label': 'Timetable'},
        {'url': 'reports:index', 'icon': 'bi-graph-up', 'label': 'Reports'},
        {'url': 'accounts:profile', 'icon': 'bi-person-circle', 'label': 'My Profile'},
    ],
}


def role_menu(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    role = 'admin' if user.is_superuser else getattr(user, 'role', 'student')
    return {
        'sidebar_menu': ROLE_MENUS.get(role, ROLE_MENUS['student']),
        'current_role': role,
    }
