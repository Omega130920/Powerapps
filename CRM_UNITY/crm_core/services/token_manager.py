import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
from django.contrib.auth import get_user_model

# Use the CRM Unity token model
from ..models import CrmUnityOutlookToken 

User = get_user_model()
logger = logging.getLogger(__name__)

def get_outlook_token_object():
    """
    Retrieves the system token record. 
    Links it to 'omega' or the first superuser as a service-account anchor.
    """
    system_user = User.objects.filter(username='omega').first() or User.objects.filter(is_superuser=True).first()
    
    if not system_user:
        logger.error("No administrative user found to anchor the System Token.")
        return None

    # We use get_or_create using the 'user' field to satisfy the model requirement
    obj, created = CrmUnityOutlookToken.objects.get_or_create(
        user=system_user,
        defaults={
            'access_token': 'initial',
            'expires_at': timezone.now()
        }
    )
    return obj

def get_current_access_token():
    """
    Retrieves the valid Access Token. 
    Unity_Internal logic: Automatically requests a new one if near expiry.
    """
    token_obj = get_outlook_token_object()
    if not token_obj:
        return None
    
    # Check if expired or expires in next 5 minutes
    if token_obj.expires_at < timezone.now() + timedelta(seconds=300):
        logger.info("Service Token expired/missing. Requesting new token via Client Credentials...")
        return request_new_client_token(token_obj)
    
    return token_obj.access_token

def request_new_client_token(token_obj):
    """
    Unity_Internal Style: Requests token using Client ID/Secret.
    """
    token_url = f"https://login.microsoftonline.com/{settings.OUTLOOK_TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        'client_id': settings.OUTLOOK_CLIENT_ID,
        'client_secret': settings.OUTLOOK_CLIENT_SECRET,
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
        
        logger.info("System Token refreshed successfully.")
        return token_obj.access_token
        
    except Exception as e:
        logger.error(f"Token acquisition failed: {e}")
        return None