import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
from PSSUBF_APP.models import PssubfOutlookToken

logger = logging.getLogger(__name__)

def get_outlook_token_object():
    """
    Retrieves the isolated token record for PSSUBF.
    Uses the email address as the unique identifier.
    """
    email_anchor = settings.OUTLOOK_EMAIL_ADDRESS
    
    obj, created = PssubfOutlookToken.objects.get_or_create(
        service_account=email_anchor,
        defaults={
            'access_token': 'initial',
            'expires_at': timezone.now()
        }
    )
    return obj

def get_current_access_token():
    token_obj = get_outlook_token_object()
    if not token_obj:
        return None
    
    # Refresh if expired or near expiry (5 mins)
    if token_obj.expires_at < timezone.now() + timedelta(seconds=300):
        return request_new_client_token(token_obj)
    
    return token_obj.access_token

def request_new_client_token(token_obj):
    # CHANGED: Updated to use MSGRAPH_TENANT_ID
    token_url = f"https://login.microsoftonline.com/{settings.MSGRAPH_TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        # CHANGED: Updated to use MSGRAPH_CLIENT_ID and MSGRAPH_CLIENT_SECRET
        'client_id': settings.MSGRAPH_CLIENT_ID,
        'client_secret': settings.MSGRAPH_CLIENT_SECRET,
        'scope': ' '.join(settings.GRAPH_SCOPES), 
        'grant_type': 'client_credentials'
    }

    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        new_tokens = response.json()
        
        token_obj.access_token = new_tokens['access_token']
        token_obj.expires_at = timezone.now() + timedelta(seconds=new_tokens.get('expires_in', 3600))
        token_obj.save()
        
        return token_obj.access_token
    except Exception as e:
        logger.error(f"PSSUBF Token acquisition failed: {e}")
        return None