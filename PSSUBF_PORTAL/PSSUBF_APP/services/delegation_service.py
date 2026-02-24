import json
from django.utils import timezone
from django.db import transaction
import logging

# IMPORT LOGIC: Using PSSUBF models
from PSSUBF_APP.models import PssubfInbox, PssubfDelegate, PssubfAction

logger = logging.getLogger(__name__)

@transaction.atomic
def delegate_pssubf_task(email_id, agent_name, delegator_user, form_data, is_recycle=False):
    """
    Moves an email status in PssubfInbox and creates/updates PssubfDelegate.
    Syncs the status to 'Recycled' to match the database state.
    """
    try:
        # 1. Determine Status and Agent
        final_status = 'Recycled' if is_recycle else 'Delegated'
        display_agent = agent_name if not is_recycle else "Recycle Bin"
        
        # 2. Fetch the Inbox Item to get Subject and Sender
        inbox_item = PssubfInbox.objects.get(email_id=email_id)
        
        # 3. Update status in unmanaged pssubf_inbox
        inbox_item.status = final_status
        inbox_item.save()

        # 4. Sync to unmanaged pssubf_delegate
        # update_or_create ensures we don't get duplicate primary key errors
        delegate_task, created = PssubfDelegate.objects.update_or_create(
            email_id=email_id,
            defaults={
                'assigned_agent': display_agent,
                'member_group_code': form_data.get('member_group_code'),
                'email_category': form_data.get('email_category'),
                'status': final_status,
                'subject': inbox_item.subject,
                'sender': inbox_item.sender,
            }
        )

        # 5. Log the action in unmanaged pssubf_actions
        PssubfAction.objects.create(
            task_email_id=email_id,
            action_type='Recycle' if is_recycle else 'Delegation',
            action_user=delegator_user.username,
            note_content=f"PSSUBF Task {final_status} by {delegator_user.username}",
            action_timestamp=timezone.now()
        )

        return True, f"PSSUBF Task Successfully {final_status}"

    except PssubfInbox.DoesNotExist:
        error_msg = f"Email ID {email_id} not found in PssubfInbox."
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        logger.error(f"PSSUBF Delegation failed for {email_id}: {e}")
        return False, str(e)