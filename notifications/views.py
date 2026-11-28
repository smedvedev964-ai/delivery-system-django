from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_list(request):
    if request.method == "POST":
        notification = get_object_or_404(
            Notification, pk=request.POST.get("notification_id"), user=request.user
        )
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        messages.success(request, "Уведомление отмечено прочитанным.")
        return redirect("notifications:list")

    notifications = Notification.objects.filter(user=request.user)
    return render(request, "notifications/list.html", {
        "notifications": notifications,
        "unread_count": notifications.filter(is_read=False).count(),
    })
