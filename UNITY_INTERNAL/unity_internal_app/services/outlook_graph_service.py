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

# --- Signature Generator ---
def get_user_signature(user):
    """Generates the specific HTML signature combining user details and company layout."""
    if not user:
        return ""

    # Dictionary Mapping for all Team Members
    team = {
        'jesica': ('Jesica Haynes', 'Reconciliations Specialist'),
        'timothy': ('Timothy Davids', 'Indexing Specialist'),
        'mymoena': ('Mymoena', 'Job Title'), 
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
    
    # Always use a public web URL for email signatures so external clients can render it
    logo_url = "https://futurasa.co.za/wp-content/uploads/2021/04/futura-logo.png"

    if found_user:
        full_name, title = found_user
        return f"""
        <div style="font-family: Arial, sans-serif; font-size: 13px; color: #333; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 15px;">
            <table cellpadding="0" cellspacing="0" border="0" style="width: 100%; max-width: 650px;">
                <tr>
                    <td style="padding-right: 20px; vertical-align: top; width: 200px;">
                        <div style="color: #4CAF50; font-size: 16px; font-weight: bold; margin-bottom: 2px;">{full_name}</div>
                        <div style="margin-bottom: 12px; color: #555; font-size: 12px;">{title}</div>
                        <img src="{logo_url}" alt="Futura Logo" style="width: 150px; display: block;">
                    </td>
                    <td style="vertical-align: top; border-left: 1px solid #eee; padding-left: 20px;">
                        <p style="margin: 0 0 4px 0; font-size: 12px;"><strong>phone:</strong> 087 702 5904</p>
                        <p style="margin: 0 0 4px 0; font-size: 12px;"><strong>mobile:</strong></p>
                        <p style="margin: 0 0 4px 0; font-size: 12px;"><strong>fax:</strong> 086 565 4597</p>
                        <p style="margin: 0 0 0 0; font-size: 12px;"><strong>Email:</strong> <a href="mailto:unityeb@futurasa.co.za" style="color: #2e7d32; text-decoration: none;">unityeb@futurasa.co.za</a></p>
                    </td>
                </tr>
            </table>
            
            <p style="margin: 15px 0 10px 0; font-size: 11px; font-weight: bold; color: #000;">
                Futura SA is a Level 1 B-BBEE contributor, committed to transformation and inclusive growth.
            </p>
            
            <p style="font-size: 9.5px; color: #666; line-height: 1.4; text-align: justify;">
                <strong>Disclaimer:</strong> Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by the Financial Sector Conduct Authority in terms of the FAIS Act. License Number 18287 and a licensed Section 13B Administrator number 24/760. This transmission is confidential and intended solely for the person or organization to whom it is addressed. If you have received this transmission in error, please notify us immediately by e-mail at <a href="mailto:info@futurasa.co.za" style="color: #666; text-decoration: none;">info@futurasa.co.za</a>.
            </p>
        </div>
        """

    # Fallback Signature for Users not in the dictionary
    return f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; margin-top: 20px; color: #333;">
        Kind regards,<br>
        <strong>{user.first_name or user.username}</strong>
    </div>
    """

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
        Saves or updates emails into the local unmanaged MySQL table 'unity_internal_inbox',
        capturing 'To' recipients alongside CC and BCC.
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

                # Extract To recipients
                to_list = [
                    recip.get('emailAddress', {}).get('address', '') 
                    for recip in msg.get('toRecipients', []) 
                    if recip.get('emailAddress', {}).get('address')
                ]

                # Extract CC and BCC recipients
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
                        'to_addresses': ", ".join(to_list),  # 🚀 Added To field mapping
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
            "&$select=subject,from,receivedDateTime,isRead,body,toRecipients,ccRecipients,bccRecipients"
            "&$orderby=receivedDateTime desc"
        )

        response = OutlookGraphService._make_graph_request(endpoint, target_email)

        if isinstance(response, dict) and 'value' in response:
            OutlookGraphService.sync_to_local_inbox(response['value'])

        return response

    @staticmethod
    def send_outlook_email(target_email, recipient_email, subject, body_content, content_type='HTML', attachments=None, cc_email=None, bcc_email=None, user=None):
        """
        Sends an email via Microsoft Graph, handling To, CC, BCC recipients 
        and retrieving the newly created item ID from Sent Items.
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

        # 🚀 ROBUST PARSING FOR TO, CC, AND BCC MULTIPLE RECIPIENTS
        for field, key in [(recipient_email, "toRecipients"), (cc_email, "ccRecipients"), (bcc_email, "bccRecipients")]:
            if field and key != "toRecipients": # toRecipients primary is handled, but supports comma/semi-colon split if needed globally
                pass

        # If multiple comma/semicolon separated emails are passed to recipient_email:
        if recipient_email and (',' in recipient_email or ';' in recipient_email):
            normalized_to = str(recipient_email).replace(',', ';')
            to_addr_list = [addr.strip() for addr in normalized_to.split(';') if addr.strip()]
            email_data["message"]["toRecipients"] = [{"emailAddress": {"address": addr}} for addr in to_addr_list]

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

        # Retrieve ID using Sent Items
        if isinstance(send_res, dict) and send_res.get('success') is True:
            try:
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
        endpoint = f"messages/{message_id}/attachments"
        response = OutlookGraphService._make_graph_request(endpoint, target_email)
        return response.get('value', []) if isinstance(response, dict) else []

    @staticmethod
    def get_attachment_raw(target_email, message_id, attachment_id):
        endpoint = f"messages/{message_id}/attachments/{attachment_id}"
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def get_attachment_mime(target_email, message_id, attachment_id):
        endpoint = f"messages/{message_id}/attachments/{attachment_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, target_email, is_raw=True)

    @staticmethod
    def fetch_raw_eml(target_email, message_id):
        endpoint = f"messages/{message_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, target_email, is_raw=True)