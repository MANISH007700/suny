"""
AI Action Components for Frontend
Handles intelligent actions triggered by AI responses
"""

import streamlit as st
import requests
import json
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AIActionHandler:
    """Handle AI-triggered actions in the frontend"""
    
    def __init__(self, api_base: str = "http://localhost:8888"):
        self.api_base = api_base
    
    def detect_and_show_actions(
        self,
        student_id: str,
        student_message: str,
        ai_response: str,
        context: Optional[Dict] = None,
        conversation_history: List[Dict] = []
    ) -> Dict[str, Any]:
        """
        Detect intent and show appropriate action buttons
        
        Returns:
            Intent result with detected actions
        """
        try:
            # Call intent detection API
            response = requests.post(
                f"{self.api_base}/ai-actions/detect-intent",
                json={
                    "student_id": student_id,
                    "student_message": student_message,
                    "ai_response": ai_response,
                    "context": context,
                    "conversation_history": conversation_history
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Intent detection failed: {response.status_code}")
                return {"intent": "NO_ACTION", "suggested_actions": []}
        
        except Exception as e:
            logger.error(f"Error detecting intent: {e}")
            return {"intent": "NO_ACTION", "suggested_actions": []}
    
    def render_action_buttons(self, intent_result: Dict[str, Any]) -> None:
        """Render action buttons based on detected intent"""
        actions = intent_result.get("suggested_actions", [])
        
        if not actions:
            return
        
        st.markdown("---")
        st.markdown("### 🎯 Suggested Actions")
        
        # Auto-escalation notice
        if intent_result.get("escalation_created"):
            st.success(f"✅ Auto-escalated to advisor (ID: {intent_result['escalation_created'][:8]}...)")
        
        # Render action buttons
        cols = st.columns(len(actions))
        
        for i, action in enumerate(actions):
            with cols[i]:
                self._render_single_action(action, intent_result)
    
    def _render_single_action(self, action: Dict, intent_result: Dict) -> None:
        """Render a single action button"""
        action_type = action.get("type")
        label = action.get("label", "Action")
        
        if action_type == "download_file":
            if st.button(f"📥 {label}", key=f"download_{action.get('format')}", use_container_width=True):
                self._handle_download(action, intent_result)
        
        elif action_type == "show_comparison":
            if st.button(f"⚖️ {label}", key="compare_courses_btn", use_container_width=True):
                self._handle_course_comparison(action, intent_result)
        
        elif action_type == "create_escalation":
            if not action.get("auto", False):  # Only show button for manual escalation
                if st.button(f"🆘 {label}", key="manual_escalate_btn", use_container_width=True):
                    st.session_state.show_escalation_form = True
                    st.rerun()
    
    def _handle_download(self, action: Dict, intent_result: Dict) -> None:
        """Handle file download action"""
        try:
            file_format = action.get("format", "csv")
            data = intent_result.get("data", {}).get("content", [])
            
            # Prepare download request
            download_data = {
                "file_type": file_format,
                "data": data,
                "data_type": "courses" if isinstance(data, list) and data and "metadata" in data[0] else "generic"
            }
            
            # Call download API
            response = requests.post(
                f"{self.api_base}/ai-actions/download",
                json=download_data,
                timeout=30
            )
            
            if response.status_code == 200:
                # Create download button
                st.download_button(
                    label=f"💾 Download {file_format.upper()}",
                    data=response.content,
                    file_name=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_format}",
                    mime=response.headers.get("content-type", "application/octet-stream"),
                    use_container_width=True
                )
            else:
                st.error(f"Download failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error handling download: {e}")
            st.error(f"Download error: {str(e)}")
    
    def _handle_course_comparison(self, action: Dict, intent_result: Dict) -> None:
        """Handle course comparison action"""
        try:
            courses = action.get("courses", [])
            
            if not courses or len(courses) < 2:
                st.warning("Need at least 2 courses to compare")
                return
            
            # Store in session state to show comparison
            st.session_state.show_comparison = True
            st.session_state.comparison_courses = courses
            st.rerun()
        
        except Exception as e:
            logger.error(f"Error handling comparison: {e}")
            st.error(f"Comparison error: {str(e)}")
    
    def render_course_comparison(self, courses: List[Dict], api_base: str) -> None:
        """Render course comparison view"""
        try:
            st.markdown("## ⚖️ Course Comparison")
            
            # Call comparison API
            response = requests.post(
                f"{api_base}/ai-actions/compare-courses",
                json={"courses": courses},
                timeout=30
            )
            
            if response.status_code != 200:
                st.error("Failed to generate comparison")
                return
            
            result = response.json()
            
            # Display comparison table
            st.markdown("### 📊 Side-by-Side Comparison")
            self._render_comparison_table(result.get("comparison_table", {}))
            
            # Display AI insights
            st.markdown("### 🤖 AI Insights")
            st.markdown(result.get("insights", "No insights available"))
            
            # Display recommendation
            st.markdown("### 💡 Recommendation")
            st.info(result.get("recommendation", "No recommendation available"))
            
            # Download options
            st.markdown("### 📥 Export Comparison")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Download as CSV", use_container_width=True):
                    self._download_comparison(courses, "csv", api_base)
            
            with col2:
                if st.button("Download as JSON", use_container_width=True):
                    self._download_comparison(courses, "json", api_base)
            
            # Close button
            if st.button("❌ Close Comparison", type="secondary", use_container_width=True):
                st.session_state.show_comparison = False
                st.session_state.comparison_courses = []
                st.rerun()
        
        except Exception as e:
            logger.error(f"Error rendering comparison: {e}")
            st.error(f"Comparison error: {str(e)}")
    
    def _render_comparison_table(self, table: Dict) -> None:
        """Render comparison table"""
        if not table or not table.get("rows"):
            st.warning("No comparison data available")
            return
        
        # Build HTML table
        html = '<table style="width:100%; border-collapse: collapse; font-size: 0.9rem;">\n'
        html += '  <thead>\n'
        html += '    <tr style="background-color: #1e293b;">\n'
        
        for header in table.get("headers", []):
            html += f'      <th style="border: 1px solid #475569; padding: 12px; text-align: left; color: #f1f5f9;">{header}</th>\n'
        
        html += '    </tr>\n'
        html += '  </thead>\n'
        html += '  <tbody>\n'
        
        for row in table.get("rows", []):
            html += '    <tr style="border-bottom: 1px solid #334155;">\n'
            html += f'      <td style="border: 1px solid #475569; padding: 10px; font-weight: 600; background-color: #1e293b; color: #cbd5e1;">{row.get("field", "")}</td>\n'
            
            for value in row.get("values", []):
                # Handle URLs specially
                if "http" in str(value):
                    value = f'<a href="{value}" target="_blank" style="color: #60a5fa;">Course Link</a>'
                
                html += f'      <td style="border: 1px solid #475569; padding: 10px; color: #e2e8f0;">{value}</td>\n'
            
            html += '    </tr>\n'
        
        html += '  </tbody>\n'
        html += '</table>'
        
        st.markdown(html, unsafe_allow_html=True)
    
    def _download_comparison(self, courses: List[Dict], format: str, api_base: str) -> None:
        """Download comparison in specified format"""
        try:
            response = requests.post(
                f"{api_base}/ai-actions/download",
                json={
                    "file_type": format,
                    "data": courses,
                    "data_type": "courses"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                st.download_button(
                    label=f"💾 Save {format.upper()}",
                    data=response.content,
                    file_name=f"course_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
                    mime=response.headers.get("content-type", "application/octet-stream"),
                    key=f"download_comparison_{format}"
                )
            else:
                st.error("Download failed")
        
        except Exception as e:
            logger.error(f"Error downloading comparison: {e}")
            st.error(f"Download error: {str(e)}")


def show_escalation_status(student_id: str, api_base: str) -> None:
    """Show student's escalation status and messages"""
    try:
        # Get student's escalations
        response = requests.get(
            f"{api_base}/ai-actions/escalations/student/{student_id}",
            timeout=10
        )
        
        if response.status_code != 200:
            return
        
        data = response.json()
        escalations = data.get("escalations", [])
        
        if not escalations:
            return
        
        st.markdown("---")
        st.markdown("### 📬 Your Escalations")
        
        # Show escalation cards
        for esc in escalations[:3]:  # Show last 3
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "resolved": "✅",
                "closed": "📁"
            }.get(esc.get("status", "pending"), "❓")
            
            with st.expander(f"{status_emoji} {esc.get('status', '').title()} - {esc.get('question', '')[:50]}..."):
                st.markdown(f"**Status:** {esc.get('status', 'unknown').title()}")
                st.markdown(f"**Created:** {esc.get('created_at', 'unknown')}")
                st.markdown(f"**Priority:** {'⭐' * esc.get('priority', 1)}")
                
                if esc.get("assigned_to"):
                    st.markdown(f"**Assigned to:** {esc['assigned_to']}")
                
                # Show advisor responses
                responses = esc.get("responses", [])
                if responses:
                    st.markdown("**Messages:**")
                    for resp in responses:
                        role = resp.get("role", "unknown")
                        content = resp.get("content", "")
                        timestamp = resp.get("timestamp", "")
                        
                        if role == "advisor":
                            st.success(f"🎓 Advisor: {content}")
                        else:
                            st.info(f"You: {content}")
                
                # Allow student to respond
                with st.form(f"respond_form_{esc['id']}"):
                    response_text = st.text_area(
                        "Respond to advisor:",
                        key=f"response_{esc['id']}",
                        placeholder="Type your response..."
                    )
                    
                    if st.form_submit_button("Send Response"):
                        if response_text:
                            # Send response
                            try:
                                resp = requests.post(
                                    f"{api_base}/ai-actions/escalations/{esc['id']}/respond",
                                    json={
                                        "message": response_text,
                                        "student_id": student_id
                                    },
                                    timeout=10
                                )
                                
                                if resp.status_code == 200:
                                    st.success("✅ Response sent!")
                                    st.rerun()
                                else:
                                    st.error("Failed to send response")
                            
                            except Exception as e:
                                st.error(f"Error: {e}")
    
    except Exception as e:
        logger.error(f"Error showing escalation status: {e}")


def show_advisor_response_ui(escalation_id: str, api_base: str) -> None:
    """UI for advisor to respond to student"""
    st.markdown("### 💬 Respond to Student")
    
    with st.form("advisor_response_form"):
        advisor_name = st.text_input("Your Name", value="Academic Advisor")
        message = st.text_area(
            "Your Response",
            placeholder="Type your message to the student...",
            height=150
        )
        
        submit = st.form_submit_button("📤 Send to Student", type="primary")
        
        if submit and message:
            try:
                response = requests.post(
                    f"{api_base}/ai-actions/escalations/{escalation_id}/advisor-respond",
                    json={
                        "message": message,
                        "advisor_name": advisor_name
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("✅ Message sent to student!")
                    st.rerun()
                else:
                    st.error("Failed to send message")
            
            except Exception as e:
                st.error(f"Error: {e}")

