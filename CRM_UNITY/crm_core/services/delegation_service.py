# Delegation_Service.py

import json
import logging
from django.utils import timezone
from django.db import transaction

from ..models import CrmInbox, CrmDelegateTo, CrmDelegateAction

logger = logging.getLogger(__name__)


@transaction.atomic
def delegate_email_task(email_id, agent_name, delegator_user, form_data, is_recycle=False):
    """
    Moves an email status in CrmInbox and copies all local rendering data into CrmDelegateTo.
    Preserves existing internal_notes and received_timestamp when re-delegating.
    """
    try:
        final_status = 'Recycled' if is_recycle else 'Delegated'
        display_agent = agent_name if not is_recycle else "Recycle Bin"

        group_code = form_data.get('member_group_code')
        membership_num = form_data.get('membership_number')
        work_related = form_data.get('work_related', 'No' if is_recycle else 'Yes')
        category = form_data.get('category')
        enquiry_type = form_data.get('type')
        method = form_data.get('method', 'Email')

        # 1. Update master status & classification in CrmInbox
        inbox_item = CrmInbox.objects.get(email_id=email_id)
        inbox_item.status = final_status
        inbox_item.delegated_by = delegator_user.username
        inbox_item.delegated_to = display_agent
        inbox_item.work_related = work_related
        inbox_item.member_group_code = group_code
        inbox_item.category = category
        inbox_item.type = enquiry_type
        inbox_item.method = method
        inbox_item.save()

        # Check if task already exists in CrmDelegateTo so we don't wipe existing notes on re-delegation
        existing_task = CrmDelegateTo.objects.filter(email_id=email_id).first()
        preserved_notes = (
            existing_task.internal_notes
            if (existing_task and existing_task.internal_notes)
            else json.dumps([])
        )

        # 2. Sync complete email data to CrmDelegateTo so it never needs Graph API
        delegate_task, created = CrmDelegateTo.objects.update_or_create(
            email_id=email_id,
            defaults={
                'subject': inbox_item.subject,
                'sender': inbox_item.sender,
                'sender_name': inbox_item.sender_name,
                'snippet': inbox_item.snippet,
                'body_html': inbox_item.body_html,
                'has_attachments': inbox_item.has_attachments,
                'to_recipients': inbox_item.to_recipients,
                'cc_recipients': inbox_item.cc_recipients,
                'bcc_recipients': inbox_item.bcc_recipients,
                'eml_file_path': inbox_item.eml_file_path,
                'received_timestamp': existing_task.received_timestamp if existing_task else timezone.now(),
                'status': final_status,
                'delegated_by': delegator_user.username,
                'delegated_to': display_agent,
                'work_related': work_related,
                'member_group_code': group_code,
                'membership_number': membership_num,
                'category': category,
                'type': enquiry_type,
                'method': method,
                'internal_notes': preserved_notes,
            }
        )

        # 3. Log the action in CrmDelegateAction
        if is_recycle:
            action_label = 'Recycle'
            note_msg = f"Task Recycled by {delegator_user.username}"
        elif not created:
            action_label = 'Re-Delegation'
            note_msg = f"Task Re-delegated to {display_agent} by {delegator_user.username}"
        else:
            action_label = 'Delegation'
            note_msg = f"Task Delegated to {display_agent} by {delegator_user.username}"

        CrmDelegateAction.objects.create(
            task_email_id=email_id,
            action_type=action_label,
            action_user=delegator_user.username,
            note_content=note_msg
        )

        return True, f"Task Successfully {final_status}"

    except Exception as e:
        logger.error(f"Delegation/Recycle failed for {email_id}: {e}")
        return False, str(e)


def add_action_note(email_id, user, content):
    """Logs a note in both the Task JSON and the Action Audit table."""
    try:
        task = CrmDelegateTo.objects.get(email_id=email_id)

        notes = json.loads(task.internal_notes or '[]')
        notes.append({
            'user': user.username,
            'timestamp': timezone.now().isoformat(),
            'content': content
        })
        task.internal_notes = json.dumps(notes)
        task.save()

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