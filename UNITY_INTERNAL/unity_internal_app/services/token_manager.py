import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from ..models import OutlookToken

logger = logging.getLogger(__name__)


def get_outlook_token_object():
    """Retrieves the single OutlookToken object from the database."""
    try:
        return OutlookToken.objects.get(user_principal_name=settings.OUTLOOK_EMAIL_ADDRESS)
    except OutlookToken.DoesNotExist:
        logger.info("No existing OutlookToken found. Creating placeholder.")
        return OutlookToken.objects.create(
            user_principal_name=settings.OUTLOOK_EMAIL_ADDRESS,
            access_token="initial",
            refresh_token=None,
            expires_in_seconds=0
        )


def get_current_access_token():
    """
    Retrieves the current Access Token, refreshing it using Client Credentials Flow if necessary.
    Returns the valid Access Token string or None if unsuccessful.
    """
    token_obj = get_outlook_token_object()
    expiry_time = token_obj.updated_at + timedelta(seconds=token_obj.expires_in_seconds)

    if token_obj.access_token == "initial" or expiry_time < timezone.now() + timedelta(seconds=300):
        logger.info("Access Token is near expiry or missing. Requesting new token using Client Credentials...")
        return request_new_client_token(token_obj)

    return token_obj.access_token


def request_new_client_token(token_obj):
    """
    Requests a new Access Token using Client Credentials Flow with a strict 30-second timeout.
    """
    token_url = f"https://login.microsoftonline.com/{settings.TENANT_ID}/oauth2/v2.0/token"

    data = {
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
        'scope': ' '.join(settings.GRAPH_SCOPES),
        'grant_type': 'client_credentials'
    }

    response = None
    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()

        new_tokens = response.json()
        token_obj.access_token = new_tokens['access_token']
        token_obj.expires_in_seconds = new_tokens.get('expires_in', 3600)
        token_obj.refresh_token = None
        token_obj.save()

        logger.info("Token request successful via Client Credentials Flow.")
        return token_obj.access_token

    except requests.exceptions.RequestException as e:
        logger.error(f"Token acquisition failed via Client Credentials Flow. Error: {e}")
        if response is not None:
            logger.error(f"Microsoft Response Status: {response.status_code}")
            logger.error(f"Microsoft Response Details: {response.text}")
        return None