import base64
import json
import logging
import mimetypes
import time
import requests
from dateutil import parser

from django.conf import settings
from .token_manager import get_current_access_token

logger = logging.getLogger(__name__)

# The base URL for the Microsoft Graph API
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"


# --- Signature Generator ---
def get_user_signature(user):
    """Generates the specific HTML signature combining user details and company layout."""
    if not user:
        return ""

    team = {
        'jesica': ('Jesica Haynes', 'Reconciliations Specialist', ''),
        'timothy': ('Timothy Davids', 'Indexing Specialist', ''),
        'mymoena': ('Mymoena Kariem', 'Senior Administrator', '066 192 7247'), 
        'chantal': ('Chantal Roux', 'Reconciliations Specialist', ''),
        'samantha': ('Samantha', 'Job Title', ''),
        'lorraine': ('Lorraine', 'Job Title', ''),
        'merril': ('Merril Fennessy', 'Job Title', ''),
        'gail': ('Gail le Roux', 'Job Title', ''),
        'rashanda': ('Rashanda Heradien', 'Job Title', ''),
        'manager': ('Manager Name', 'Manager', ''),
        'omega': ('Omega User', 'Developer', ''),
    }

    user_key = user.username.lower() if hasattr(user, 'username') else ""
    first_name = user.first_name.lower() if hasattr(user, 'first_name') and user.first_name else ""

    found_user = team.get(user_key) or team.get(first_name)
    logo_url = "https://static.futurasa.co.za/images/futura-logo.png"

    if found_user:
        full_name = found_user[0]
        title = found_user[1]
        mobile = found_user[2] if len(found_user) > 2 else ""
        
        mobile_html = (
            f'<div style="margin: 0 0 4px 0; font-size: 12px;"><strong style="color: #4CAF50;">mobile:</strong> {mobile}</div>'
            if mobile
            else '<div style="margin: 0 0 4px 0; font-size: 12px;"><strong style="color: #4CAF50;">mobile:</strong></div>'
        )

        return f"""
        <div style="font-family: Arial, sans-serif; font-size: 13px; color: #333; margin-top: 20px;">
            <p style="margin: 0 0 20px 0; font-size: 13px; color: #333;">
                Note: Please <strong>do not send schedules and claim forms to personal email addresses</strong> as it is only actioned from <strong><a href="mailto:unityeb@futurasa.co.za" style="color: #0000EE; text-decoration: underline;">unityeb@futurasa.co.za</a></strong>
            </p>
            
            <p style="margin: 0 0 5px 0; font-size: 13px; color: #333;">Kind Regards</p>
            
            <div style="color: #4CAF50; font-size: 14px; font-weight: bold; margin-bottom: 2px;">{full_name}</div>
            <div style="margin-bottom: 20px; color: #333; font-size: 13px;">{title}</div>
            
            <table cellpadding="0" cellspacing="0" border="0" style="width: 100%; max-width: 650px; margin-bottom: 15px;">
                <tr>
                    <td style="padding-right: 15px; vertical-align: middle; width: 140px;">
                        <img src="{logo_url}" alt="Futura Logo" style="width: 150px; display: block;">
                    </td>
                    <td style="vertical-align: middle; border-left: 2px solid #4CAF50; padding-left: 15px;">
                        <div style="margin: 0 0 4px 0; font-size: 12px;"><strong style="color: #4CAF50;">phone:</strong> 087 702 5904</div>
                        {mobile_html}
                        <div style="margin: 0 0 4px 0; font-size: 12px;"><strong style="color: #4CAF50;">fax:</strong> 086 565 4597</div>
                        <div style="margin: 0 0 0 0; font-size: 12px;"><strong style="color: #4CAF50;">Email:</strong> <a href="mailto:unityeb@futurasa.co.za" style="color: #0000EE; text-decoration: underline;">unityeb@futurasa.co.za</a></div>
                    </td>
                </tr>
            </table>
            
            <p style="margin: 20px 0 15px 0; font-size: 12px; color: #333;">
                Futura SA is a Level 1 B-BBEE contributor, committed to transformation and inclusive growth.
            </p>
            
            <p style="font-size: 9.5px; color: #000; line-height: 1.5; text-align: justify;">
                <strong>Disclaimer:</strong> Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by the Financial Sector Conduct Authority in terms of the FAIS Act. License Number 18287 and a licensed Section 13B Administrator number 24/760. This transmission is confidential and intended solely for the person or organization to whom it is addressed. It may contain privileged and confidential information. If you are not the intended recipient, you should not copy, distribute or take any action in reliance on it. If you have received this transmission in error, please notify us immediately by e-mail at <a href="mailto:info@futurasa.co.za" style="color: #0000EE; text-decoration: underline;">info@futurasa.co.za</a>.
            </p>
        </div>
        """

    return f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; margin-top: 20px; color: #333;">
        Kind regards,<br>
        <strong>{user.first_name or user.username}</strong>
    </div>
    """


class OutlookGraphService:

    @staticmethod
    def _make_graph_request(endpoint, target_email=None, method='GET', data=None, is_mime=False):
        """
        Unified request handler using System Service Token with dynamic target_email fallback.
        Handles both JSON responses and raw MIME streams ($value).
        """
        access_token = get_current_access_token()
        if not access_token:
            return {'error': 'Could not acquire access token'}

        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', '')
        url = f"{GRAPH_API_URL}/users/{mailbox}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Prefer': 'outlook.timezone="South Africa Standard Time"'  # Forces Microsoft Graph to return SAST
        }
        
        # Only add JSON content-type if we aren't requesting a raw value stream
        if not is_mime:
            headers['Content-Type'] = 'application/json'

        try:
            # Added timeouts to prevent the app from hanging during network delays
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=(5, 25))
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data if isinstance(data, dict) else None, timeout=(5, 25))
            else:
                return {'error': f"Unsupported HTTP method: {method}"}
            
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
                error_detail = response.json().get('error', {}).get('message', str(e))
            except Exception:
                error_detail = str(e)
            return {'error': error_detail}

    @staticmethod
    def fetch_inbox_messages(target_email=None, top_count=500):
        """
        Fetches recent emails for the live inbox, including full HTML body, CC, and BCC.
        """
        endpoint = (
            f"mailFolders/inbox/messages?$top={top_count}"
            f"&$select=id,subject,from,receivedDateTime,bodyPreview,body,hasAttachments,ccRecipients,bccRecipients"
            f"&$orderby=receivedDateTime desc"
        )
        return OutlookGraphService._make_graph_request(endpoint, target_email=target_email)

    @staticmethod
    def send_outlook_email(target_email=None, recipient_email=None, subject=None, body_content=None, content_type='HTML', attachments=None, cc_email=None, bcc_email=None, user=None):
        """
        CRM_UNITY: Sends directly and MUST return the real Microsoft Message ID.
        Fully updated to handle positional/keyword variables, multi-recipient arrays, and multi-file mapping arrays.
        """
        endpoint = "sendMail"
        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', '')
        
        final_recipient = recipient_email if recipient_email else None
        final_body = body_content if body_content else ""

        if user and content_type.upper() == 'HTML':
            final_body += get_user_signature(user)

        # 1. Prepare the email payload
        message_dict = {
            "subject": subject,
            "body": {"contentType": content_type, "content": final_body},
            "toRecipients": [],
            "ccRecipients": [],
            "bccRecipients": [],
            "attachments": []
        }

        if final_recipient:
            normalized_to = str(final_recipient).replace(',', ';')
            to_addr_list = [addr.strip() for addr in normalized_to.split(';') if addr.strip()]
            message_dict["toRecipients"] = [{"emailAddress": {"address": addr}} for addr in to_addr_list]

        # ROBUST PARSING SAFETY GUARD FOR CC RECIPIENTS
        if cc_email:
            normalized_cc = str(cc_email).replace(',', ';')
            cc_list = [addr.strip() for addr in normalized_cc.split(';') if addr.strip()]
            for address in cc_list:
                message_dict["ccRecipients"].append({
                    "emailAddress": {"address": address}
                })

        # ROBUST PARSING SAFETY GUARD FOR BCC RECIPIENTS
        if bcc_email:
            normalized_bcc = str(bcc_email).replace(',', ';')
            bcc_list = [addr.strip() for addr in normalized_bcc.split(';') if addr.strip()]
            for address in bcc_list:
                message_dict["bccRecipients"].append({
                    "emailAddress": {"address": address}
                })

        # Handle Attachments
        if attachments:
            for f in attachments:
                try:
                    f.seek(0)
                    attachment_content_type = getattr(f, 'content_type', '')
                    
                    if not attachment_content_type or attachment_content_type == 'application/octet-stream':
                        attachment_content_type, _ = mimetypes.guess_type(f.name)
                        
                    if not attachment_content_type:
                        if f.name.lower().endswith('.eml'):
                            attachment_content_type = 'message/rfc822'
                        elif f.name.lower().endswith('.msg'):
                            attachment_content_type = 'application/vnd.ms-outlook'
                        else:
                            attachment_content_type = 'application/octet-stream'

                    encoded_content = base64.b64encode(f.read()).decode('utf-8')
                    message_dict["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": f.name,
                        "contentType": attachment_content_type,
                        "contentBytes": encoded_content
                    })
                except Exception as attachment_err:
                    logger.error(f"Failed to encode file for Microsoft transmission array payload: {attachment_err}")

        payload = {"message": message_dict, "saveToSentItems": "true"}

        # 2. Send the email (Requires Mail.Send permission)
        result = OutlookGraphService._make_graph_request(endpoint, target_email=mailbox, method='POST', data=payload)

        if isinstance(result, dict) and 'error' in result:
            return {'success': False, 'error': result.get('error')}
        
        # 3. Retrieve the REAL ID from Sent Items
        time.sleep(1.5) 
        
        try:
            sent_endpoint = "mailFolders/sentitems/messages?$top=1&$select=id&$orderby=receivedDateTime desc"
            sent_check = OutlookGraphService._make_graph_request(sent_endpoint, target_email=mailbox, method='GET')
            
            if sent_check and 'value' in sent_check and len(sent_check['value']) > 0:
                message_id = sent_check['value'][0]['id'] 
                
                return {
                    'success': True, 
                    'id': message_id,
                    'outlook_id': message_id
                }
            else:
                return {'success': False, 'error': 'Email sent but could not locate ID in Sent Items.'}
        
        except Exception as e:
            return {'success': False, 'error': f"ID Retrieval failed: {str(e)}"}
    
    @staticmethod
    def fetch_attachments(*args, **kwargs):
        """Metadata for all attachments with flexible argument parsing."""
        if len(args) == 2:
            target_email, message_id = args
        elif len(args) == 1:
            target_email, message_id = None, args[0]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')

        endpoint = f"messages/{message_id}/attachments"
        response = OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET')
        return response.get('value', []) if isinstance(response, dict) else []
    
    @staticmethod
    def get_attachment_raw(*args, **kwargs):
        """Raw bytes/metadata for attachments with flexible argument parsing."""
        if len(args) == 3:
            target_email, message_id, attachment_id = args
        elif len(args) == 2:
            target_email, message_id, attachment_id = None, args[0], args[1]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')
            attachment_id = kwargs.get('attachment_id')

        endpoint = f"messages/{message_id}/attachments/{attachment_id}"
        return OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET')

    @staticmethod
    def get_attachment_mime(*args, **kwargs):
        """Fetches raw attachment stream bytes ($value) with flexible argument parsing."""
        if len(args) == 3:
            target_email, message_id, attachment_id = args
        elif len(args) == 2:
            target_email, message_id, attachment_id = None, args[0], args[1]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')
            attachment_id = kwargs.get('attachment_id')

        endpoint = f"messages/{message_id}/attachments/{attachment_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET', is_mime=True)

    @staticmethod
    def get_email_mime_content(*args, **kwargs):
        """
        Fetches the raw RFC822 MIME content of an email ($value).
        Used for downloading .eml files with flexible argument parsing.
        """
        if len(args) == 2:
            target_email, message_id = args
        elif len(args) == 1:
            target_email, message_id = None, args[0]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')

        endpoint = f"messages/{message_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET', is_mime=True)