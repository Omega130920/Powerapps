
# Delegation_Service.py


import json
from django.utils import timezone
from django.db import transaction
import logging

from ..models import CrmInbox, CrmDelegateTo, CrmDelegateAction

logger = logging.getLogger(__name__)

@transaction.atomic
def delegate_email_task(email_id, agent_name, delegator_user, form_data, is_recycle=False):
    """
    Moves an email status in CrmInbox and creates/updates CrmDelegateTo.
    FIX: Removed 'is_recycled' to prevent DB errors since column does not exist.
    """
    try:
        # Determine values based on whether we are recycling or delegating
        final_status = 'Recycled' if is_recycle else 'Delegated'
        display_agent = agent_name if not is_recycle else "Recycle Bin"
        
        # 1. Update master status in CrmInbox
        inbox_item = CrmInbox.objects.get(email_id=email_id)
        inbox_item.status = final_status
        inbox_item.delegated_by = delegator_user.username
        inbox_item.delegated_to = display_agent
        
        group_code = form_data.get('member_group_code')
        inbox_item.member_group_code = group_code 
        inbox_item.save()

        # 2. Sync to CrmDelegateTo
        # IMPORTANT: 'is_recycled' is REMOVED from the defaults dictionary below
        delegate_task, _ = CrmDelegateTo.objects.update_or_create(
            email_id=email_id,
            defaults={
                'subject': inbox_item.subject,
                'sender': inbox_item.sender,
                'snippet': inbox_item.snippet,
                'status': final_status,  # We use the existing status column
                'delegated_by': delegator_user.username,
                'delegated_to': display_agent,
                'work_related': form_data.get('work_related', 'Yes'),
                'member_group_code': group_code,
                'category': form_data.get('category'),
                'type': form_data.get('type'),
                'method': form_data.get('method', 'Email'),
                'internal_notes': json.dumps([]) 
            }
        )

        # 3. Log the action in CrmDelegateAction
        CrmDelegateAction.objects.create(
            task_email_id=email_id,
            action_type='Recycle' if is_recycle else 'Delegation',
            action_user=delegator_user.username,
            note_content=f"Task {final_status} by {delegator_user.username}"
        )

        return True, f"Task Successfully {final_status}"

    except Exception as e:
        logger.error(f"Delegation/Recycle failed for {email_id}: {e}")
        return False, str(e)

def add_action_note(email_id, user, content):
    """Logs a note in both the Task JSON and the Action Audit table."""
    try:
        task = CrmDelegateTo.objects.get(email_id=email_id)
        
        # Update JSON internal_notes in CrmDelegateTo
        notes = json.loads(task.internal_notes or '[]')
        notes.append({
            'user': user.username,
            'timestamp': timezone.now().isoformat(),
            'content': content
        })
        task.internal_notes = json.dumps(notes)
        task.save()

        # Create individual audit entry in CrmDelegateAction for reporting
        CrmDelegateAction.objects.create(
            task_email_id=email_id,
            action_type='Add Note',
            action_user=user.username,
            note_content=content
        )
        return True
    except Exception as e:
        logger.error(f"Failed to add note for {email_id}: {e}")
        return False