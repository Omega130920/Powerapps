import requests
import logging
import base64  # <--- ADDED THIS IMPORT
from django.conf import settings
from .token_manager import get_current_access_token

logger = logging.getLogger(__name__)

class OutlookGraphService:
    @staticmethod
    def _make_graph_request(endpoint, method='GET', data=None):
        """Unified request handler using System Service Token."""
        access_token = get_current_access_token()
        if not access_token:
            return {'error': 'Could not acquire access token'}

        # Construct full URL using the service mailbox from settings
        url = f"https://graph.microsoft.com/v1.0/users/{settings.OUTLOOK_EMAIL_ADDRESS}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers, json=data)
            
            # 202 Accepted (common for sendMail) returns empty text
            if response.status_code == 202 or not response.text:
                return {}

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Graph Request Error: {e}")
            # Try to extract a useful error message from the response if available
            try:
                error_detail = response.json().get('error', {}).get('message', str(e))
            except:
                error_detail = str(e)
            return {'error': error_detail}

    @staticmethod
    def fetch_inbox_messages(top_count=15):
        """Fetches recent emails for the live inbox."""
        endpoint = f"mailFolders/inbox/messages?$top={top_count}&$select=id,subject,from,receivedDateTime,bodyPreview"
        return OutlookGraphService._make_graph_request(endpoint)

    @staticmethod
    def send_outlook_email(recipient, subject, body_html, attachments=None):
        """
        Sends an email using the Service Account defined in settings.
        UPDATED: Now supports a list of Django UploadedFile objects as attachments.
        """
        endpoint = "sendMail"
        
        # 1. Construct the base payload
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body_html
                },
                "toRecipients": [
                    {"emailAddress": {"address": recipient}}
                ],
                "attachments": [] # Start empty
            },
            "saveToSentItems": "true"
        }

        # 2. Process Attachments if provided
        if attachments:
            for f in attachments:
                try:
                    # Reset file pointer to the beginning to ensure we read the whole file
                    f.seek(0)
                    content_bytes = f.read()
                    encoded_content = base64.b64encode(content_bytes).decode('utf-8')
                    
                    # Append to payload
                    payload["message"]["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": f.name,
                        "contentType": getattr(f, 'content_type', 'application/octet-stream'),
                        "contentBytes": encoded_content
                    })
                except Exception as e:
                    logger.error(f"Failed to process attachment {f.name}: {e}")
                    return {'success': False, 'error': f"Attachment Error: {str(e)}"}

        # 3. Send request to Microsoft Graph via the unified handler
        result = OutlookGraphService._make_graph_request(endpoint, method='POST', data=payload)

        # Microsoft Graph sendMail returns an empty dictionary/body on success.
        # If there is an 'error' key in the dictionary, it failed.
        if isinstance(result, dict) and 'error' in result:
            return {'success': False, 'error': result.get('error')}
        
        return {'success': True}