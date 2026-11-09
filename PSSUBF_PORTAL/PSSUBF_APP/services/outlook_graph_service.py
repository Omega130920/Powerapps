import requests
import logging
from django.conf import settings
from django.template.loader import render_to_string
from .token_manager import get_current_access_token

logger = logging.getLogger(__name__)

def get_user_email_signature(user):
    """
    Maps system usernames to Full Names and renders the email signature template.
    """
    if not user:
        full_name = "PSSUBF Administrator"
    else:
        username = user.username if hasattr(user, 'username') else str(user)
        
        # Map system usernames to the full name that should display in the signature
        name_mapping = {
            'LuanovanEck': 'Luano van Eck',
            'Testuser1': 'Test Agent',
            'omega': 'Omega System Assistant',
        }
        
        # Fallback to the username nicely formatted if not explicitly mapped
        full_name = name_mapping.get(username, username.replace('_', ' ').title())
    
    context = {
        'agent_full_name': full_name,
    }
    
    # Renders signature template located at pssubf/pssubf_email_signature.html
    try:
        return render_to_string('pssubf/pssubf_email_signature.html', context)
    except Exception as e:
        logger.error(f"Error rendering email signature template: {e}")
        return f"<br><br><p>Kind regards,<br><strong>{full_name}</strong><br>PSSUBF Administrators</p>"


class OutlookGraphService:
    @staticmethod
    def _make_graph_request(endpoint, method='GET', data=None, params=None):
        """
        Unified request handler using PSSUBF Service Token.
        Includes a mandatory 30-second timeout guardrail on all external calls.
        """
        access_token = get_current_access_token()
        if not access_token:
            return {'error': 'Could not acquire PSSUBF access token'}

        url = f"https://graph.microsoft.com/v1.0/users/{settings.OUTLOOK_EMAIL_ADDRESS}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        try:
            # 🟢 TIMEOUT GUARDRAIL: Enforces 30s connection/read timeout on all requests
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)
            
            # 202 Accepted (common for sendMail) returns empty text
            if response.status_code == 202 or not response.text:
                return {}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"PSSUBF Graph Request Timeout (30s) on endpoint: {endpoint}")
            return {'error': 'Microsoft Graph API request timed out after 30 seconds.'}
        except Exception as e:
            logger.error(f"PSSUBF Graph Request Error: {e}")
            return {'error': str(e)}

    @staticmethod
    def send_outlook_email(sender, recipient, subject, body, cc=None, bcc=None, attachments=None, user=None):
        """
        Sends an email via Microsoft Graph API.
        Supports HTML body, Base64 attachments, CC, BCC, and automatically appends 
        the user's personalized HTML signature if a user is provided.
        """
        endpoint = "sendMail"
        
        # Automatically append the agent's signature if user context is provided
        final_body = body
        if user:
            signature_html = get_user_email_signature(user)
            final_body = body + signature_html

        message_payload = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": final_body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient
                    }
                }
            ]
        }

        # Handle CC recipients (allows comma-separated multiple emails)
        if cc:
            cc_list = [email.strip() for email in cc.split(',') if email.strip()]
            if cc_list:
                message_payload["ccRecipients"] = [
                    {"emailAddress": {"address": email}} for email in cc_list
                ]

        # Handle BCC recipients (allows comma-separated multiple emails)
        if bcc:
            bcc_list = [email.strip() for email in bcc.split(',') if email.strip()]
            if bcc_list:
                message_payload["bccRecipients"] = [
                    {"emailAddress": {"address": email}} for email in bcc_list
                ]

        # Add attachments if provided
        if attachments:
            message_payload["attachments"] = attachments

        payload = {
            "message": message_payload,
            "saveToSentItems": "true"
        }

        return OutlookGraphService._make_graph_request(endpoint, method='POST', data=payload)

    @staticmethod
    def fetch_inbox_messages(target_email, top_count=50):
        """
        Fetches messages from the Graph API.
        Selects only essential inbox header metadata.
        """
        endpoint = f"mailFolders/inbox/messages?$top={top_count}&$select=id,subject,from,receivedDateTime,bodyPreview"
        return OutlookGraphService._make_graph_request(endpoint, method='GET')

    @staticmethod
    def fetch_attachments(target_email, message_id):
        """
        Fetches attachment headers without downloading heavy base64 'contentBytes'.
        Keeps memory utilization negligible when viewing email threads.
        """
        endpoint = f"messages/{message_id}/attachments"
        # 🟢 MEMORY OPTIMIZATION: Excludes contentBytes payload from server RAM
        params = {'$select': 'id,name,contentType,size,isInline'}
        response = OutlookGraphService._make_graph_request(endpoint, method='GET', params=params)
        return response.get('value', [])
    
    @staticmethod
    def get_attachment_raw(target_email, message_id, attachment_id):
        """
        Retrieves raw attachment data including contentBytes (used for inline image rendering).
        """
        endpoint = f"messages/{message_id}/attachments/{attachment_id}"
        return OutlookGraphService._make_graph_request(endpoint, method='GET')