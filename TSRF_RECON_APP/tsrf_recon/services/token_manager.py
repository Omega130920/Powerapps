import requests
from django.conf import settings
from datetime import timedelta
from tsrf_recon.models import TSRFReconOutlookToken 
from django.utils import timezone  # Use this for timezone-aware comparisons

def get_outlook_token_object():
    """Retrieves the token for the system mailbox."""
    try:
        # Note: Your model uses a OneToOne to User. 
        # For system-level flow, we look for the record associated with the admin/system user.
        return TSRFReconOutlookToken.objects.first() 
    except TSRFReconOutlookToken.DoesNotExist:
        return None

def get_current_access_token():
    token_obj = get_outlook_token_object()
    
    # Use timezone.now() to match the 'aware' datetime stored in the DB
    current_time = timezone.now()
    
    # If no token exists or it's about to expire (within 5 mins)
    if not token_obj or token_obj.expires_at < current_time + timedelta(seconds=300):
        return request_new_client_token()
    
    return token_obj.access_token

def request_new_client_token():
    token_url = f"https://login.microsoftonline.com/{settings.MSGRAPH_TENANT_ID}/oauth2/v2.0/token"
    data = {
        'client_id': settings.MSGRAPH_CLIENT_ID,
        'client_secret': settings.MSGRAPH_CLIENT_SECRET,
        'scope': ' '.join(settings.GRAPH_SCOPES),
        'grant_type': 'client_credentials'
    }

    response = requests.post(token_url, data=data)
    response.raise_for_status()
    new_tokens = response.json()
    
    # Update or Create the token record
    from django.contrib.auth import get_user_model
    User = get_user_model()
    system_user = User.objects.filter(is_superuser=True).first()
    
    # Calculate expiration using timezone.now()
    expiration_time = timezone.now() + timedelta(seconds=new_tokens.get('expires_in', 3600))
    
    token_obj, created = TSRFReconOutlookToken.objects.update_or_create(
        user=system_user,
        defaults={
            'access_token': new_tokens['access_token'],
            'expires_at': expiration_time
        }
    )
    return token_obj.access_token