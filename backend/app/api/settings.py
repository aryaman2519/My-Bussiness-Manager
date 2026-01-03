from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.api.auth import get_current_active_user
import json

router = APIRouter(prefix="/settings", tags=["settings"])

# Endpoints for template upload/analysis removed as they are obsolete.
# Use standard business settings in /business-setup/ endpoints.

@router.get("/template")
async def get_invoice_template(
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns the saved template HTML if it exists.
    If staff calls this, they get their Owner's template.
    """
    target_user = current_user
    if current_user.role == "staff" and current_user.owner_id:
        # Fetch Owner
        if current_user.owner:
            target_user = current_user.owner
    
    return {
        "html": target_user.invoice_template_html,
        "mapping": target_user.invoice_mapping
    }
