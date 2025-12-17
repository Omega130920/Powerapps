import requests
import json
from django.conf import settings
from .token_manager import get_current_access_token 

# The base URL for the Microsoft Graph API
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

def _make_graph_request(endpoint, target_email, method='GET', data=None):
    """
    Generic internal function to handle all authenticated requests to the Graph API.
    """
    access_token = get_current_access_token()
    
    if not access_token:
        print("ERROR: Failed to retrieve or refresh access token.")
        return {'error': 'Authentication failed: Missing or expired token.'}

    url = f"{GRAPH_API_URL}/users/{target_email}/{endpoint}"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=json.dumps(data))
        else:
            return {'error': f"Unsupported HTTP method: {method}"}
        
        response.raise_for_status() 

        # Handle successful 202 (Accepted) response (Needed for sendMail)
        if response.status_code == 202 and method == 'POST':
            return {'success': True}

        return response.json()

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        print(f"Graph API HTTP Error {status_code}: {e.response.text}")
        error_details = e.response.json() if e.response.text else str(e)
        return {'error': f"Graph API Error: Status {status_code}", 
                'details': error_details}
    except requests.exceptions.RequestException as e:
        print(f"Network/Connection Error: {e}")
        return {'error': f"Network Error: {str(e)}"}


# --- Public Service Functions ---

def fetch_inbox_messages(target_email, top_count=10):
    """Fetches the latest messages from the specified target mailbox."""
    endpoint = f"mailFolders/inbox/messages?$top={top_count}&$select=subject,from,receivedDateTime,isRead"
    return _make_graph_request(endpoint, target_email)

def send_outlook_email(target_email, recipient_email, subject, body_content, content_type='Text'):
    """Sends an email from the specified target mailbox (target_email)."""
    email_data = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": content_type, 
                "content": body_content
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient_email
                    }
                }
            ],
        },
        "saveToSentItems": "true" 
    }
    
    endpoint = "sendMail"
    response = _make_graph_request(endpoint, target_email, method='POST', data=email_data)
    
    if 'error' in response:
        return response
    
    return {'success': True, 'message': 'Email successfully submitted to Graph API.'}