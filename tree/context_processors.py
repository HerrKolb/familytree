from django.utils import timezone


def now(request):
    """Stellt {{ now }} in allen Templates zur Verfügung."""
    return {'now': timezone.now()}
