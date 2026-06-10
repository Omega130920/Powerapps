import requests
import json
import base64
import logging
from django.conf import settings
from .token_manager import get_current_access_token 

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

    # Replace with the direct link to the Futura logo hosted on your server
    logo_url = "https://futurasa.co.za/wp-content/uploads/2021/04/futura-logo.png"

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

class OutlookGraphService:
    @staticmethod
    def _make_graph_request(endpoint, target_email, method='GET', data=None, is_raw=False):
        access_token = get_current_access_token()
        if not access_token:
            logger.error("Authentication failed: Missing or expired token.")
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
            if is_raw: return response.content
            if response.status_code == 202 and method == 'POST': return {'success': True}
            return response.json()
        except Exception as e:
            logger.error(f"Graph API Error: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def send_outlook_email(target_email, recipient_email, subject, body_content, content_type='HTML', attachments=None, user=None):
        """
        Sends an email from the target mailbox with automatic signature injection.
        """
        # Inject Signature if user is provided
        if user and content_type.upper() == 'HTML':
            signature = get_user_signature(user)
            body_content += signature

        if isinstance(recipient_email, str):
            addresses = [email.strip() for email in recipient_email.split(',') if email.strip()]
        elif isinstance(recipient_email, list):
            addresses = [email.strip() for email in recipient_email if isinstance(email, str)]
        else:
            addresses = []

        email_data = {
            "message": {
                "subject": subject,
                "body": {"contentType": content_type, "content": body_content},
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in addresses],
                "attachments": [] 
            },
            "saveToSentItems": "true" 
        }

        if attachments:
            for file in attachments:
                try:
                    file.seek(0)
                    encoded_content = base64.b64encode(file.read()).decode('utf-8')
                    email_data["message"]["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": file.name,
                        "contentType": getattr(file, 'content_type', 'application/octet-stream'),
                        "contentBytes": encoded_content
                    })
                except Exception as e:
                    logger.error(f"Failed to process attachment {getattr(file, 'name', 'unknown')}: {e}")
        
        return OutlookGraphService._make_graph_request("sendMail", target_email, method='POST', data=email_data)