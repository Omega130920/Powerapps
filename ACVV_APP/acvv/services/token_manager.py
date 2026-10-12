import requests
from django.conf import settings
from datetime import datetime, timedelta

from acvv.models import OutlookToken 

def get_outlook_token_object():
    """Retrieves the single OutlookToken object from the database."""
    try:
        # We try to get the existing token object
        return OutlookToken.objects.get(user_principal_name=settings.OUTLOOK_EMAIL_ADDRESS)
    except OutlookToken.DoesNotExist:
        # If it doesn't exist, we create a new, empty record to store the first token
        return OutlookToken.objects.create(
            user_principal_name=settings.OUTLOOK_EMAIL_ADDRESS,
            access_token="initial", # Placeholder
            refresh_token=None,
            expires_in_seconds=0
        )

def get_current_access_token():
    """
    Retrieves the current Access Token, refreshing it using Client Credentials Flow if necessary.
    Returns the valid Access Token string or None if unsuccessful.
    """
    token_obj = get_outlook_token_object()
    
    # Calculate when the token actually expires (in UTC)
    expiry_time_utc = token_obj.updated_at + timedelta(seconds=token_obj.expires_in_seconds)
    
    # Check if we have less than 5 minutes (300 seconds) left or if it's the first run
    if expiry_time_utc < datetime.utcnow().replace(tzinfo=token_obj.updated_at.tzinfo) + timedelta(seconds=300):
        print("Access Token is near expiry or missing. Requesting new token using Client Credentials...")
        return request_new_client_token(token_obj)
    
    return token_obj.access_token

def request_new_client_token(token_obj):
    """
    Requests a new Access Token using the Client ID and Client Secret (Client Credentials Flow).
    Returns the new Access Token string on success, or None on failure.
    """
    
    token_url = f"https://login.microsoftonline.com/{settings.TENANT_ID}/oauth2/v2.0/token"
    
    # Request body for the Client Credentials grant type
    data = {
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
        'scope': ' '.join(settings.GRAPH_SCOPES), # Use the .default scope
        'grant_type': 'client_credentials'
    }

    response = None
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status() # Raise HTTPError for bad status codes
        
        new_tokens = response.json()
        
        # 1. Update the database record with the new token details
        token_obj.access_token = new_tokens['access_token']
        token_obj.expires_in_seconds = new_tokens.get('expires_in', 3600)
        token_obj.refresh_token = None # No refresh token in this flow
        token_obj.save()
        
        print("Token request successful via Client Credentials Flow.")
        return token_obj.access_token
        
    except requests.exceptions.RequestException as e:
        print(f"Token acquisition failed via Client Credentials Flow. Error: {e}")
        if response is not None:
             print(f"Microsoft Response Status: {response.status_code}")
             print(f"Microsoft Response Details: {response.text}")
        return None