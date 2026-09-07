from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import Notification


def notify_user(*, recipient: User, subject: str, message: str, link_url: str | None = None, send_email: bool = True, send_sms: bool = False):
    """Create a Notification and optionally send email/SMS.

    - recipient: Django User to notify
    - subject, message: content
    - link_url: optional relative URL for deep-linking (e.g., /product/123/detail/)
    - send_email: if True and recipient.email exists, send an email via Django email backend
    - send_sms: placeholder; integrate your SMS provider here
    """
    note = Notification.objects.create(
        recipient=recipient,
        subject=subject,
        message=message,
        link_url=link_url,
    )

    # Email (best-effort; ignore failures when email backend isn't configured)
    if send_email and getattr(recipient, 'email', None):
        try:
            send_mail(
                subject=subject,
                message=message + (f"\n\nView: {settings.DEFAULT_DOMAIN}{link_url}" if getattr(settings, 'DEFAULT_DOMAIN', None) and link_url else ''),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost'),
                recipient_list=[recipient.email],
                fail_silently=True,
            )
        except Exception:
            # Silently ignore email failures to avoid blocking in-app notifications
            pass

    # SMS (stub for integration)
    if send_sms:
        # TODO: Integrate with an SMS provider (Twilio, AWS SNS, etc.)
        # Example: sms_client.send(to=recipient.profile.contact_no, text=subject + " - " + message)
        # For now, this is a no-op to keep flow non-blocking.
        pass

    return note
