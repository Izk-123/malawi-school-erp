from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('staff/', include('staff.urls')),
    path('attendance/', include('attendance.urls')),
    path('grades/', include('grades.urls')),
    path('fees/', include('fees.urls')),
    path('timetable/', include('timetable.urls')),
    path('reports/', include('reports.urls')),
    path('notifications/', include('notifications.urls')),
    path('syllabus/', include('syllabus.urls')),
    path('payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Developer tooling — login required so the shell renders.
    urlpatterns += [
        path(
            'dev/components/',
            login_required(TemplateView.as_view(template_name='dev/components.html')),
            name='dev_components',
        ),
        path(
            'dev/responsive/',
            login_required(TemplateView.as_view(template_name='dev/responsive.html')),
            name='dev_responsive',
        ),
    ]