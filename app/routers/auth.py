"""Authentication router."""
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.whatsapp import whatsapp_client, initialize_client
from app.database import app_state


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class QRResponse(BaseModel):
    """QR code response."""
    qr_code: str | None
    is_authenticated: bool


class AuthStatusResponse(BaseModel):
    """Authentication status response."""
    is_authenticated: bool


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status():
    """Get current authentication status."""
    return {"is_authenticated": app_state.is_authenticated}


@router.post("/qr", response_model=QRResponse)
async def get_qr_code():
    """Get QR code for login or check authentication."""
    if app_state.is_authenticated:
        return {"qr_code": None, "is_authenticated": True}
    
    qr_code = await whatsapp_client.get_qr_code()
    return {"qr_code": qr_code, "is_authenticated": False}


@router.post("/check", response_model=AuthStatusResponse)
async def check_auth():
    """Check if authentication is complete."""
    is_authenticated = await whatsapp_client.check_authenticated()
    app_state.is_authenticated = is_authenticated
    
    if is_authenticated:
        await whatsapp_client.save_session()
    
    return {"is_authenticated": is_authenticated}


@router.post("/wait")
async def wait_for_auth(timeout: int = 60):
    """Wait for QR code scan to complete."""
    if app_state.is_authenticated:
        return {"success": True, "message": "Already authenticated"}
    
    success = await whatsapp_client.wait_for_auth(timeout)
    
    if success:
        await whatsapp_client.save_session()
    
    return {"success": success}


@router.post("/logout")
async def logout():
    """Logout and clear session."""
    await whatsapp_client.close_driver()
    app_state.is_authenticated = False
    app_state.qr_code = None
    
    # Clear session file
    import os
    from app.config import WHATSAPP_SESSION_FILE
    if WHATSAPP_SESSION_FILE.exists():
        os.remove(WHATSAPP_SESSION_FILE)
    
    return {"success": True, "message": "Logged out successfully"}


@router.on_event("startup")
async def startup():
    """Initialize on startup."""
    await initialize_client()


@router.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    await whatsapp_client.close_driver()