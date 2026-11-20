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


def _parse_recipients(recipient_input):
    """Helper function to parse strings or lists of email addresses into Microsoft Graph format."""
    if not recipient_input:
        return []
    if isinstance(recipient_input, str):
        raw_emails = [e.strip() for e in recipient_input.replace(',', ';').split(';') if e.strip()]
    elif isinstance(recipient_input, list):
        raw_emails = [e.strip() for e in recipient_input if isinstance(e, str) and e.strip()]
    else:
        raw_emails = []
    return [{"emailAddress": {"address": email}} for email in raw_emails]


class OutlookGraphService:

    @staticmethod
    def _make_graph_request(endpoint, target_email=None, method='GET', data=None, is_raw=False, is_mime=False):
        """
        Generic internal function to handle authenticated requests with timeout protection
        and ImmutableId support. When is_mime=True, returns the streaming response object.
        """
        access_token = get_current_access_token()
        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', '')

        if not access_token:
            logger.error("ERROR: Failed to retrieve or refresh access token.")
            return {'error': 'Authentication failed: Missing or expired token.'}

        url = f"{GRAPH_API_URL}/users/{mailbox}/{endpoint}"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Prefer': 'IdType="ImmutableId", outlook.timezone="South Africa Standard Time"'
        }

        if not is_raw and not is_mime:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=(5, 30), stream=is_mime)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data if isinstance(data, dict) else None, timeout=(5, 30))
            else:
                return {'error': f"Unsupported HTTP method: {method}"}

            if is_mime and response.status_code == 200:
                return response

            if is_raw and response.status_code == 200:
                return response.content

            if response.status_code == 202 and method == 'POST':
                return {'success': True}

            if not response.text:
                return {'success': True}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 'Unknown'
            logger.error(f"Graph API HTTP Error {status_code}: {getattr(e.response, 'text', str(e))}")
            try:
                error_details = e.response.json()
            except Exception:
                error_details = getattr(e.response, 'text', str(e))

            return {'error': f"Graph API Error: Status {status_code}", 'details': error_details}

        except requests.exceptions.RequestException as e:
            logger.error(f"Network/Connection Error: {e}")
            return {'error': f"Network Error: {str(e)}"}

    @staticmethod
    def fetch_inbox_messages(target_email=None, top_count=100):
        """
        Fetches recent inbox messages for ingestion into local storage.
        Includes id, subject, from, toRecipients, ccRecipients, bccRecipients,
        receivedDateTime, bodyPreview, body, and hasAttachments.
        """
        endpoint = (
            f"mailFolders/inbox/messages?$top={top_count}"
            "&$select=id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,isRead,hasAttachments,bodyPreview,body"
            "&$orderby=receivedDateTime desc"
        )
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def fetch_message_details(target_email, message_id):
        """Fetches a single message's full metadata and HTML body for one-time local ingestion."""
        endpoint = (
            f"messages/{message_id}"
            "?$select=id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,hasAttachments,bodyPreview,body"
        )
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def fetch_attachments(*args, **kwargs):
        """
        Fetches ONLY attachment metadata (including isInline and contentId for CID images)
        so binary payloads are never pulled into RAM as JSON base64 strings.
        """
        if len(args) == 2:
            target_email, message_id = args
        elif len(args) == 1:
            target_email, message_id = None, args[0]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')

        endpoint = f"messages/{message_id}/attachments?$select=id,name,contentType,size,isInline,microsoft.graph.fileAttachment/contentId"
        response = OutlookGraphService._make_graph_request(endpoint, target_email)
        return response.get('value', []) if isinstance(response, dict) else []

    @staticmethod
    def stream_attachment_mime(target_email, message_id, attachment_id, chunk_size=8192):
        """
        Streams the raw binary content of an attachment in 8 KB chunks directly
        from Graph's /$value endpoint to prevent RAM spikes.
        """
        endpoint = f"messages/{message_id}/attachments/{attachment_id}/$value"
        response = OutlookGraphService._make_graph_request(endpoint, target_email, method='GET', is_mime=True)

        if not response or (isinstance(response, dict) and 'error' in response):
            logger.error(f"Error initiating stream for attachment {attachment_id}: {response}")
            return None

        def file_iterator():
            try:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk
            finally:
                response.close()

        return file_iterator()

    @staticmethod
    def stream_raw_eml(target_email, message_id, chunk_size=8192):
        """
        Streams the raw RFC822 MIME (.eml) content of an email in 8 KB chunks
        directly from Graph's /$value endpoint to disk without loading into RAM.
        """
        endpoint = f"messages/{message_id}/$value"
        response = OutlookGraphService._make_graph_request(endpoint, target_email, method='GET', is_mime=True)

        if not response or (isinstance(response, dict) and 'error' in response):
            logger.error(f"Error initiating EML stream for message {message_id}: {response}")
            return None

        def eml_iterator():
            try:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk
            finally:
                response.close()

        return eml_iterator()

    @staticmethod
    def send_outlook_email(target_email=None, recipient_email=None, subject=None, body_content=None, content_type='HTML', attachments=None, cc_email=None, bcc_email=None, user=None):
        """
        Sends an email via Microsoft Graph and retrieves the matching item ID from Sent Items.
        """
        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', '')
        final_body = body_content or ""

        if user and content_type.upper() == 'HTML':
            final_body += get_user_signature(user)

        email_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": content_type,
                    "content": final_body
                },
                "toRecipients": _parse_recipients(recipient_email),
                "ccRecipients": _parse_recipients(cc_email),
                "bccRecipients": _parse_recipients(bcc_email),
                "attachments": []
            },
            "saveToSentItems": "true"
        }

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

        send_res = OutlookGraphService._make_graph_request("sendMail", mailbox, method='POST', data=email_data)

        if isinstance(send_res, dict) and 'error' in send_res:
            return {'success': False, 'error': send_res.get('error'), 'details': send_res.get('details')}

        # Retrieve the matching message ID from Sent Items by matching the subject
        time.sleep(1.5)
        try:
            sent_endpoint = "mailFolders/sentitems/messages?$top=5&$select=id,subject&$orderby=sentDateTime desc"
            sent_check = OutlookGraphService._make_graph_request(sent_endpoint, mailbox, method='GET')

            if isinstance(sent_check, dict) and 'value' in sent_check:
                for msg in sent_check['value']:
                    if (msg.get('subject') or '').strip() == (subject or '').strip():
                        return {
                            'success': True,
                            'id': msg['id'],
                            'message': 'Email sent and ID retrieved.'
                        }
                if len(sent_check['value']) > 0:
                    return {
                        'success': True,
                        'id': sent_check['value'][0]['id'],
                        'message': 'Email sent and fallback ID retrieved.'
                    }
        except Exception as e:
            logger.error(f"Sent Items ID retrieval failed: {e}")

        return {'success': True, 'id': None}

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