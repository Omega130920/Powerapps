import base64
import json
import logging
import mimetypes
import requests
from dateutil import parser

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

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
    def _make_graph_request(endpoint, target_email=None, method='GET', data=None, is_raw=False):
        """
        Generic internal function to handle authenticated requests with timeout protection.
        """
        access_token = get_current_access_token()
        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', '')

        if not access_token:
            logger.error("ERROR: Failed to retrieve or refresh access token.")
            return {'error': 'Authentication failed: Missing or expired token.'}

        url = f"{GRAPH_API_URL}/users/{mailbox}/{endpoint}"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Prefer': 'outlook.timezone="South Africa Standard Time"'
        }

        if not is_raw:
            headers['Content-Type'] = 'application/json'

        try:
            # 🟢 TIMEOUT GUARD ADDED TO PREVENT WORKER UNRESPONSIVENESS
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=(5, 25))
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data if isinstance(data, dict) else None, timeout=(5, 25))
            else:
                return {'error': f"Unsupported HTTP method: {method}"}

            if is_raw and response.status_code == 200:
                return response.content

            if response.status_code == 202 and method == 'POST':
                return {'success': True}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logger.error(f"Graph API HTTP Error {status_code}: {e.response.text}")
            try:
                error_details = e.response.json()
            except Exception:
                error_details = e.response.text if e.response.text else str(e)

            return {'error': f"Graph API Error: Status {status_code}", 'details': error_details}

        except requests.exceptions.RequestException as e:
            logger.error(f"Network/Connection Error: {e}")
            return {'error': f"Network Error: {str(e)}"}

    @staticmethod
    def sync_to_local_inbox(messages_data):
        """
        Saves or updates emails into local unmanaged MySQL table 'unity_internal_inbox'.
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

                to_list = [
                    recip.get('emailAddress', {}).get('address', '') 
                    for recip in msg.get('toRecipients', []) 
                    if recip.get('emailAddress', {}).get('address')
                ]
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
                        'to_addresses': ", ".join(to_list),
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

    @staticmethod
    def fetch_inbox_messages(target_email=None, top_count=10):
        """
        🟢 OPTIMIZED: Uses $select metadata filtering to reduce RAM payload footprint.
        """
        endpoint = (
            f"mailFolders/inbox/messages?$top={top_count}"
            "&$select=id,subject,from,receivedDateTime,isRead,hasAttachments,toRecipients,ccRecipients,bccRecipients"
            "&$orderby=receivedDateTime desc"
        )

        response = OutlookGraphService._make_graph_request(endpoint, target_email)

        if isinstance(response, dict) and 'value' in response:
            OutlookGraphService.sync_to_local_inbox(response['value'])

        return response

    @staticmethod
    def send_outlook_email(target_email=None, recipient_email=None, subject=None, body_content=None, content_type='HTML', attachments=None, cc_email=None, bcc_email=None, user=None):
        """
        Sends an email via Microsoft Graph and retrieves newly created item ID from Sent Items.
        """
        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', '')
        
        if user and content_type.upper() == 'HTML':
            body_content += get_user_signature(user)

        email_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": content_type, 
                    "content": body_content
                },
                "toRecipients": [{"emailAddress": {"address": recipient_email.strip()}}] if recipient_email else [],
                "ccRecipients": [], 
                "bccRecipients": [], 
                "attachments": [] 
            },
            "saveToSentItems": "true" 
        }

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

        if attachments:
            for file in attachments:
                try:
                    file.seek(0)
                    attachment_content_type = getattr(file, 'content_type', '')
                    
                    if not attachment_content_type or attachment_content_type == 'application/octet-stream':
                        attachment_content_type, _ = mimetypes.guess_type(file.name)
                        
                    if not attachment_content_type:
                        if file.name.lower().endswith('.eml'):
                            attachment_content_type = 'message/rfc822'
                        elif file.name.lower().endswith('.msg'):
                            attachment_content_type = 'application/vnd.ms-outlook'
                        else:
                            attachment_content_type = 'application/octet-stream'

                    encoded_string = base64.b64encode(file.read()).decode('utf-8')
                    
                    email_data["message"]["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": file.name,
                        "contentType": attachment_content_type,
                        "contentBytes": encoded_string
                    })
                except Exception as e:
                    logger.error(f"Failed to package attachment: {e}")

        endpoint = "sendMail"
        send_res = OutlookGraphService._make_graph_request(endpoint, mailbox, method='POST', data=email_data)

        if isinstance(send_res, dict) and send_res.get('success') is True:
            try:
                sent_endpoint = "mailFolders/sentitems/messages?$top=1&$select=id,subject&$orderby=receivedDateTime desc"
                sent_check = OutlookGraphService._make_graph_request(sent_endpoint, mailbox)

                if sent_check and 'value' in sent_check and len(sent_check['value']) > 0:
                    return {
                        'success': True, 
                        'id': sent_check['value'][0]['id'],
                        'message': 'Email sent and ID retrieved.'
                    }
            except Exception as e:
                logger.error(f"Sent Items ID retrieval failed: {e}")

        return send_res

    @staticmethod
    def fetch_attachments(*args, **kwargs):
        if len(args) == 2:
            target_email, message_id = args
        elif len(args) == 1:
            target_email, message_id = None, args[0]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')

        endpoint = f"messages/{message_id}/attachments"
        response = OutlookGraphService._make_graph_request(endpoint, target_email)
        return response.get('value', []) if isinstance(response, dict) else []

    @staticmethod
    def get_attachment_raw(*args, **kwargs):
        if len(args) == 3:
            target_email, message_id, attachment_id = args
        elif len(args) == 2:
            target_email, message_id, attachment_id = None, args[0], args[1]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')
            attachment_id = kwargs.get('attachment_id')

        endpoint = f"messages/{message_id}/attachments/{attachment_id}"
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def get_attachment_mime(*args, **kwargs):
        if len(args) == 3:
            target_email, message_id, attachment_id = args
        elif len(args) == 2:
            target_email, message_id, attachment_id = None, args[0], args[1]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')
            attachment_id = kwargs.get('attachment_id')

        endpoint = f"messages/{message_id}/attachments/{attachment_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, target_email, is_raw=True)

    @staticmethod
    def fetch_raw_eml(*args, **kwargs):
        if len(args) == 2:
            target_email, message_id = args
        elif len(args) == 1:
            target_email, message_id = None, args[0]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')

        endpoint = f"messages/{message_id}/$value"
        return OutlookGraphService._make_graph_request(endpoint, target_email, is_raw=True)