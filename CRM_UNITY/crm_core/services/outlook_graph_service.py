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
        Added 'is_mime' parameter to handle raw RFC822/MIME streams ($value).
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
                # If it's a response object, try to get JSON error
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
        Captured outlook_id by creating a draft first, then sending.
        """
        # STEP 1: Create a Draft Message to obtain a Message ID
        create_endpoint = "messages"
        draft_payload = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body_html
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient}}
            ]
        }

        draft_result = OutlookGraphService._make_graph_request(create_endpoint, method='POST', data=draft_payload)
        
        if isinstance(draft_result, dict) and 'error' in draft_result:
            return {'success': False, 'error': draft_result.get('error')}
        
        message_id = draft_result.get('id')
        if not message_id:
            return {'success': False, 'error': 'Failed to retrieve message ID from Microsoft Graph'}

        # STEP 2: Upload Attachments to the Draft if they exist
        if attachments:
            for f in attachments:
                try:
                    f.seek(0)
                    content_bytes = f.read()
                    encoded_content = base64.b64encode(content_bytes).decode('utf-8')
                    
                    attachment_payload = {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": f.name,
                        "contentType": getattr(f, 'content_type', 'application/octet-stream'),
                        "contentBytes": encoded_content
                    }
                    
                    attach_endpoint = f"messages/{message_id}/attachments"
                    attach_result = OutlookGraphService._make_graph_request(attach_endpoint, method='POST', data=attachment_payload)
                    
                    if isinstance(attach_result, dict) and 'error' in attach_result:
                        logger.error(f"Attachment failed for {f.name}: {attach_result.get('error')}")
                except Exception as e:
                    logger.error(f"Failed to process attachment {f.name}: {e}")

        # STEP 3: Send the Draft
        send_endpoint = f"messages/{message_id}/send"
        send_result = OutlookGraphService._make_graph_request(send_endpoint, method='POST')

        if isinstance(send_result, dict) and 'error' in send_result:
            return {'success': False, 'error': send_result.get('error')}
        
        # Return success and the ID so it can be stored in DirectEmailLog
        return {'success': True, 'outlook_id': message_id}
    
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
        NEW: Fetches the raw RFC822 MIME content of an email.
        This allows downloading the actual .eml file.
        """
        endpoint = f"messages/{message_id}/$value"
        # We pass is_mime=True so the handler returns raw bytes instead of JSON
        return OutlookGraphService._make_graph_request(endpoint, method='GET', is_mime=True)