"""Contacts router."""
from typing import List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.whatsapp import whatsapp_client
from app.database import app_state


router = APIRouter(prefix="/api/contacts", tags=["Contacts"])


class ContactModel(BaseModel):
    """Contact model."""
    phone: str
    name: str
    avatar: str | None = None
    is_online: bool = False


@router.get("", response_model=List[ContactModel])
async def get_contacts():
    """Get all contacts."""
    if not app_state.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Return cached contacts if available
    if app_state.contacts_cache:
        return app_state.contacts_cache
    
    # Refresh contacts
    contacts = await whatsapp_client.refresh_contacts()
    return contacts


@router.get("/search", response_model=List[ContactModel])
async def search_contacts(q: str = Query(..., min_length=1)):
    """Search contacts by name or phone."""
    if not app_state.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if app_state.contacts_cache:
        # Filter cached contacts
        results = [
            c for c in app_state.contacts_cache
            if q.lower() in c.get("name", "").lower() or q in c.get("phone", "")
        ]
        return results
    
    # Refresh and search
    await whatsapp_client.refresh_contacts()
    results = [
        c for c in app_state.contacts_cache
        if q.lower() in c.get("name", "").lower() or q in c.get("phone", "")
    ]
    return results


@router.post("/refresh", response_model=List[ContactModel])
async def refresh_contacts():
    """Force refresh contacts from WhatsApp."""
    if not app_state.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    contacts = await whatsapp_client.refresh_contacts()
    return contacts