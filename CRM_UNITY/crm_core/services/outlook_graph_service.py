# outlook_graph_service.py

import requests
import logging
import base64
from django.conf import settings
from .token_manager import get_current_access_token

logger = logging.getLogger(__name__)

class OutlookGraphService:

    @staticmethod
    def _make_graph_request(endpoint, method='GET', data=None, is_mime=False):
        """
        Unified request handler using System Service Token.
        Handles both JSON responses and raw MIME streams ($value).
        """
        access_token = get_current_access_token()
        if not access_token:
            return {'error': 'Could not acquire access token'}

        # Construct full URL using the service mailbox from settings
        url = f"https://graph.microsoft.com/v1.0/users/{settings.OUTLOOK_EMAIL_ADDRESS}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        
        # Only add JSON content-type if we aren't requesting a raw value stream
        if not is_mime:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers, json=data)
            
            # If we requested a MIME stream ($value), return the raw content bytes
            if is_mime and response.status_code == 200:
                return response.content

            # 202 Accepted (common for sendMail) returns empty text
            if response.status_code == 202 or not response.text:
                return {}

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Graph Request Error: {e}")
            try:
                # Attempt to extract specific Microsoft Graph error messages
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
        CRM_UNITY: Sends an email directly via the /sendMail endpoint.
        Updated to fix 403 Forbidden errors by removing the 'Draft' creation step,
        which requires Mail.ReadWrite permissions.
        """
        endpoint = "sendMail"
        
        # 1. Construct the message dictionary structure
        message_dict = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body_html
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient}}
            ],
            "attachments": []
        }

        # 2. Process and encode attachments directly into the message payload
        if attachments:
            for f in attachments:
                try:
                    f.seek(0)
                    content_bytes = f.read()
                    encoded_content = base64.b64encode(content_bytes).decode('utf-8')
                    
                    message_dict["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": f.name,
                        "contentType": getattr(f, 'content_type', 'application/octet-stream'),
                        "contentBytes": encoded_content
                    })
                except Exception as e:
                    logger.error(f"CRM_UNITY: Failed to encode attachment {f.name}: {e}")

        # 3. Wrap the message in the 'message' key required by the /sendMail API
        payload = {
            "message": message_dict,
            "saveToSentItems": "true"
        }

        # 4. Execute the single POST request to send the email
        result = OutlookGraphService._make_graph_request(endpoint, method='POST', data=payload)

        # Check for error results returned from the handler
        if isinstance(result, dict) and 'error' in result:
            return {'success': False, 'error': result.get('error')}
        
        # On success, return a static ID as /sendMail does not return the created Message ID
        return {'success': True, 'outlook_id': 'DIRECT_SEND_SUCCESS'}
    
    @staticmethod
    def fetch_attachments(target_email, message_id):
        """Metadata for all attachments."""
        endpoint = f"messages/{message_id}/attachments"
        response = OutlookGraphService._make_graph_request(endpoint, method='GET')
        return response.get('value', [])
    
    @staticmethod
    def get_attachment_raw(target_email, message_id, attachment_id):
        """Raw bytes for image thumbnails."""
        endpoint = f"messages/{message_id}/attachments/{attachment_id}"
        return OutlookGraphService._make_graph_request(endpoint, method='GET')

    @staticmethod
    def get_email_mime_content(message_id):
        """
        Fetches the raw RFC822 MIME content of an email ($value).
        Used for downloading .eml files.
        """
        endpoint = f"messages/{message_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, method='GET', is_mime=True)