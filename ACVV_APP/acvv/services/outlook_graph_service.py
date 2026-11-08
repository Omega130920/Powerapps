import base64
import json
import logging
import mimetypes
import requests

from django.conf import settings

# Initialize logger
logger = logging.getLogger(__name__)

# The base URL for the Microsoft Graph API
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"


def get_user_signature(user):
    """Generates the specific HTML signature based on the logged-in user."""
    if not user or not hasattr(user, 'username'):
        return ""

    username = user.username.lower()
    first_name = user.first_name.lower() if user.first_name else ""

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
    def _make_graph_request(endpoint, target_email=None, method='GET', data=None, is_raw=False):
        """
        Generic internal function to handle authenticated requests with timeout protection.
        """
        from .token_manager import get_current_access_token

        access_token = get_current_access_token()
        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'lorraine@futurasa.co.za')

        if not access_token:
            logger.error("Authentication failed: Missing or expired token.")
            return {'error': 'Authentication failed: Missing or expired token.'}

        url = f"{GRAPH_API_URL}/users/{mailbox}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Prefer': 'IdType="ImmutableId"'
        }

        if not is_raw:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=(5, 25))
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=json.dumps(data) if isinstance(data, dict) else None, timeout=(5, 25))
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
    def fetch_outlook_data(endpoint, target_email=None):
        return OutlookGraphService._make_graph_request(endpoint, target_email, method='GET')

    @staticmethod
    def fetch_inbox_messages(target_email=None, top_count=10):
        endpoint = f"mailFolders/inbox/messages?$top={top_count}&$select=subject,from,receivedDateTime,isRead,body&$orderby=receivedDateTime desc"
        return OutlookGraphService._make_graph_request(endpoint, target_email)

    @staticmethod
    def fetch_message_details(target_email, message_id):
        endpoint = f"messages/{message_id}"
        return OutlookGraphService._make_graph_request(endpoint, target_email)

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

    @staticmethod
    def send_outlook_email(target_email=None, recipient_email=None, subject=None, body_content=None, content_type='HTML', attachments=None, cc=None, bcc=None, user=None):
        """
        Sends an email from the target mailbox with support for multiple attachments, CC, and BCC.
        """
        mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'lorraine@futurasa.co.za')

        if user and content_type.upper() == 'HTML':
            signature = get_user_signature(user)
            body_content += signature

        email_data = {
            "message": {
                "subject": subject,
                "body": {"contentType": content_type, "content": body_content},
                "toRecipients": _parse_recipients(recipient_email),
                "ccRecipients": _parse_recipients(cc),
                "bccRecipients": _parse_recipients(bcc),
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
                        "name": file.name,
                        "contentType": attachment_content_type,
                        "contentBytes": encoded_content
                    })
                except Exception as e:
                    logger.error(f"Failed to process attachment {getattr(file, 'name', 'unknown')}: {e}")

        return OutlookGraphService._make_graph_request("sendMail", mailbox, method='POST', data=email_data)