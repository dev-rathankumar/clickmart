from django.utils import timezone
from .models import Event

def get_current_event():
    now = timezone.now()
    event = Event.objects.filter(start_date__lte=now, end_date__gte=now, active=True).first()
    if event:
        return event
    return Event.objects.filter(default=True).first()


