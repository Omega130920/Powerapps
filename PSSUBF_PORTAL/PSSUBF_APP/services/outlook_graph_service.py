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
        
        # Map your system usernames to the full name that should display in the signature
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
    
    # Renders your signature template located at pssubf/pssubf_email_signature.html
    try:
        return render_to_string('pssubf/pssubf_email_signature.html', context)
    except Exception as e:
        logger.error(f"Error rendering email signature template: {e}")
        return f"<br><br><p>Kind regards,<br><strong>{full_name}</strong><br>PSSUBF Administrators</p>"


class OutlookGraphService:
    @staticmethod
    def _make_graph_request(endpoint, method='GET', data=None):
        """Unified request handler using PSSUBF Service Token."""
        access_token = get_current_access_token()
        if not access_token:
            return {'error': 'Could not acquire PSSUBF access token'}

        url = f"https://graph.microsoft.com/v1.0/users/{settings.OUTLOOK_EMAIL_ADDRESS}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers, json=data)
            
            # 202 Accepted (common for sendMail) returns empty text
            if response.status_code == 202 or not response.text:
                return {}

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"PSSUBF Graph Request Error: {e}")
            return {'error': str(e)}

    @staticmethod
    def send_outlook_email(sender, recipient, subject, body, attachments=None, user=None):
        """
        Sends an email via Microsoft Graph API.
        Supports HTML body, Base64 attachments, and automatically appends 
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
        Accepts target_email as first argument to fix the 400 Bad Request error
        caused by passing an email string into the $top parameter.
        """
        endpoint = f"mailFolders/inbox/messages?$top={top_count}&$select=id,subject,from,receivedDateTime,bodyPreview"
        return OutlookGraphService._make_graph_request(endpoint, method='GET')

    @staticmethod
    def fetch_attachments(target_email, message_id):
        endpoint = f"messages/{message_id}/attachments"
        response = OutlookGraphService._make_graph_request(endpoint, method='GET')
        return response.get('value', [])
    
    @staticmethod
    def get_attachment_raw(target_email, message_id, attachment_id):
        endpoint = f"messages/{message_id}/attachments/{attachment_id}"
        return OutlookGraphService._make_graph_request(endpoint, method='GET')