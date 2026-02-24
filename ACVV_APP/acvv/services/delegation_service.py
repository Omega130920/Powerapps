from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from acvv.models import DelegationTransactionLog, EmailDelegation, DelegationNote
from acvv.services.outlook_graph_service import fetch_inbox_messages # Needed if we embed complex logic
from dateutil import parser

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
                print(f"Error parsing date {received_date_str} for {email_id}: {e}")
                # We ignore the date if parsing fails, using NULL
        
        # Create the new record
        delegation = EmailDelegation.objects.create(email_id=email_id, **defaults)
        
    # NOTE: We skip using .get_or_create() as the custom logic for date parsing 
    # and setting defaults is clearer with the try/except block.

    return delegation

@transaction.atomic
def delegate_email_task(email_id, assigned_user_pk, delegator_user, classification_data):
    """
    Assigns an email task to a user, classifies it using the provided data, and sets the status to 'Delegated'.
    """
    try:
        # 1. Get/Create the delegation record 
        # (Implementation assumed to be in get_or_create_delegation_status)
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
        delegation.mip_names = classification_data.get('mip_names') # Save MIP Names/Group Code
        
        delegation.save()

        # Optional: Log delegation as a note (internal record)
        DelegationNote.objects.create(
            delegation=delegation,
            user=delegator_user,
            content=(
                f"Delegated to {assigned_user.username}. "
                f"Category: {delegation.email_category}, "
                f"MIP: {delegation.mip_names or 'None'}"
            )
        )

        return True, f"Task successfully delegated to {assigned_user.username}."

    except User.DoesNotExist:
        return False, "Assigned user not found."
    except Exception as e:
        # Log the full exception detail for server debugging
        print(f"ERROR during delegation of {email_id}: {e}")
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
        return False, f"Error logging transaction: {e}"