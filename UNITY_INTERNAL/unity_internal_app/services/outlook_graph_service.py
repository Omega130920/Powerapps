import requests
import json
import base64
from django.conf import settings
from .token_manager import get_current_access_token 
from dateutil import parser
import logging

logger = logging.getLogger(__name__)

# The base URL for the Microsoft Graph API
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

# --- NEW: Signature Generator ---
def get_user_signature(user):
    """Generates the specific HTML signature based on the user's name."""
    if not user:
        return ""

    # Dictionary Mapping for all Team Members
    team = {
        'jesica': ('Jesica Haynes', 'Reconciliations Specialist'),
        'timothy': ('Timothy Davids', 'Indexing Specialist'),
        'mymoena': ('Mymoena', 'Job Title'),  # Update Titles as needed
        'chantal': ('Chantal', 'Job Title'),
        'karen': ('Karen', 'Job Title'),
        'samantha': ('Samantha', 'Job Title'),
        'lorraine': ('Lorraine', 'Job Title'),
        'merril': ('Merril', 'Job Title'),
        'gail': ('Gail', 'Job Title'),
        'rashanda': ('Rashanda', 'Job Title'),
        'manager': ('Manager Name', 'Manager'),
        'omega': ('Omega User', 'Developer'),
        'alpha': ('Alpha User', 'Developer'),
    }

    user_key = user.username.lower() if hasattr(user, 'username') else ""
    first_name = user.first_name.lower() if hasattr(user, 'first_name') and user.first_name else ""
    
    found_user = team.get(user_key) or team.get(first_name)
    logo_url = "https://futurasa.co.za/wp-content/uploads/2021/04/futura-logo.png"

    if found_user:
        full_name, title = found_user
        return f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 12px; color: #333; margin-top: 30px; padding-top: 15px;">
            <div style="color: #4CAF50; font-size: 15px; font-weight: bold; margin-bottom: 2px;">{full_name}</div>
            <div style="margin-bottom: 12px; color: #333;">{title}</div>
            <img src="{logo_url}" alt="Futura" width="130" style="display: block; margin-bottom: 5px;">
            <div style="font-size: 11px; color: #666; margin-top: 15px;">
                <p>Futura SA is a Level 1 B-BBEE contributor, committed to transformation and inclusive growth.</p>
                <p style="font-size: 8.5px; color: #000; text-align: justify; line-height: 1.4;">
                <strong>Disclaimer:</strong> Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by the Financial Sector Conduct Authority in terms of the FAIS Act. License Number 18287 and a licensed Section 13B Administrator number 24/760.
                </p>
            </div>
        </div>
        """
    
    # Fallback Signature for Test Users (testuser1, testuser2, etc.)
    return f"""
    <div style="font-family: sans-serif; font-size: 12px; margin-top: 20px;">
        Kind regards,<br>
        <strong>{user.first_name or user.username}</strong>
    </div>
    """
# --------------------------------

class OutlookGraphService:
    """
    A service class to wrap Graph API calls, using the token manager 
    and handling delegation via target_email.
    """

    @staticmethod
    def _make_graph_request(endpoint, target_email, method='GET', data=None, is_raw=False):
        """
        Generic internal function to handle authenticated requests.
        Supports is_raw for binary/MIME content (returns response.content).
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

            # If we need the raw binary content (e.g., for .eml files or attachment /$value)
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
                
            return {'error': f"Graph API Error: Status {status_code}", 
                    'details': error_details}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network/Connection Error: {e}")
            return {'error': f"Network Error: {str(e)}"}

    # --- Local Sync Logic ---

    @staticmethod
    def sync_to_local_inbox(messages_data):
        """
        saves or updates emails into the local unmanaged MySQL table 'unity_internal_inbox'.
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

                # Extract CC and BCC recipients from Microsoft's JSON structure
                cc_list = [
                    recip.get('emailAddress', {}).get('address', '') 
                    for recip in msg.get('ccRecipients', []) 
                    if recip.get('emailAddress', {}).get('address')
                ]
                bcc_list = [
                    recip.get('emailAddress', {}).get('address', '') 
                    for recip in msg.get('bccRecipients', []) 
                    if recip.get('emailAddress', {}).get('address')
                ]

                OutlookInbox.objects.update_or_create(
                    email_id=email_id,
                    defaults={
                        'subject': subject,
                        'sender_name': sender_name,
                        'sender_address': sender_addr,
                        'cc_addresses': ", ".join(cc_list),
                        'bcc_addresses': ", ".join(bcc_list),
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
            "&$select=subject,from,receivedDateTime,isRead,body,ccRecipients,bccRecipients"
            "&$orderby=receivedDateTime desc"
        )
        
        response = OutlookGraphService._make_graph_request(endpoint, target_email)
        
        if isinstance(response, dict) and 'value' in response:
            OutlookGraphService.sync_to_local_inbox(response['value'])
            
        return response

    @staticmethod
    def send_outlook_email(target_email, recipient_email, subject, body_content, content_type='HTML', attachments=None, cc_email=None, bcc_email=None, user=None):
        """
        Sends an email via Microsoft Graph and retrieves the newly created ID 
        by fetching the most recent item in Sent Items, avoiding subject-filter errors.
        """
        
        # --- Inject Signature ---
        if user and content_type.upper() == 'HTML':
            body_content += get_user_signature(user)

        email_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": content_type, 
                    "content": body_content
                },
                "toRecipients": [{"emailAddress": {"address": recipient_email.strip()}}],
                "ccRecipients": [], 
                "bccRecipients": [], 
                "attachments": [] 
            },
            "saveToSentItems": "true" 
        }

        # 🚀 ROBUST PARSING FOR CC/BCC
        for field, key in [(cc_email, "ccRecipients"), (bcc_email, "bccRecipients")]:
            if field:
                normalized = str(field).replace(',', ';')
                addr_list = [addr.strip() for addr in normalized.split(';') if addr.strip()]
                for address in addr_list:
                    email_data["message"][key].append({"emailAddress": {"address": address}})

        # Process Attachments
        if attachments:
            for file in attachments:
                try:
                    file.seek(0)
                    encoded_string = base64.b64encode(file.read()).decode('utf-8')
                    email_data["message"]["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": file.name,
                        "contentType": getattr(file, 'content_type', 'application/octet-stream'),
                        "contentBytes": encoded_string
                    })
                except Exception as e:
                    logger.error(f"Failed to package attachment: {e}")
        
        # Send
        endpoint = "sendMail"
        send_res = OutlookGraphService._make_graph_request(endpoint, target_email, method='POST', data=email_data)
        
        # Retrieve ID using a more reliable method
        if isinstance(send_res, dict) and send_res.get('success') is True:
            try:
                # 🚀 FIX: Get the most recent item in Sent Items instead of filtering by subject
                # This works even if the subject changed or contains special characters
                sent_endpoint = "mailFolders/sentitems/messages?$top=1&$select=id,subject&$orderby=receivedDateTime desc"
                sent_check = OutlookGraphService._make_graph_request(sent_endpoint, target_email)
                
                if sent_check and 'value' in sent_check and len(sent_check['value']) > 0:
                    return {
                        'success': True, 
                        'id': sent_check['value'][0]['id'],
                        'message': 'Email sent and ID retrieved.'
                    }
            except Exception as e:
                logger.error(f"Sent Items ID retrieval failed: {e}")
        
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
        Fetches specific attachment metadata (JSON).
        """
        endpoint = f"messages/{message_id}/attachments/{attachment_id}"
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def get_attachment_mime(target_email, message_id, attachment_id):
        """
        Fetches the raw binary content of an attachment using the /$value segment.
        Required for ItemAttachments (nested emails).
        """
        endpoint = f"messages/{message_id}/attachments/{attachment_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, target_email, is_raw=True)

    @staticmethod
    def fetch_raw_eml(target_email, message_id):
        """
        Fetches the raw MIME content of a main message for .eml download.
        """
        endpoint = f"messages/{message_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, target_email, is_raw=True)