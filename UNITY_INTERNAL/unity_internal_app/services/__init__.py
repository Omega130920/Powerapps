# Import from the actual filename (outlook_graph_service.py)
from .outlook_graph_service import OutlookGraphService

# Keep your other services here too so views.py can find them
from .delegation_service import (
    get_or_create_delegation_status, 
    delegate_email_task, 
    add_delegation_note, 
    get_delegated_emails_for_user,
    log_delegation_transaction
)