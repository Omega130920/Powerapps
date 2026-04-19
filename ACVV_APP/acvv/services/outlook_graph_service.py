import requests
import json
import base64
import re  # Added for recipient string cleaning
from django.conf import settings
from .token_manager import get_current_access_token 

# The base URL for the Microsoft Graph API
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

def _make_graph_request(endpoint, target_email, method='GET', data=None):
    """
    Generic internal function to handle all authenticated requests to the Graph API.
    Handles token retrieval and basic error handling, using the target_email 
    for delegation.
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


# --- Public Service Functions (Delegation-Aware) ---

def fetch_inbox_messages(target_email, top_count=10):
    endpoint = f"mailFolders/inbox/messages?$top={top_count}&$select=subject,from,receivedDateTime,isRead"
    return _make_graph_request(endpoint, target_email)

def send_outlook_email(target_email, recipient_email, subject, body_content, content_type='Text', attachment=None):
    """
    Sends an email from the specified target mailbox (target_email).
    FIXED: Handles recipient_email as a single string OR a list of strings to support multiple recipients.
    """
    
    # --- MULTI-RECIPIENT LOGIC ---
    # If it's a string (e.g., from a database or manual entry), split it into a list
    if isinstance(recipient_email, str):
        recipients_list = [email.strip() for email in re.split('[;,]', recipient_email) if email.strip()]
    else:
        # Otherwise assume it's already a list passed from the view
        recipients_list = recipient_email

    # Format for Graph API: Each email must be its own object in the array
    to_recipients = [
        {
            "emailAddress": {
                "address": email
            }
        } for email in recipients_list
    ]

    email_data = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": content_type, 
                "content": body_content
            },
            "toRecipients": to_recipients, # Now a correctly formatted list of objects
            "attachments": [] 
        },
        "saveToSentItems": "true" 
    }

    if attachment:
        try:
            attachment.seek(0)
            content_bytes = attachment.read()
            encoded_content = base64.b64encode(content_bytes).decode('utf-8')

            email_data["message"]["attachments"].append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": attachment.name,
                "contentType": attachment.content_type,
                "contentBytes": encoded_content
            })
        except Exception as e:
            print(f"Failed to process attachment for sendMail: {e}")
    
    endpoint = "sendMail"
    
    response = _make_graph_request(endpoint, target_email, method='POST', data=email_data)
    
    if 'error' in response:
        return response
    
    return {'success': True, 'message': 'Email successfully submitted to Graph API.'}