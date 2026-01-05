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
    def _make_graph_request(endpoint, target_email, method='GET', data=None):
        """
        Generic internal function to handle all authenticated requests to the Graph API.
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

            if response.status_code == 202 and method == 'POST':
                return {'success': True}

            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logger.error(f"Graph API HTTP Error {status_code}: {e.response.text}")
            error_details = e.response.json() if e.response.text else str(e)
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
        # Local import to prevent circular dependency
        from ..models import OutlookInbox 
        
        sync_count = 0
        for msg in messages_data:
            try:
                # Extract values safely
                email_id = msg.get('id')
                subject = msg.get('subject')
                sender_name = msg.get('from', {}).get('emailAddress', {}).get('name')
                sender_addr = msg.get('from', {}).get('emailAddress', {}).get('address')
                body = msg.get('body', {}).get('content')
                received_str = msg.get('receivedDateTime')

                # Update or Create in MySQL
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

    # --- Public Service Functions (Delegation-Aware) ---

    @staticmethod
    def fetch_inbox_messages(target_email, top_count=10):
        """
        Fetches the latest messages and syncs them to the local MySQL inbox.
        Included 'body' in select so we can archive the content.
        """
        # We add 'body' to the select query so we have the content to save locally
        endpoint = (
            f"mailFolders/inbox/messages?$top={top_count}"
            "&$select=subject,from,receivedDateTime,isRead,body"
            "&$orderby=receivedDateTime desc"
        )
        
        response = OutlookGraphService._make_graph_request(endpoint, target_email)
        
        if 'value' in response:
            # Trigger the local sync
            OutlookGraphService.sync_to_local_inbox(response['value'])
            
        return response

    @staticmethod
    def send_outlook_email(target_email, recipient_email, subject, body_content, content_type='Text'):
        """
        Sends an email and logs the action.
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
        response = OutlookGraphService._make_graph_request(endpoint, target_email, method='POST', data=email_data)
        
        if 'error' in response:
            return response
        
        return {'success': True, 'message': 'Email successfully submitted to Graph API.'}
    
    # --- Attachment Handling ---

    @staticmethod
    def fetch_attachments(target_email, message_id):
        """
        Fetches the metadata for all attachments belonging to a specific message.
        """
        endpoint = f"messages/{message_id}/attachments"
        response = OutlookGraphService._make_graph_request(endpoint, target_email)
        
        # Return the list of attachment objects if found, else empty list
        return response.get('value', [])

    @staticmethod
    def get_attachment_raw(target_email, message_id, attachment_id):
        """
        Fetches the raw data for a specific attachment.
        Note: Microsoft Graph returns this as a Base64 string in the 'contentBytes' field.
        """
        endpoint = f"messages/{message_id}/attachments/{attachment_id}"
        return OutlookGraphService._make_graph_request(endpoint, target_email)