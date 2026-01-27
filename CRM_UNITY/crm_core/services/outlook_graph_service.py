# outlook_graph_service.py

import time
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
        CRM_UNITY: Sends directly and MUST return the real Microsoft Message ID.
        """
        endpoint = "sendMail"
        
        # 1. Prepare the email payload
        message_dict = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body_html},
            "toRecipients": [{"emailAddress": {"address": recipient.strip()}}],
            "attachments": []
        }

        # Handle Attachments
        if attachments:
            for f in attachments:
                f.seek(0)
                encoded_content = base64.b64encode(f.read()).decode('utf-8')
                message_dict["attachments"].append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": f.name,
                    "contentType": getattr(f, 'content_type', 'application/octet-stream'),
                    "contentBytes": encoded_content
                })

        payload = {"message": message_dict, "saveToSentItems": "true"}

        # 2. Send the email (Requires Mail.Send permission)
        result = OutlookGraphService._make_graph_request(endpoint, method='POST', data=payload)

        if isinstance(result, dict) and 'error' in result:
            return {'success': False, 'error': result.get('error')}
        
        # 3. Retrieve the REAL ID from Sent Items
        # We wait 1.5 seconds for Microsoft to update the Sent folder
        time.sleep(1.5) 
        
        try:
            # We fetch the absolute latest item from the Sent Items folder
            sent_endpoint = "mailFolders/sentitems/messages?$top=1&$select=id&$orderby=receivedDateTime desc"
            sent_check = OutlookGraphService._make_graph_request(sent_endpoint, method='GET')
            
            if sent_check and 'value' in sent_check and len(sent_check['value']) > 0:
                # This is the real AAMk... ID
                message_id = sent_check['value'][0]['id'] 
                
                return {
                    'success': True, 
                    'outlook_id': message_id  # <--- This is what you wanted!
                }
            else:
                return {'success': False, 'error': 'Email sent but could not locate ID in Sent Items.'}
        
        except Exception as e:
            return {'success': False, 'error': f"ID Retrieval failed: {str(e)}"}
    
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