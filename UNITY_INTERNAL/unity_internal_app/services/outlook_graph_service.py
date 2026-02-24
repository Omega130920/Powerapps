import requests
import json
from django.conf import settings
from .token_manager import get_current_access_token 
from dateutil import parser
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
    def _make_graph_request(endpoint, target_email, method='GET', data=None, is_raw=False):
        """
        Generic internal function to handle authenticated requests.
        Updated to support is_raw for binary/MIME content.
        """
        access_token = get_current_access_token()
        
        if not access_token:
            logger.error("ERROR: Failed to retrieve or refresh access token.")
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

            # If we need the raw binary content (e.g., for .eml files)
            if is_raw:
                return response.content

            if response.status_code == 202 and method == 'POST':
                return {'success': True}

            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logger.error(f"Graph API HTTP Error {status_code}: {e.response.text}")
            
            # Try to return JSON error if available, else string
            try:
                error_details = e.response.json()
            except:
                error_details = e.response.text if e.response.text else str(e)
                
            return {'error': f"Graph API Error: Status {status_code}", 
                    'details': error_details}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network/Connection Error: {e}")
            return {'error': f"Network Error: {str(e)}"}

    # --- Local Sync Logic ---

    @staticmethod
    def sync_to_local_inbox(messages_data):
        """
        Saves or updates emails into the local unmanaged MySQL table 'unity_internal_inbox'.
        """
        from ..models import OutlookInbox 
        
        sync_count = 0
        for msg in messages_data:
            try:
                email_id = msg.get('id')
                subject = msg.get('subject')
                sender_name = msg.get('from', {}).get('emailAddress', {}).get('name')
                sender_addr = msg.get('from', {}).get('emailAddress', {}).get('address')
                body = msg.get('body', {}).get('content')
                received_str = msg.get('receivedDateTime')

                OutlookInbox.objects.update_or_create(
                    email_id=email_id,
                    defaults={
                        'subject': subject,
                        'sender_name': sender_name,
                        'sender_address': sender_addr,
                        'body_content': body,
                        'received_at': parser.isoparse(received_str) if received_str else None
                    }
                )
                sync_count += 1
            except Exception as e:
                logger.error(f"Failed to sync email {msg.get('id')}: {e}")
        
        return sync_count

    # --- Public Service Functions ---

    @staticmethod
    def fetch_inbox_messages(target_email, top_count=10):
        """
        Fetches latest messages and syncs to local MySQL.
        """
        endpoint = (
            f"mailFolders/inbox/messages?$top={top_count}"
            "&$select=subject,from,receivedDateTime,isRead,body"
            "&$orderby=receivedDateTime desc"
        )
        
        response = OutlookGraphService._make_graph_request(endpoint, target_email)
        
        if isinstance(response, dict) and 'value' in response:
            OutlookGraphService.sync_to_local_inbox(response['value'])
            
        return response

    @staticmethod
    def send_outlook_email(target_email, recipient_email, subject, body_content, content_type='HTML'):
        """
        Sends an email via Microsoft Graph and retrieves the newly created ID 
        from Sent Items to allow for future viewing and downloading.
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
        # 1. Send the email
        send_res = OutlookGraphService._make_graph_request(endpoint, target_email, method='POST', data=email_data)
        
        # 2. Check for success (202 Accepted returns {'success': True} in your _make_graph_request)
        if isinstance(send_res, dict) and send_res.get('success') is True:
            try:
                # 3. Retrieve the ID of the email just placed in 'Sent Items'
                # We filter by subject to ensure we get the right one
                sent_endpoint = f"mailFolders/sentitems/messages?$top=1&$select=id&$filter=subject eq '{subject}'"
                sent_check = OutlookGraphService._make_graph_request(sent_endpoint, target_email)
                
                if sent_check and 'value' in sent_check and len(sent_check['value']) > 0:
                    # Return the ID so the View can save it in UnityNotes
                    return {
                        'success': True, 
                        'id': sent_check['value'][0]['id'],
                        'message': 'Email sent and ID retrieved.'
                    }
            except Exception as e:
                logger.error(f"Email sent but Sent Items ID retrieval failed: {e}")
        
        # Fallback if ID couldn't be fetched but mail was sent
        return send_res
    
    # --- Attachment & Raw Content Handling ---

    @staticmethod
    def fetch_attachments(target_email, message_id):
        """
        Fetches metadata for attachments.
        """
        endpoint = f"messages/{message_id}/attachments"
        response = OutlookGraphService._make_graph_request(endpoint, target_email)
        return response.get('value', []) if isinstance(response, dict) else []

    @staticmethod
    def get_attachment_raw(target_email, message_id, attachment_id):
        """
        Fetches specific attachment data.
        """
        endpoint = f"messages/{message_id}/attachments/{attachment_id}"
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def fetch_raw_eml(target_email, message_id):
        """
        Fetches the raw MIME content of a message for .eml download.
        Uses the /$value segment.
        """
        endpoint = f"messages/{message_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, target_email, is_raw=True)