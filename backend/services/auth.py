"""Simple API-key and staff-based authorization helper for training endpoints.

Usage:
    from services.auth import authorize_request
    authorize_request(request)  # raises rest_framework.exceptions.PermissionDenied on failure
"""
import os
from django.conf import settings
from rest_framework.exceptions import PermissionDenied


def _get_allowed_keys():
    keys = getattr(settings, "TRAINING_API_KEYS", None)
    if keys:
        if isinstance(keys, (list, tuple)):
            return [k.strip() for k in keys if k]
        return [k.strip() for k in str(keys).split(",") if k.strip()]

    env = os.environ.get("TRAINING_API_KEYS")
    if env:
        return [k.strip() for k in env.split(",") if k.strip()]

    return []


def authorize_request(request):
    """Authorize a Django request for training actions.

    Rules:
      - If `X-API-KEY` header matches a key in `TRAINING_API_KEYS`, allow.
      - Else if the user is authenticated and `is_staff`, allow.
      - Else raise PermissionDenied.
    """
    allowed = _get_allowed_keys()
    # header keys are available as HTTP_X_API_KEY in META or via request.headers
    header_key = None
    try:
        header_key = request.META.get("HTTP_X_API_KEY") or (getattr(request, "headers", {}) or {}).get("X-API-KEY")
    except Exception:
        header_key = request.META.get("HTTP_X_API_KEY")

    if header_key and header_key in allowed:
        return True

    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False) and getattr(user, "is_staff", False):
        return True

    raise PermissionDenied("Authentication credentials were not provided or are invalid.")
