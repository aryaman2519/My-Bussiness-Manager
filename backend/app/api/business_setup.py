"""
Business Setup API Endpoints

Handles business configuration for the invoice template system.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import base64
import json
import os

from app.models.database import get_db
from app.models.user import User
from app.auth.security import get_current_active_user


# ... existing imports ...

router = APIRouter(prefix="/business-setup", tags=["business-setup"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads/templates"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class BusinessDetailsRequest(BaseModel):
    """Request model for saving business details."""
    business_name: str
    business_address: str
    business_phone: str

class CoordinatesUpdateRequest(BaseModel):
    """Request model for updating template coordinates."""
    coordinates: dict

# Create static images directory
IMAGES_DIR = "static/business_images"
os.makedirs(IMAGES_DIR, exist_ok=True)

@router.post("/upload-logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and save business logo image to disk."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate filename unique to owner
    # logo_{owner_id}.png
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    filename = f"logo_{current_user.id}.{file_ext}"
    file_path = os.path.join(IMAGES_DIR, filename)
    
    # Save file
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Save path to user
    current_user.business_logo = file_path
    db.commit()
    
    # Return preview
    import base64
    logo_base64 = base64.b64encode(content).decode('utf-8')
    logo_data_uri = f"data:{file.content_type};base64,{logo_base64}"
    
    return {
        "logo_preview": logo_data_uri,
        "message": "Logo uploaded successfully"
    }

@router.post("/upload-signature")
async def upload_signature(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and save signature image to disk."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate filename unique to owner
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    filename = f"signature_{current_user.id}.{file_ext}"
    file_path = os.path.join(IMAGES_DIR, filename)
    
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Save path to user
    current_user.signature_image = file_path
    db.commit()
    
    # Return preview
    import base64
    sig_base64 = base64.b64encode(content).decode('utf-8')
    sig_data_uri = f"data:{file.content_type};base64,{sig_base64}"
    
    return {
        "signature_preview": sig_data_uri,
        "message": "Signature uploaded successfully"
    }

@router.post("/save-details")
async def save_business_details(
    details: BusinessDetailsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save business name, address, and phone number."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    
    # Update user with business details
    current_user.business_name = details.business_name
    current_user.business_address = details.business_address
    current_user.business_phone = details.business_phone
    
    db.commit()
    
    return {
        "message": "Business details saved successfully",
        "business_name": details.business_name,
        "business_address": details.business_address,
        "business_phone": details.business_phone
    }

@router.put("/coordinates")
async def update_coordinates(
    request: CoordinatesUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update template field coordinates."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    
    # Save coordinates as JSON string
    current_user.template_coordinates = json.dumps(request.coordinates)
    db.commit()
    
    return {
        "message": "Coordinates updated successfully"
    }

@router.get("/settings")
async def get_business_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current business settings for invoice generation.
    Staff members get their owner's settings.
    """
    # Determine target user (owner or staff's owner)
    target_user = current_user
    if current_user.role == "staff" and current_user.owner:
        target_user = current_user.owner
    
    # Parse coordinates
    coordinates = {}
    if target_user.template_coordinates:
        try:
            coordinates = json.loads(target_user.template_coordinates)
        except:
            coordinates = {}
    
    return {
        "business_name": target_user.business_name,
        "business_address": target_user.business_address,
        "business_phone": target_user.business_phone,
        "logo": target_user.business_logo,
        "signature": target_user.signature_image,
        "template_path": target_user.template_pdf_path,
        "coordinates": coordinates,
        "has_template": bool(target_user.template_pdf_path),
        "setup_complete": all([
            target_user.business_name,
            target_user.template_pdf_path
        ])
    }

