from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if getattr(request.user, "role", None) not in roles and not (
                request.user.is_superuser and "admin" in roles
            ):
                raise PermissionDenied("У вашей учётной записи нет доступа к этой странице.")
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
