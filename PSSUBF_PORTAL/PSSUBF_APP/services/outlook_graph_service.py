import requests
import logging
from django.conf import settings
from .token_manager import get_current_access_token

logger = logging.getLogger(__name__)

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
    def send_outlook_email(sender, recipient, subject, body, attachments=None):
        """
        Sends an email via Microsoft Graph API.
        Supports HTML body and Base64 attachments.
        """
        endpoint = "sendMail"
        message_payload = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body
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
    def fetch_inbox_messages(top_count=50):
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