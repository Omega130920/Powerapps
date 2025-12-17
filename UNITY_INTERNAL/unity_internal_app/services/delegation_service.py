from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from dateutil import parser
import logging

# 1. To import from models.py (one level up)
from ..models import EmailDelegation, DelegationNote, DelegationTransactionLog 
# 2. To import from outlook_graph_service.py (in the same 'services' directory)
from .outlook_graph_service import OutlookGraphService 

User = get_user_model()
logger = logging.getLogger(__name__)


def get_or_create_delegation_status(email_id, received_date_str=None):
    """
    Retrieves the existing EmailDelegation record or creates a new one 
    with status 'NEW' and saves the received date if provided.
    """
    try:
        delegation = EmailDelegation.objects.get(email_id=email_id)
        created = False
    except EmailDelegation.DoesNotExist:
        created = True
        
        # Determine defaults for creation
        defaults = {'status': 'NEW'}
        
        # 🛑 Save received_at ONLY upon creation 🛑
        if received_date_str:
            try:
                # Parse the ISO datetime string from the Graph API
                defaults['received_at'] = parser.isoparse(received_date_str)
            except Exception as e:
                logger.warning(f"Error parsing date {received_date_str} for {email_id}: {e}")
                # We ignore the date if parsing fails, using NULL
        
        # Create the new record
        delegation = EmailDelegation.objects.create(email_id=email_id, **defaults)
        
    return delegation

@transaction.atomic
def delegate_email_task(email_id, assigned_user_pk, delegator_user, classification_data):
    """
    Assigns an email task to a user, classifies it using the provided data, 
    and sets the status to 'Delegated'.
    """
    try:
        # 1. Get/Create the delegation record 
        delegation = get_or_create_delegation_status(email_id)
        
        # 2. Check current status
        if delegation.status != 'NEW':
            return False, f"Task status is already {delegation.get_status_display()}."
            
        # 3. Get the assignee user object
        assigned_user = User.objects.get(pk=assigned_user_pk)
        
        # 4. Perform the delegation update AND save classification data
        delegation.assigned_user = assigned_user
        delegation.status = 'DEL'  # Set status to Delegated
        delegation.delegated_at = timezone.now()
        
        # 🛑 SAVING NEW CLASSIFICATION DATA 🛑
        # work_related is a Boolean field (we check if the form value is 'Yes')
        delegation.work_related = classification_data.get('work_related') == 'Yes'
        delegation.email_category = classification_data.get('email_category')
        delegation.communication_type = classification_data.get('comm_type')
        # CORRECTED: Use 'company_code' key from input and save to 'company_code' model field
        delegation.company_code = classification_data.get('company_code') 
        
        delegation.save()

        # Optional: Log delegation as a note (internal record)
        DelegationNote.objects.create(
            delegation=delegation,
            user=delegator_user,
            content=(
                f"Delegated to {assigned_user.username}. "
                f"Category: {delegation.email_category}, "
                f"Company Code: {delegation.company_code or 'None'}" # <-- CORRECTED LOG MESSAGE
            )
        )

        return True, f"Task successfully delegated to {assigned_user.username}."

    except User.DoesNotExist:
        return False, "Assigned user not found."
    except Exception as e:
        # Log the full exception detail for server debugging
        logger.exception(f"ERROR during delegation of {email_id}")
        return False, f"An unexpected error occurred during delegation: {e}"

def add_delegation_note(delegation_id, user, content):
    """Adds a note against a delegated email task."""
    if not content:
        return False, "Note content cannot be empty."
        
    try:
        delegation = EmailDelegation.objects.get(pk=delegation_id)
        
        DelegationNote.objects.create(
            delegation=delegation,
            user=user,
            content=content
        )
        return True, "Note added successfully."
        
    except EmailDelegation.DoesNotExist:
        return False, "Delegation record not found."

def get_delegated_emails_for_user(user):
    """Retrieves all active email tasks delegated to the current user."""
    return EmailDelegation.objects.filter(
        assigned_user=user,
        status__in=['DEL'] # Only show currently delegated/active tasks
    ).order_by('-delegated_at')
    
def log_delegation_transaction(delegation_id, user, subject, recipient_email, action_type='EMAIL_REPLY'):
    """Creates a record in the DelegationTransactionLog."""
    try:
        delegation = EmailDelegation.objects.get(pk=delegation_id)
        DelegationTransactionLog.objects.create(
            delegation=delegation,
            user=user,
            subject=subject,
            recipient_email=recipient_email,
            action_type=action_type
        )
        return True, "Transaction logged successfully."
    except EmailDelegation.DoesNotExist:
        return False, "Delegation record not found for logging."
    except Exception as e:
        logger.exception("Error logging delegation transaction")
        return False, f"Error logging transaction: {e}"