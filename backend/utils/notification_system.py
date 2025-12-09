"""
Notification System
Manages notifications for students and advisors
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notifications"""
    ESCALATION_CREATED = "escalation_created"
    ESCALATION_UPDATED = "escalation_updated"
    ADVISOR_RESPONSE = "advisor_response"
    STUDENT_RESPONSE = "student_response"
    STATUS_CHANGE = "status_change"
    SYSTEM_MESSAGE = "system_message"


class NotificationSystem:
    """Manage notifications for users"""
    
    def __init__(self, storage_path: str = "./backend/data/notifications.json"):
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    
    def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        priority: int = 1
    ) -> Dict:
        """
        Create a new notification
        
        Args:
            user_id: User to notify (student_id or advisor_id)
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional data
            priority: Priority level (1-5)
        
        Returns:
            Created notification
        """
        try:
            notifications = self._load_notifications()
            
            notification = {
                "id": self._generate_id(),
                "user_id": user_id,
                "type": notification_type.value,
                "title": title,
                "message": message,
                "data": data or {},
                "priority": priority,
                "read": False,
                "created_at": datetime.now().isoformat(),
                "read_at": None
            }
            
            notifications.append(notification)
            self._save_notifications(notifications)
            
            logger.info(f"Created notification for {user_id}: {title}")
            
            return notification
        
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return {}
    
    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get notifications for a user"""
        try:
            notifications = self._load_notifications()
            
            # Filter by user
            user_notifications = [n for n in notifications if n.get("user_id") == user_id]
            
            # Filter by read status
            if unread_only:
                user_notifications = [n for n in user_notifications if not n.get("read", False)]
            
            # Sort by priority and created_at
            user_notifications.sort(
                key=lambda x: (-x.get("priority", 1), x.get("created_at", "")),
                reverse=True
            )
            
            # Limit results
            if limit:
                user_notifications = user_notifications[:limit]
            
            return user_notifications
        
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            notifications = self._load_notifications()
            
            for i, notif in enumerate(notifications):
                if notif.get("id") == notification_id:
                    notifications[i]["read"] = True
                    notifications[i]["read_at"] = datetime.now().isoformat()
                    self._save_notifications(notifications)
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        try:
            notifications = self._load_notifications()
            count = 0
            
            for i, notif in enumerate(notifications):
                if notif.get("user_id") == user_id and not notif.get("read", False):
                    notifications[i]["read"] = True
                    notifications[i]["read_at"] = datetime.now().isoformat()
                    count += 1
            
            if count > 0:
                self._save_notifications(notifications)
            
            return count
        
        except Exception as e:
            logger.error(f"Error marking all as read: {e}")
            return 0
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification"""
        try:
            notifications = self._load_notifications()
            original_count = len(notifications)
            
            notifications = [n for n in notifications if n.get("id") != notification_id]
            
            if len(notifications) < original_count:
                self._save_notifications(notifications)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
            return False
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        try:
            notifications = self._load_notifications()
            
            count = sum(
                1 for n in notifications
                if n.get("user_id") == user_id and not n.get("read", False)
            )
            
            return count
        
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    def notify_escalation_created(self, escalation: Dict, student_id: str) -> Dict:
        """Create notification when escalation is created"""
        return self.create_notification(
            user_id=student_id,
            notification_type=NotificationType.ESCALATION_CREATED,
            title="Question Escalated to Advisor",
            message=f"Your question has been sent to an advisor for review.",
            data={"escalation_id": escalation.get("id")},
            priority=2
        )
    
    def notify_advisor_response(self, escalation_id: str, student_id: str, advisor_name: str) -> Dict:
        """Notify student when advisor responds"""
        return self.create_notification(
            user_id=student_id,
            notification_type=NotificationType.ADVISOR_RESPONSE,
            title=f"Response from {advisor_name}",
            message=f"Your advisor has responded to your question.",
            data={"escalation_id": escalation_id},
            priority=3
        )
    
    def notify_student_response(self, escalation_id: str, advisor_id: str, student_id: str) -> Dict:
        """Notify advisor when student responds"""
        return self.create_notification(
            user_id=advisor_id,
            notification_type=NotificationType.STUDENT_RESPONSE,
            title=f"Student Response",
            message=f"Student {student_id} has responded to escalation.",
            data={"escalation_id": escalation_id, "student_id": student_id},
            priority=2
        )
    
    def notify_status_change(self, escalation_id: str, student_id: str, new_status: str) -> Dict:
        """Notify student of status change"""
        return self.create_notification(
            user_id=student_id,
            notification_type=NotificationType.STATUS_CHANGE,
            title="Escalation Status Updated",
            message=f"Your escalation status changed to: {new_status.title()}",
            data={"escalation_id": escalation_id, "new_status": new_status},
            priority=2
        )
    
    def _load_notifications(self) -> List[Dict]:
        """Load notifications from storage"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_notifications(self, notifications: List[Dict]):
        """Save notifications to storage"""
        with open(self.storage_path, 'w') as f:
            json.dump(notifications, f, indent=2)
    
    def _generate_id(self) -> str:
        """Generate unique notification ID"""
        import uuid
        return str(uuid.uuid4())

