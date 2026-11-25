from django.conf import settings
from django.utils import timezone


def now(request):
    """Stellt {{ now }} in allen Templates zur Verfügung."""
    return {'now': timezone.now()}


def auth_mode(request):
    """Stellt Anmeldemodus und Abmelde-Adresse für die Templates bereit."""
    return {
        'auth_mode': settings.AUTH_MODE,
        'logout_url_external': settings.LOGOUT_URL_EXTERNAL,
    }
