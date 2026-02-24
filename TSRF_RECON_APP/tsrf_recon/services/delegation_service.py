from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from dateutil import parser

# Corrected Imports for TSRF_RECON_APP
from tsrf_recon.models import EmailDelegation, DelegationNote, EmailTransaction

User = get_user_model()

def get_or_create_delegation_status(email_id, received_date_str=None):
    """
    Retrieves the existing EmailDelegation record or creates a new one 
    with status 'NEW' and saves the received date if provided.
    """
    try:
        # Check if a record already exists for this Graph API email ID
        delegation = EmailDelegation.objects.get(email_id=email_id)
    except EmailDelegation.DoesNotExist:
        # Prepare defaults for the new database row
        defaults = {'status': 'NEW'}
        
        # Parse the received date from Microsoft Graph (ISO format)
        if received_date_str:
            try:
                defaults['received_at'] = parser.isoparse(received_date_str)
            except Exception as e:
                print(f"Error parsing date {received_date_str} for {email_id}: {e}")
        
        # Create the record in 'tsrf_email_delegation' table
        delegation = EmailDelegation.objects.create(email_id=email_id, **defaults)
        
    return delegation

@transaction.atomic
def delegate_email_task(email_id, assigned_user_pk, delegator_user, classification_data):
    """
    Assigns an email task to a user, classifies it, and sets status to 'DEL'.
    """
    try:
        # 1. Ensure the delegation record exists in our DB
        deleg = get_or_create_delegation_status(email_id)
        
        # 2. Prevent re-delegating tasks that are already being worked on
        if deleg.status not in ['NEW', 'DEL']:
            return False, f"Task cannot be delegated. Current status: {deleg.get_status_display()}"
            
        # 3. Fetch the agent (User) to be assigned
        assigned_user = User.objects.get(pk=assigned_user_pk)
        
        # 4. Map classification data to the TSRF model fields
        # Note: mapping 'company_code' to the 'company_code' field in your SQL table
        deleg.assigned_user = assigned_user
        deleg.status = 'DEL'
        deleg.company_code = classification_data.get('company_code')
        deleg.email_category = classification_data.get('email_category')
        
        # Communication type and work related logic
        # Your SQL table might need 'communication_type' added if not already there
        if hasattr(deleg, 'communication_type'):
            deleg.communication_type = classification_data.get('comm_type')
        
        deleg.work_related = classification_data.get('work_related') == 'Yes'
        
        deleg.save()

        # 5. Log the assignment as an internal note for audit purposes
        DelegationNote.objects.create(
            delegation=deleg,
            user=delegator_user,
            content=f"Delegated to {assigned_user.username}. Category: {deleg.email_category}",
            action_type="Assignment"
        )

        return True, f"Task successfully delegated to {assigned_user.username}."

    except User.DoesNotExist:
        return False, "Assigned user not found."
    except Exception as e:
        print(f"ERROR during delegation of {email_id}: {e}")
        return False, f"An unexpected error occurred: {str(e)}"

def add_delegation_note(delegation_id, user, content):
    """Adds a note against a delegated email task in 'tsrf_delegation_note'."""
    if not content:
        return False, "Note content cannot be empty."
    try:
        delegation = EmailDelegation.objects.get(pk=delegation_id)
        DelegationNote.objects.create(
            delegation=delegation,
            user=user,
            content=content,
            action_type='Note'
        )
        return True, "Note added successfully."
    except EmailDelegation.DoesNotExist:
        return False, "Delegation record not found."

def get_delegated_emails_for_user(user):
    """Retrieves all active email tasks delegated to the current user."""
    return EmailDelegation.objects.filter(
        assigned_user=user,
        status='DEL'
    ).order_by('-received_at')
    
def log_delegation_transaction(delegation_id, user, subject, recipient_email, action_type='Reply Sent'):
    """
    Creates a record in the 'tsrf_email_transaction' table.
    """
    try:
        delegation = EmailDelegation.objects.get(pk=delegation_id)
        EmailTransaction.objects.create(
            delegation=delegation,
            user=user,
            subject=subject,
            recipient=recipient_email, # Matches 'recipient' column in your SQL
            action_type=action_type
        )
        return True, "Transaction logged successfully."
    except EmailDelegation.DoesNotExist:
        return False, "Delegation record not found."