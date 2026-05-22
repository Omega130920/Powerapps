import requests
import json
import base64
import logging
from django.conf import settings
from .token_manager import get_current_access_token 

# Initialize logger
logger = logging.getLogger(__name__)

# The base URL for the Microsoft Graph API
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

class OutlookGraphService:
    """
    A service class to wrap Graph API calls, ensuring a consistent
    API-first approach for all Outlook interactions.
    """

    @staticmethod
    def _make_graph_request(endpoint, target_email, method='GET', data=None, is_raw=False):
        """
        Generic internal function to handle authenticated requests.
        Supports is_raw for binary content (e.g., attachments).
        """
        access_token = get_current_access_token()
        
        if not access_token:
            logger.error("Authentication failed: Missing or expired token.")
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

            # Return raw binary content if requested
            if is_raw:
                return response.content

            if response.status_code == 202 and method == 'POST':
                return {'success': True}

            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logger.error(f"Graph API HTTP Error {status_code}: {e.response.text}")
            
            try:
                error_details = e.response.json()
            except:
                error_details = e.response.text if e.response.text else str(e)
                
            return {'error': f"Graph API Error: Status {status_code}", 'details': error_details}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network/Connection Error: {e}")
            return {'error': f"Network Error: {str(e)}"}

    # --- Public Service Functions ---

    @staticmethod
    def fetch_outlook_data(endpoint, target_email):
        return OutlookGraphService._make_graph_request(endpoint, target_email, method='GET')

    @staticmethod
    def fetch_inbox_messages(target_email, top_count=10):
        endpoint = f"mailFolders/inbox/messages?$top={top_count}&$select=subject,from,receivedDateTime,isRead,body&$orderby=receivedDateTime desc"
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def fetch_message_details(target_email, message_id):
        endpoint = f"messages/{message_id}"
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def fetch_attachments(target_email, message_id):
        endpoint = f"messages/{message_id}/attachments"
        response = OutlookGraphService._make_graph_request(endpoint, target_email)
        return response.get('value', []) if isinstance(response, dict) else []

    @staticmethod
    def send_outlook_email(target_email, recipient_email, subject, body_content, content_type='HTML', attachments=None):
        """
        Sends an email from the target mailbox with support for multiple attachments.
        Fixed: Handles both list and string inputs for recipient_email to prevent AttributeError.
        """
        
        # Determine the list of addresses
        if isinstance(recipient_email, str):
            addresses = [email.strip() for email in recipient_email.split(',') if email.strip()]
        elif isinstance(recipient_email, list):
            addresses = [email.strip() for email in recipient_email if isinstance(email, str)]
        else:
            addresses = []

        email_data = {
            "message": {
                "subject": subject,
                "body": {"contentType": content_type, "content": body_content},
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in addresses],
                "attachments": [] 
            },
            "saveToSentItems": "true" 
        }

        if attachments:
            for file in attachments:
                try:
                    file.seek(0)
                    encoded_content = base64.b64encode(file.read()).decode('utf-8')
                    email_data["message"]["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": file.name,
                        "contentType": getattr(file, 'content_type', 'application/octet-stream'),
                        "contentBytes": encoded_content
                    })
                except Exception as e:
                    logger.error(f"Failed to process attachment {getattr(file, 'name', 'unknown')}: {e}")
        
        return OutlookGraphService._make_graph_request("sendMail", target_email, method='POST', data=email_data)