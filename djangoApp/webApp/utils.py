from functools import wraps
from webApp.models import Transaction
from django.http import HttpResponseForbidden


from django.shortcuts import render

def is_user(allowed_user_types):
    """
    Decorator that restricts view access to users with specific user types.

    :param allowed_user_types: A set of UserType values allowed to access the view.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if the user is authenticated
            if not request.user.is_authenticated:
                return render(request, 'webApp/authentication-required.html', status=403)

            # Check if the user type is in the allowed set
            if request.user.user_type not in allowed_user_types:
                return render(request, 'webApp/permission-denied.html', status=403)

            # Proceed to the view if checks pass
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def add_transaction(transaction_type,details, amount=None, quantity=None):

    transaction = Transaction(
        transaction_type = transaction_type,
        details = details,
        amount=amount,
        quantity=quantity)
    transaction.save()
