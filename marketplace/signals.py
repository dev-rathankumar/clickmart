from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .utils import merge_session_cart_to_db

@receiver(user_logged_in)
def handle_user_logged_in(sender, user, request, **kwargs):
    merge_session_cart_to_db(request, user)