from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notes = request.user.notifications.all()[:20]
    return JsonResponse({
        'notifications': [
            {'id': n.id, 'message': n.message, 'type': n.notification_type, 'is_read': n.is_read}
            for n in notes
        ]
    })


@login_required
@require_POST
def mark_read(request, pk):
    Notification.objects.filter(pk=pk, recipient=request.user).update(is_read=True)
    return JsonResponse({'status': 'ok'})
