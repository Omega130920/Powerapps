import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil import parser
from crm_core.models import CrmInbox, CrmDelegateTo
from crm_core.services.outlook_graph_service import OutlookGraphService

logger = logging.getLogger(__name__)

def extract_addresses(recipient_list):
    """Safely extracts comma-separated email addresses from Microsoft Graph recipient array."""
    if not recipient_list or not isinstance(recipient_list, list):
        return ""
    addresses = [
        item.get('emailAddress', {}).get('address', '').strip()
        for item in recipient_list
        if item.get('emailAddress', {}).get('address')
    ]
    return ", ".join(filter(None, addresses))

class Command(BaseCommand):
    help = 'Auto-downloads incoming emails from Microsoft Graph API and saves full bodies, CC, and BCC to MySQL'

    def handle(self, *args, **options):
        self.stdout.write("Starting Outlook email synchronization...")
        
        inbox_data = OutlookGraphService.fetch_inbox_messages(top_count=100)
        
        if 'error' in inbox_data:
            self.stderr.write(self.style.ERROR(f"Outlook Error: {inbox_data['error']}"))
            return

        emails = inbox_data.get('value', [])
        delegated_ids = set(CrmDelegateTo.objects.values_list('email_id', flat=True))
        
        new_count = 0
        updated_count = 0

        for msg in emails:
            email_id = msg.get('id')
            
            # Skip if already fully delegated
            if email_id in delegated_ids:
                continue
                
            raw_date = msg.get('receivedDateTime')
            local_date = timezone.localtime(parser.isoparse(raw_date)) if raw_date else None
            
            # Extract HTML body safely
            body_content = msg.get('body', {}).get('content', '')

            # 🟢 EXTRACT CC AND BCC RECIPIENTS
            cc_str = extract_addresses(msg.get('ccRecipients', []))
            bcc_str = extract_addresses(msg.get('bccRecipients', []))

            # Check if it exists in CrmInbox
            existing_entry = CrmInbox.objects.filter(email_id=email_id).first()

            if existing_entry:
                # Update existing entry if missing HTML body or CC/BCC (backward compatibility rollout)
                if not existing_entry.body_html or existing_entry.cc_recipients is None:
                    existing_entry.body_html = body_content
                    existing_entry.has_attachments = msg.get('hasAttachments', False)
                    existing_entry.cc_recipients = cc_str
                    existing_entry.bcc_recipients = bcc_str
                    existing_entry.save()
                    updated_count += 1
            else:
                # Create brand new local entry
                CrmInbox.objects.create(
                    email_id=email_id,
                    subject=msg.get('subject', 'No Subject'),
                    sender=msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown'),
                    snippet=msg.get('bodyPreview', ''),
                    body_html=body_content,
                    has_attachments=msg.get('hasAttachments', False),
                    cc_recipients=cc_str,
                    bcc_recipients=bcc_str,
                    received_timestamp=local_date,
                    status='Pending'
                )
                new_count += 1

        self.stdout.write(self.style.SUCCESS(f"Sync complete: {new_count} new, {updated_count} updated."))