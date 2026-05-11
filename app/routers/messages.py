"""Messages router."""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, field_validator
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.whatsapp import whatsapp_client
from app.database import app_state, Message, get_session
from app.config import MESSAGE_STATUS_PENDING, MESSAGE_STATUS_SENT, MESSAGE_STATUS_FAILED


router = APIRouter(prefix="/api/messages", tags=["Messages"])


class SendMessageRequest(BaseModel):
    """Send message request."""
    phone: str
    message: str
    contact_name: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not v or not v.strip():
            raise ValueError('Phone number is required')
        # Remove spaces and validate format
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content is required')
        if len(v) > 65536:
            raise ValueError('Message too long (max 65536 characters)')
        return v


class ScheduleMessageRequest(BaseModel):
    """Schedule message request."""
    phone: str
    message: str
    scheduled_at: datetime
    contact_name: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not v or not v.strip():
            raise ValueError('Phone number is required')
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content is required')
        if len(v) > 65536:
            raise ValueError('Message too long (max 65536 characters)')
        return v
    
    @field_validator('scheduled_at')
    @classmethod
    def validate_scheduled_at(cls, v):
        if v <= datetime.now(timezone.utc):
            raise ValueError('Scheduled time must be in the future')
        return v


class MessageResponse(BaseModel):
    """Message response."""
    id: int
    contact_phone: str
    contact_name: str
    content: str
    status: str
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


class SendResponse(BaseModel):
    """Send response."""
    success: bool
    message: str


@router.post("/send", response_model=SendResponse)
async def send_message(request: SendMessageRequest):
    """Send a message instantly."""
    if not app_state.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        success = await whatsapp_client.send_message(request.phone, request.message)
        
        if success:
            # Save to database
            async for session in get_session():
                msg = Message(
                    contact_phone=request.phone,
                    contact_name=request.contact_name or request.phone,
                    content=request.message,
                    status=MESSAGE_STATUS_SENT,
                    sent_at=datetime.now(timezone.utc)
                )
                session.add(msg)
                await session.commit()
            
            return {"success": True, "message": "Message sent successfully"}
        else:
            return {"success": False, "message": "Failed to send message"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule", response_model=SendResponse)
async def schedule_message(request: ScheduleMessageRequest):
    """Schedule a message for later."""
    if not app_state.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate scheduled time
    if request.scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future")
    
    # Save to database
    async for session in get_session():
        msg = Message(
            contact_phone=request.phone,
            contact_name=request.contact_name or request.phone,
            content=request.message,
            status=MESSAGE_STATUS_PENDING,
            scheduled_at=request.scheduled_at
        )
        session.add(msg)
        await session.commit()
    
    return {"success": True, "message": f"Message scheduled for {request.scheduled_at}"}


@router.get("/history", response_model=List[MessageResponse])
async def get_message_history(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100)
):
    """Get message history."""
    async for session in get_session():
        stmt = select(Message).order_by(Message.created_at.desc()).limit(limit)
        
        if status:
            stmt = stmt.where(Message.status == status)
        
        result = await session.execute(stmt)
        messages = result.scalars().all()
        
        return [
            MessageResponse(
                id=m.id,
                contact_phone=m.contact_phone,
                contact_name=m.contact_name,
                content=m.content,
                status=m.status,
                scheduled_at=m.scheduled_at,
                sent_at=m.sent_at,
                error_message=m.error_message,
                created_at=m.created_at
            )
            for m in messages
        ]


@router.delete("/{message_id}")
async def delete_message(message_id: int):
    """Delete a message from history."""
    async for session in get_session():
        stmt = delete(Message).where(Message.id == message_id)
        result = await session.execute(stmt)
        await session.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Message not found")
    
    return {"success": True, "message": "Message deleted"}


@router.get("/stats")
async def get_message_stats():
    """Get message statistics."""
    async for session in get_session():
        # Count by status
        total = await session.execute(select(Message))
        total_count = len(total.scalars().all())
        
        pending = await session.execute(
            select(Message).where(Message.status == MESSAGE_STATUS_PENDING)
        )
        pending_count = len(pending.scalars().all())
        
        sent = await session.execute(
            select(Message).where(Message.status == MESSAGE_STATUS_SENT)
        )
        sent_count = len(sent.scalars().all())
        
        failed = await session.execute(
            select(Message).where(Message.status == MESSAGE_STATUS_FAILED)
        )
        failed_count = len(failed.scalars().all())
        
        return {
            "total": total_count,
            "pending": pending_count,
            "sent": sent_count,
            "failed": failed_count
        }