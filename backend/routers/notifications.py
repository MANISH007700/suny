"""
Notifications Router
API endpoints for notification system
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from utils.notification_system import NotificationSystem, NotificationType

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize notification system
notification_system = NotificationSystem()


# === REQUEST/RESPONSE MODELS ===

class Notification(BaseModel):
    """Notification model"""
    id: str
    user_id: str
    type: str
    title: str
    message: str
    data: dict
    priority: int
    read: bool
    created_at: str
    read_at: Optional[str] = None


class CreateNotificationRequest(BaseModel):
    """Request to create notification"""
    user_id: str
    notification_type: str
    title: str
    message: str
    data: Optional[dict] = None
    priority: int = 1


# === ENDPOINTS ===

@router.get("/health")
async def health_check():
    """Health check for notifications service"""
    return {"status": "healthy", "service": "notifications"}


@router.get("/{user_id}", response_model=List[Notification])
async def get_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: Optional[int] = None
):
    """
    Get notifications for a user
    
    Args:
        user_id: User identifier
        unread_only: Only return unread notifications
        limit: Maximum number of notifications to return
    """
    try:
        notifications = notification_system.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit
        )
        
        return notifications
    
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/count")
async def get_unread_count(user_id: str):
    """Get count of unread notifications"""
    try:
        count = notification_system.get_unread_count(user_id)
        
        return {
            "user_id": user_id,
            "unread_count": count
        }
    
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Notification)
async def create_notification(request: CreateNotificationRequest):
    """Create a new notification"""
    try:
        # Convert string to enum
        try:
            notif_type = NotificationType(request.notification_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid notification type: {request.notification_type}")
        
        notification = notification_system.create_notification(
            user_id=request.user_id,
            notification_type=notif_type,
            title=request.title,
            message=request.message,
            data=request.data,
            priority=request.priority
        )
        
        if not notification:
            raise HTTPException(status_code=500, detail="Failed to create notification")
        
        return notification
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark a notification as read"""
    try:
        success = notification_system.mark_as_read(notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "status": "success",
            "message": "Notification marked as read",
            "notification_id": notification_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{user_id}/read-all")
async def mark_all_as_read(user_id: str):
    """Mark all notifications as read for a user"""
    try:
        count = notification_system.mark_all_as_read(user_id)
        
        return {
            "status": "success",
            "message": f"Marked {count} notifications as read",
            "count": count
        }
    
    except Exception as e:
        logger.error(f"Error marking all as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification"""
    try:
        success = notification_system.delete_notification(notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "status": "success",
            "message": "Notification deleted",
            "notification_id": notification_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

