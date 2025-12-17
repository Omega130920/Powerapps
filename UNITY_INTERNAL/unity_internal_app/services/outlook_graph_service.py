import requests
import json
from django.conf import settings
from .token_manager import get_current_access_token 
import logging

logger = logging.getLogger(__name__)

# The base URL for the Microsoft Graph API
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

class OutlookGraphService:
    """
    A service class to wrap Graph API calls, using the token manager 
    and handling delegation via target_email.
    """

    @staticmethod
    def _make_graph_request(endpoint, target_email, method='GET', data=None):
        """
        Generic internal function to handle all authenticated requests to the Graph API.
        Handles token retrieval and basic error handling, using the target_email 
        for delegation.
        """
        # 1. Get the Access Token (Client Credentials flow provides app-level token)
        access_token = get_current_access_token()
        
        if not access_token:
            logger.error("ERROR: Failed to retrieve or refresh access token.")
            return {'error': 'Authentication failed: Missing or expired token.'}

        # 🛑 KEY CHANGE: Use the dynamic target_email in the URL for delegation 🛑
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
            
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status() 

            # 🛑 Handle successful 202 (Accepted) response (Needed for sendMail) 🛑
            if response.status_code == 202 and method == 'POST':
                return {'success': True}

            # Return the JSON content for success (for 200/201 responses)
            return response.json()

        except requests.exceptions.HTTPError as e:
            # Catch specific HTTP errors from Graph API
            status_code = e.response.status_code
            logger.error(f"Graph API HTTP Error {status_code}: {e.response.text}")
            
            # Attempt to parse JSON error body if available
            error_details = e.response.json() if e.response.text else str(e)
            return {'error': f"Graph API Error: Status {status_code}", 
                    'details': error_details}
            
        except requests.exceptions.RequestException as e:
            # Catch network or connection errors
            logger.error(f"Network/Connection Error: {e}")
            return {'error': f"Network Error: {str(e)}"}


    # --- Public Service Functions (Delegation-Aware) ---

    @staticmethod
    def fetch_inbox_messages(target_email, top_count=10):
        """
        Fetches the latest messages from the specified target mailbox's Inbox.
        """
        endpoint = f"mailFolders/inbox/messages?$top={top_count}&$select=subject,from,receivedDateTime,isRead"
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def send_outlook_email(target_email, recipient_email, subject, body_content, content_type='Text'):
        """
        Sends an email from the specified target mailbox (target_email).
        """
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
        
        # Use the helper to make the authenticated POST request, passing the target_email as the sender
        response = OutlookGraphService._make_graph_request(endpoint, target_email, method='POST', data=email_data)
        
        if 'error' in response:
            return response
        
        # Success is guaranteed if the helper returns {'success': True}
        return {'success': True, 'message': 'Email successfully submitted to Graph API.'}