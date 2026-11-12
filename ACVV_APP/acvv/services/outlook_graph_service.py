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
    if not user or not hasattr(user, 'username'):
        return ""

    username = user.username.lower()
    first_name = user.first_name.lower() if hasattr(user, 'first_name') and user.first_name else ""

    logo_url = "https://static.futurasa.co.za/images/futura-logo.png"

    base_disclaimer = """
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 11px; color: #333; margin-top: 15px;">
        <p>Futura SA is a Level 1 B-BBEE contributor, committed to transformation and inclusive growth.</p>
        <p style="font-size: 8.5px; color: #000; text-align: justify; line-height: 1.4;">
        <strong>Disclaimer:</strong> Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by the Financial Sector Conduct Authority in terms of the FAIS Act. License Number 18287 and a licensed Section 13B Administrator number 24/760. This transmission is confidential and intended solely for the person or organization to whom it is addressed. It may contain privileged and confidential information. If you are not the intended recipient, you should not copy, distribute or take any action in reliance on it. If you have received this transmission in error, please notify us immediately by e-mail at <a href="mailto:info@futurasa.co.za">info@futurasa.co.za</a>.
        </p>
    </div>
    """

    # Signature for Jesica
    if 'jesica' in username or 'jessica' in username or 'jesica' in first_name or 'jessica' in first_name:
        return f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 12px; color: #333; margin-top: 30px; padding-top: 15px;">
            <div style="color: #4CAF50; font-size: 15px; font-weight: bold; margin-bottom: 2px;">Jesica Haynes</div>
            <div style="margin-bottom: 12px; color: #333;">Reconciliations Specialist</div>
            <table style="border-collapse: collapse; margin-bottom: 10px;">
                <tr>
                    <td style="padding-right: 15px; border-right: 1px solid #a3a3a3; vertical-align: middle;">
                        <img src="{logo_url}" alt="Futura" width="130" style="display: block;">
                    </td>
                    <td style="padding-left: 15px; font-size: 12px; vertical-align: middle; line-height: 1.5;">
                        <div><span style="color: #4CAF50;">phone:</span> 087 702 5941 (direct)</div>
                        <div><span style="color: #4CAF50;">phone:</span> 087 702 2320 (switchboard)</div>
                        <div><span style="color: #4CAF50;">email:</span> <a href="mailto:acvv@futurasa.co.za" style="color: #1e88e5; text-decoration: underline;">acvv@futurasa.co.za</a></div>
                    </td>
                </tr>
            </table>
            {base_disclaimer}
        </div>
        """
    # Signature for Timothy
    elif 'timothy' in username or 'timothy' in first_name:
        return f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 12px; color: #333; margin-top: 30px; padding-top: 15px;">
            <div style="color: #4CAF50; font-size: 15px; font-weight: bold; margin-bottom: 2px;">Timothy Davids</div>
            <div style="margin-bottom: 12px; color: #333;">Indexing Specialist</div>
            <table style="border-collapse: collapse; margin-bottom: 10px;">
                <tr>
                    <td style="padding-right: 15px; border-right: 1px solid #a3a3a3; vertical-align: middle;">
                        <img src="{logo_url}" alt="Futura" width="130" style="display: block;">
                    </td>
                    <td style="padding-left: 15px; font-size: 12px; vertical-align: middle; line-height: 1.5;">
                        <div><span style="color: #4CAF50;">email:</span> <a href="mailto:acvv@futurasa.co.za" style="color: #1e88e5; text-decoration: underline;">acvv@futurasa.co.za</a></div>
                    </td>
                </tr>
            </table>
            {base_disclaimer}
        </div>
        """
    return ""


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
    """
    A service class to wrap Graph API calls, ensuring a consistent
    API-first approach for all Outlook interactions.
    """

    @staticmethod
    def _make_graph_request(endpoint, target_email=None, method='GET', data=None, is_mime=False, is_raw=False):
        """
        Unified request handler using System Service Token with dynamic target_email fallback.
        Handles both JSON responses and raw MIME streams ($value).
        """
        access_token = get_current_access_token()
        if not access_token:
            logger.error("Authentication failed: Missing or expired token.")
            return {'error': 'Authentication failed: Missing or expired token.'}

        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'lorraine@futurasa.co.za')
        url = f"{GRAPH_API_URL}/users/{mailbox}/{endpoint}"
        
        stream_mode = bool(is_mime or is_raw)

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Prefer': 'IdType="ImmutableId", outlook.timezone="South Africa Standard Time"'
        }
        
        if not stream_mode:
            headers['Content-Type'] = 'application/json'

        response = None
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=(5, 25), stream=stream_mode)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data if isinstance(data, dict) else None, timeout=(5, 25))
            else:
                return {'error': f"Unsupported HTTP method: {method}"}
            
            # If we requested a MIME stream ($value), return the active response object so iter_content can stream it
            if stream_mode and response.status_code == 200:
                return response

            if response.status_code == 202 and method == 'POST':
                return {'success': True}

            if response.status_code == 202 or not response.text:
                return {}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 'Unknown'
            logger.error(f"Graph API HTTP Error {status_code}: {e.response.text if e.response is not None else str(e)}")

            try:
                error_details = e.response.json() if e.response is not None else str(e)
            except Exception:
                error_details = e.response.text if (e.response is not None and e.response.text) else str(e)

            return {'error': f"Graph API Error: Status {status_code}", 'details': error_details}

        except requests.exceptions.RequestException as e:
            logger.error(f"Network/Connection Error: {e}")
            return {'error': f"Network Error: {str(e)}"}

    @staticmethod
    def fetch_outlook_data(endpoint, target_email=None):
        """Generic GET wrapper used across ACVV views."""
        return OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET')

    @staticmethod
    def fetch_inbox_messages(target_email=None, top_count=200):
        """
        Fetches recent emails for the live inbox.
        Excludes 'body' and 'bodyPreview' from $select to prevent large memory payloads on inbox load.
        """
        endpoint = (
            f"mailFolders/inbox/messages?$top={top_count}"
            f"&$select=id,subject,from,receivedDateTime,isRead,hasAttachments,ccRecipients,bccRecipients"
            f"&$orderby=receivedDateTime desc"
        )
        return OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET')

    @staticmethod
    def fetch_message_details(target_email, message_id):
        endpoint = f"messages/{message_id}"
        return OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET')

    @staticmethod
    def fetch_attachments(*args, **kwargs):
        """
        Fetches ONLY attachment metadata (id, name, contentType, size) so opening an email
        never downloads full attachment binaries into server RAM.
        """
        if len(args) == 2:
            target_email, message_id = args
        elif len(args) == 1:
            target_email, message_id = None, args[0]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')

        endpoint = f"messages/{message_id}/attachments?$select=id,name,contentType,size"
        response = OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET')
        return response.get('value', []) if isinstance(response, dict) else []

    @staticmethod
    def get_attachment_raw(*args, **kwargs):
        """Raw bytes/metadata for a single attachment with flexible argument parsing."""
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
    def stream_attachment_mime(target_email, message_id, attachment_id, chunk_size=8192):
        """
        Streams the raw binary content of an attachment in 8 KB chunks directly
        from the /$value endpoint to prevent RAM exhaustion and 502 crashes.
        """
        endpoint = f"messages/{message_id}/attachments/{attachment_id}/$value"
        response = OutlookGraphService._make_graph_request(
            endpoint, target_email=target_email, method='GET', is_mime=True
        )

        if not response or (isinstance(response, dict) and 'error' in response):
            err = response.get('error') if isinstance(response, dict) else 'Unknown stream error'
            logger.error(f"Error initiating stream for attachment {attachment_id}: {err}")
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
    def get_attachment_mime(*args, **kwargs):
        """Fetches raw attachment bytes ($value) with flexible argument parsing."""
        if len(args) == 3:
            target_email, message_id, attachment_id = args
        elif len(args) == 2:
            target_email, message_id, attachment_id = None, args[0], args[1]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')
            attachment_id = kwargs.get('attachment_id')

        endpoint = f"messages/{message_id}/attachments/{attachment_id}/$value"
        response = OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET', is_mime=True)
        if hasattr(response, 'content'):
            try:
                return response.content
            finally:
                response.close()
        return response

    @staticmethod
    def fetch_raw_eml(*args, **kwargs):
        """Fetches raw RFC822 MIME content ($value) for downloading .eml files in ACVV."""
        if len(args) == 2:
            target_email, message_id = args
        elif len(args) == 1:
            target_email, message_id = None, args[0]
        else:
            target_email = kwargs.get('target_email')
            message_id = kwargs.get('message_id')

        endpoint = f"messages/{message_id}/$value"
        response = OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET', is_mime=True)
        if hasattr(response, 'content'):
            try:
                return response.content
            finally:
                response.close()
        return response

    @staticmethod
    def get_email_mime_content(*args, **kwargs):
        """Alias for fetch_raw_eml for cross-app compatibility."""
        return OutlookGraphService.fetch_raw_eml(*args, **kwargs)

    @staticmethod
    def send_outlook_email(target_email=None, recipient_email=None, subject=None, body_content=None, content_type='HTML', attachments=None, cc=None, bcc=None, cc_email=None, bcc_email=None, user=None):
        """
        Sends an email from the target mailbox with support for multiple attachments, CC, and BCC.
        """
        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'lorraine@futurasa.co.za')
        final_cc = cc if cc is not None else cc_email
        final_bcc = bcc if bcc is not None else bcc_email
        final_body = body_content or ""

        if user and content_type.upper() == 'HTML':
            final_body += get_user_signature(user)

        email_data = {
            "message": {
                "subject": subject,
                "body": {"contentType": content_type, "content": final_body},
                "toRecipients": _parse_recipients(recipient_email),
                "ccRecipients": _parse_recipients(final_cc),
                "bccRecipients": _parse_recipients(final_bcc),
                "attachments": []
            },
            "saveToSentItems": "true"
        }

        if attachments:
            for file in attachments:
                try:
                    file.seek(0)
                    encoded_content = base64.b64encode(file.read()).decode('utf-8')
                    attachment_content_type = getattr(file, 'content_type', '')
                    if not attachment_content_type or attachment_content_type == 'application/octet-stream':
                        attachment_content_type, _ = mimetypes.guess_type(file.name)
                    if not attachment_content_type:
                        attachment_content_type = 'application/octet-stream'

                    email_data["message"]["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": getattr(file, 'name', 'attachment'),
                        "contentType": attachment_content_type,
                        "contentBytes": encoded_content
                    })
                except Exception as e:
                    logger.error(f"Failed to process attachment {getattr(file, 'name', 'unknown')}: {e}")

        result = OutlookGraphService._make_graph_request("sendMail", target_email=mailbox, method='POST', data=email_data)

        if isinstance(result, dict) and 'error' in result:
            return {'success': False, 'error': result.get('error')}

        # Safely check recent Sent Items ONLY for a message whose subject matches what we just sent
        time.sleep(1.5)
        try:
            sent_endpoint = "mailFolders/sentitems/messages?$top=5&$select=id,subject&$orderby=sentDateTime desc"
            sent_check = OutlookGraphService._make_graph_request(sent_endpoint, target_email=mailbox, method='GET')
            if isinstance(sent_check, dict) and 'value' in sent_check:
                for msg in sent_check['value']:
                    if (msg.get('subject') or '').strip() == (subject or '').strip():
                        message_id = msg['id']
                        return {
                            'success': True,
                            'id': message_id,
                            'message_id': message_id,
                            'outlook_id': message_id,
                        }
        except Exception as e:
            logger.warning(f"Sent item ID lookup skipped: {e}")

        # If not yet indexed in Sent Items, return success without a mismatched Graph ID
        return {'success': True, 'id': None, 'message_id': None}