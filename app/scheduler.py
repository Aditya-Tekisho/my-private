"""Message scheduler module."""
import asyncio
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Message, get_session
from app.whatsapp import whatsapp_client
from app.config import MESSAGE_STATUS_PENDING, MESSAGE_STATUS_SENT, MESSAGE_STATUS_FAILED


class MessageScheduler:
    """Scheduler for pending messages."""
    
    def __init__(self):
        self._running = False
        self._task = None
    
    async def start(self):
        """Start the scheduler."""
        self._running = True
        self._task = asyncio.create_task(self._run())
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _run(self):
        """Run the scheduler loop."""
        while self._running:
            try:
                await self._check_pending_messages()
            except Exception as e:
                print(f"Scheduler error: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_pending_messages(self):
        """Check and send pending messages."""
        async for session in get_session():
            # Get pending messages that are due
            now = datetime.now(timezone.utc)
            stmt = select(Message).where(
                Message.status == MESSAGE_STATUS_PENDING,
                Message.scheduled_at <= now
            )
            result = await session.execute(stmt)
            messages = result.scalars().all()
            
            for message in messages:
                success = False
                
                # Try to send the message
                try:
                    if whatsapp_client.driver:
                        success = await whatsapp_client.send_message(
                            message.contact_phone,
                            message.content
                        )
                except Exception as e:
                    message.error_message = str(e)
                
                # Update message status
                if success:
                    message.status = MESSAGE_STATUS_SENT
                    message.sent_at = datetime.now(timezone.utc)
                else:
                    message.status = MESSAGE_STATUS_FAILED
                    message.error_message = message.error_message or "Failed to send"
                
                await session.commit()


# Global scheduler instance
scheduler = MessageScheduler()


async def start_scheduler():
    """Start the message scheduler."""
    await scheduler.start()


async def stop_scheduler():
    """Stop the message scheduler."""
    await scheduler.stop()