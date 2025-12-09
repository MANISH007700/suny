"""
Notification Widget for Frontend
Displays real-time notifications to users
"""

import streamlit as st
import requests
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def show_notification_bell(user_id: str, api_base: str) -> None:
    """
    Show notification bell with unread count
    
    Args:
        user_id: User identifier
        api_base: API base URL
    """
    try:
        # Get unread count
        response = requests.get(
            f"{api_base}/notifications/{user_id}/count",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            unread_count = data.get("unread_count", 0)
            
            # Display notification bell
            if unread_count > 0:
                st.markdown(f"""
                <div style="position: fixed; top: 20px; right: 20px; z-index: 9999;">
                    <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                                color: white; padding: 0.5rem 1rem; border-radius: 20px;
                                box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
                                font-weight: 600; font-size: 0.9rem;
                                display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.2rem;">🔔</span>
                        <span>{unread_count} New</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    except Exception as e:
        logger.error(f"Error showing notification bell: {e}")


def show_notifications_panel(user_id: str, api_base: str, user_mode: str = "Student") -> None:
    """
    Show notifications panel in sidebar or expander
    
    Args:
        user_id: User identifier
        api_base: API base URL
        user_mode: User mode (Student, Advisor, Administrator)
    """
    try:
        # Get notifications
        response = requests.get(
            f"{api_base}/notifications/{user_id}",
            params={"limit": 10},
            timeout=10
        )
        
        if response.status_code != 200:
            return
        
        notifications = response.json()
        
        if not notifications:
            st.info("📭 No notifications")
            return
        
        st.markdown("### 🔔 Notifications")
        
        # Separate unread and read
        unread = [n for n in notifications if not n.get("read", False)]
        read = [n for n in notifications if n.get("read", False)]
        
        # Show unread first
        if unread:
            st.markdown("**Unread**")
            for notif in unread:
                render_notification(notif, api_base, user_id)
        
        # Show read in expander
        if read:
            with st.expander(f"📖 Read Notifications ({len(read)})"):
                for notif in read:
                    render_notification(notif, api_base, user_id, show_compact=True)
        
        # Mark all as read button
        if unread:
            if st.button("✅ Mark All as Read", use_container_width=True):
                mark_all_as_read(user_id, api_base)
                st.rerun()
    
    except Exception as e:
        logger.error(f"Error showing notifications panel: {e}")
        st.error(f"Error loading notifications: {str(e)}")


def render_notification(
    notification: Dict,
    api_base: str,
    user_id: str,
    show_compact: bool = False
) -> None:
    """Render a single notification"""
    notif_id = notification.get("id", "")
    notif_type = notification.get("type", "system_message")
    title = notification.get("title", "Notification")
    message = notification.get("message", "")
    priority = notification.get("priority", 1)
    is_read = notification.get("read", False)
    created_at = notification.get("created_at", "")
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        time_str = dt.strftime("%b %d, %I:%M %p")
    except:
        time_str = "Recently"
    
    # Priority colors
    priority_colors = {
        1: "#6b7280",
        2: "#3b82f6",
        3: "#f59e0b",
        4: "#ef4444",
        5: "#dc2626"
    }
    
    priority_color = priority_colors.get(priority, "#6b7280")
    
    # Type icons
    type_icons = {
        "escalation_created": "🎯",
        "escalation_updated": "🔄",
        "advisor_response": "💬",
        "student_response": "👤",
        "status_change": "📊",
        "system_message": "ℹ️"
    }
    
    icon = type_icons.get(notif_type, "📢")
    
    # Render notification card
    if show_compact:
        st.markdown(f"""
        <div style="background: #1e293b; padding: 0.75rem; border-radius: 8px; 
                    margin-bottom: 0.5rem; border-left: 3px solid {priority_color};
                    opacity: 0.7;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="color: #94a3b8; font-size: 0.85rem;">{icon} {title}</div>
                    <div style="color: #64748b; font-size: 0.8rem; margin-top: 0.25rem;">{time_str}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        bg_color = "#1e293b" if is_read else "#334155"
        
        st.markdown(f"""
        <div style="background: {bg_color}; padding: 1rem; border-radius: 8px; 
                    margin-bottom: 0.75rem; border-left: 4px solid {priority_color};
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                <div style="flex: 1;">
                    <div style="color: #f1f5f9; font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem;">
                        {icon} {title}
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.5;">
                        {message}
                    </div>
                </div>
            </div>
            <div style="color: #64748b; font-size: 0.8rem; margin-top: 0.5rem;">
                {time_str}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # View escalation button if applicable
            if "escalation_id" in notification.get("data", {}):
                escalation_id = notification["data"]["escalation_id"]
                if st.button(f"View Details", key=f"view_{notif_id}", use_container_width=True):
                    st.session_state.selected_escalation = escalation_id
                    st.rerun()
        
        with col2:
            # Mark as read button
            if not is_read:
                if st.button("✓", key=f"read_{notif_id}", use_container_width=True):
                    mark_as_read(notif_id, api_base)
                    st.rerun()


def mark_as_read(notification_id: str, api_base: str) -> bool:
    """Mark notification as read"""
    try:
        response = requests.patch(
            f"{api_base}/notifications/{notification_id}/read",
            timeout=5
        )
        
        return response.status_code == 200
    
    except Exception as e:
        logger.error(f"Error marking as read: {e}")
        return False


def mark_all_as_read(user_id: str, api_base: str) -> bool:
    """Mark all notifications as read"""
    try:
        response = requests.patch(
            f"{api_base}/notifications/{user_id}/read-all",
            timeout=5
        )
        
        return response.status_code == 200
    
    except Exception as e:
        logger.error(f"Error marking all as read: {e}")
        return False


def auto_refresh_notifications(user_id: str, api_base: str, refresh_interval: int = 30) -> None:
    """
    Auto-refresh notifications at specified interval
    
    Args:
        user_id: User identifier
        api_base: API base URL
        refresh_interval: Refresh interval in seconds
    """
    import time
    
    # Use session state to track last refresh
    if "last_notification_refresh" not in st.session_state:
        st.session_state.last_notification_refresh = time.time()
    
    current_time = time.time()
    time_since_refresh = current_time - st.session_state.last_notification_refresh
    
    # Auto-refresh if interval has passed
    if time_since_refresh >= refresh_interval:
        st.session_state.last_notification_refresh = current_time
        # Trigger rerun to fetch new notifications
        st.rerun()

