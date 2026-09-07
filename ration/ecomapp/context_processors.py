from .models import Category, Cart
from django.contrib.auth.models import AnonymousUser
from django.db.models import Count
from django.core.exceptions import ImproperlyConfigured

def categories_context(request):
    """Add categories to all template contexts."""
    return {
        'categories': Category.objects.all()
    }


def cart_count(request):
    """Provide the count of cart items for the logged-in user across all templates."""
    try:
        if request.user.is_authenticated:
            return {
                'cart_count': Cart.objects.filter(user=request.user).count()
            }
    except Exception:
        # If anything goes wrong (e.g., during migrations), fail safely
        pass

    return {'cart_count': 0}


def notifications_context(request):
    """Provide unread notifications count globally.

    Exposed as 'unread_notifications_count'. Safe on all pages.
    """
    count = 0
    try:
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            # Lazy import to avoid circulars in migrations
            from .models import Notification
            count = Notification.objects.filter(recipient=user, is_read=False).count()
    except Exception:
        # Fail-safe during migrations or missing table
        count = 0
    return { 'unread_notifications_count': count }

