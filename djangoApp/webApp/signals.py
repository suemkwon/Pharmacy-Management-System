from django.contrib.auth import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from webApp.models import User, TransactionType
from webApp.utils import add_transaction


@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
   add_transaction(TransactionType.LOGIN,f"{user} logged in")


@receiver(user_logged_out)
def log_user_logout(sender, user, request, **kwargs):
    add_transaction(TransactionType.LOGOUT, f"{user} logged out")

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get("username", "Unknown")
    user = User.objects.filter(username=username).first()  # Try to get user if it exists
    add_transaction(TransactionType.LOGIN_FAIL,f"Failed login attempt for username: {username}, user: {user}")
