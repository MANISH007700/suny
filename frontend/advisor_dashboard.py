"""
Enhanced Advisor Dashboard
Comprehensive interface for advisors to manage escalations and communicate with students
"""

import streamlit as st
import requests
import time
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AdvisorDashboard:
    """Enhanced advisor dashboard with real-time communication"""
    
    def __init__(self, api_base: str = "http://localhost:8888"):
        self.api_base = api_base
    
    def render(self):
        """Render the complete advisor dashboard"""
        st.markdown("# 🎓 Advisor Dashboard")
        st.markdown("Manage student escalations and provide personalized guidance")
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview",
            "📬 Escalations",
            "👥 Students",
            "🤖 AI Tools"
        ])
        
        with tab1:
            self._render_overview()
        
        with tab2:
            self._render_escalations()
        
        with tab3:
            self._render_students()
        
        with tab4:
            self._render_ai_tools()
    
    def _render_overview(self):
        """Render dashboard overview with statistics"""
        st.markdown("## 📊 Dashboard Overview")
        
        try:
            # Get dashboard stats
            response = requests.get(f"{self.api_base}/advisor/dashboard/stats", timeout=10)
            
            if response.status_code != 200:
                st.error("Failed to load dashboard stats")
                return
            
            stats = response.json()
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Escalations",
                    stats.get("total_escalations", 0),
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Pending",
                    stats.get("pending", 0),
                    delta=None,
                    delta_color="inverse"
                )
            
            with col3:
                st.metric(
                    "In Progress",
                    stats.get("in_progress", 0),
                    delta=None
                )
            
            with col4:
                st.metric(
                    "High Risk Students",
                    stats.get("high_risk_students", 0),
                    delta=None,
                    delta_color="inverse"
                )
            
            st.markdown("---")
            
            # Repeat students
            st.markdown("### 🔄 Students with Multiple Escalations")
            
            repeat_students = stats.get("repeat_students", [])
            
            if repeat_students:
                for student in repeat_students[:5]:
                    risk_color = {
                        "low": "#10b981",
                        "medium": "#f59e0b",
                        "high": "#ef4444",
                        "critical": "#dc2626"
                    }.get(student.get("risk_level", "low"), "#6b7280")
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                                padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;
                                border-left: 4px solid {risk_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: #f1f5f9; font-size: 1.1rem;">{student.get("name", "Unknown")}</strong>
                                <span style="color: #94a3b8; margin-left: 1rem;">ID: {student.get("student_id", "N/A")}</span>
                            </div>
                            <div>
                                <span style="background: {risk_color}; color: white; padding: 0.25rem 0.75rem; 
                                             border-radius: 12px; font-size: 0.85rem; font-weight: 600;">
                                    {student.get("escalation_count", 0)} escalations
                                </span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No repeat escalations yet")
        
        except Exception as e:
            logger.error(f"Error rendering overview: {e}")
            st.error(f"Error loading overview: {str(e)}")
    
    def _render_escalations(self):
        """Render escalations list and detail view"""
        st.markdown("## 📬 Escalations")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "pending", "in_progress", "resolved", "closed"],
                key="status_filter"
            )
        
        with col2:
            priority_filter = st.slider(
                "Min Priority",
                1, 5, 1,
                key="priority_filter"
            )
        
        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        try:
            # Get escalations
            params = {}
            if status_filter != "All":
                params["status"] = status_filter
            if priority_filter > 1:
                params["priority_min"] = priority_filter
            
            response = requests.get(
                f"{self.api_base}/advisor/escalations",
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                st.error("Failed to load escalations")
                return
            
            escalations = response.json()
            
            if not escalations:
                st.info("No escalations found")
                return
            
            # Display escalations
            for esc in escalations:
                self._render_escalation_card(esc)
        
        except Exception as e:
            logger.error(f"Error rendering escalations: {e}")
            st.error(f"Error loading escalations: {str(e)}")
    
    def _render_escalation_card(self, escalation: Dict):
        """Render a single escalation card"""
        esc_id = escalation.get("id", "unknown")
        student_id = escalation.get("student_id", "unknown")
        status = escalation.get("status", "pending")
        priority = escalation.get("priority", 1)
        question = escalation.get("question", "No question")
        
        # Status colors
        status_colors = {
            "pending": "#f59e0b",
            "in_progress": "#3b82f6",
            "resolved": "#10b981",
            "closed": "#6b7280"
        }
        
        status_color = status_colors.get(status, "#6b7280")
        
        with st.expander(f"{'⭐' * priority} {status.upper()} - {question[:60]}..."):
            # Escalation details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Student ID:** {student_id}")
                st.markdown(f"**Status:** {status.title()}")
                st.markdown(f"**Priority:** {'⭐' * priority}")
                st.markdown(f"**Created:** {escalation.get('created_at', 'Unknown')}")
                
                if escalation.get("assigned_to"):
                    st.markdown(f"**Assigned to:** {escalation['assigned_to']}")
            
            with col2:
                # Quick actions
                st.markdown("**Quick Actions:**")
                
                if st.button("📧 Email Student", key=f"email_{esc_id}", use_container_width=True):
                    self._generate_email(esc_id)
                
                if st.button("📅 Schedule Meeting", key=f"meeting_{esc_id}", use_container_width=True):
                    self._generate_meeting(esc_id)
                
                if st.button("📋 Recovery Plan", key=f"recovery_{esc_id}", use_container_width=True):
                    self._generate_recovery_plan(esc_id)
            
            st.markdown("---")
            
            # Question and AI response
            st.markdown("### Student Question")
            st.info(question)
            
            st.markdown("### AI Response")
            st.markdown(escalation.get("ai_response", "No AI response"))
            
            st.markdown("### Escalation Reason")
            st.warning(escalation.get("escalation_reason", "No reason provided"))
            
            # Conversation history
            if escalation.get("conversation_history"):
                with st.expander("💬 Conversation History"):
                    for msg in escalation["conversation_history"]:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        
                        if role == "user":
                            st.markdown(f"**Student:** {content}")
                        else:
                            st.markdown(f"**AI:** {content}")
                        st.markdown("---")
            
            # Advisor notes
            st.markdown("### 📝 Advisor Notes")
            notes = escalation.get("advisor_notes", [])
            
            if notes:
                for note in notes:
                    st.markdown(f"**{note.get('timestamp', 'Unknown')}**")
                    st.markdown(note.get("note", ""))
                    st.markdown("---")
            
            # Responses (student-advisor communication)
            st.markdown("### 💬 Messages")
            responses = escalation.get("responses", [])
            
            if responses:
                for resp in responses:
                    role = resp.get("role", "unknown")
                    content = resp.get("content", "")
                    timestamp = resp.get("timestamp", "")
                    
                    if role == "advisor":
                        st.success(f"**🎓 Advisor ({resp.get('advisor_name', 'Unknown')})** - {timestamp}\n\n{content}")
                    else:
                        st.info(f"**👤 Student** - {timestamp}\n\n{content}")
            
            # Respond to student
            st.markdown("### 📤 Respond to Student")
            
            with st.form(f"respond_form_{esc_id}"):
                advisor_name = st.text_input("Your Name", value="Academic Advisor", key=f"advisor_name_{esc_id}")
                message = st.text_area(
                    "Your Response",
                    placeholder="Type your message to the student...",
                    height=150,
                    key=f"message_{esc_id}"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    submit = st.form_submit_button("📤 Send to Student", type="primary", use_container_width=True)
                
                with col2:
                    # Update status
                    new_status = st.selectbox(
                        "Update Status",
                        ["pending", "in_progress", "resolved", "closed"],
                        index=["pending", "in_progress", "resolved", "closed"].index(status),
                        key=f"status_{esc_id}"
                    )
                
                if submit and message:
                    self._send_advisor_response(esc_id, message, advisor_name, new_status)
            
            # Add note
            with st.form(f"note_form_{esc_id}"):
                st.markdown("### 📝 Add Private Note")
                note_text = st.text_area(
                    "Note (only visible to advisors)",
                    placeholder="Add internal notes...",
                    key=f"note_{esc_id}"
                )
                
                if st.form_submit_button("Add Note", use_container_width=True):
                    if note_text:
                        self._add_advisor_note(esc_id, note_text)
    
    def _send_advisor_response(self, escalation_id: str, message: str, advisor_name: str, new_status: str):
        """Send advisor response to student"""
        try:
            # Send message
            response = requests.post(
                f"{self.api_base}/ai-actions/escalations/{escalation_id}/advisor-respond",
                json={
                    "message": message,
                    "advisor_name": advisor_name
                },
                timeout=10
            )
            
            if response.status_code == 200:
                # Update status
                update_response = requests.patch(
                    f"{self.api_base}/advisor/escalations/{escalation_id}",
                    json={"status": new_status},
                    timeout=10
                )
                
                if update_response.status_code == 200:
                    st.success("✅ Message sent and status updated!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Message sent but status update failed")
            else:
                st.error("Failed to send message")
        
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            st.error(f"Error: {str(e)}")
    
    def _add_advisor_note(self, escalation_id: str, note: str):
        """Add private advisor note"""
        try:
            response = requests.patch(
                f"{self.api_base}/advisor/escalations/{escalation_id}",
                json={"note": note},
                timeout=10
            )
            
            if response.status_code == 200:
                st.success("✅ Note added!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to add note")
        
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            st.error(f"Error: {str(e)}")
    
    def _generate_email(self, escalation_id: str):
        """Generate outreach email"""
        try:
            with st.spinner("Generating email..."):
                response = requests.post(
                    f"{self.api_base}/advisor/escalations/{escalation_id}/generate-email",
                    timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.markdown("### 📧 Generated Email")
                    st.text_area("Email Content", value=data.get("email", ""), height=300)
                else:
                    st.error("Failed to generate email")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def _generate_meeting(self, escalation_id: str):
        """Generate meeting invitation"""
        try:
            with st.spinner("Generating meeting invitation..."):
                response = requests.post(
                    f"{self.api_base}/advisor/escalations/{escalation_id}/generate-meeting",
                    timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.markdown("### 📅 Generated Meeting Invitation")
                    st.text_area("Invitation Content", value=data.get("invitation", ""), height=250)
                else:
                    st.error("Failed to generate invitation")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def _generate_recovery_plan(self, escalation_id: str):
        """Generate academic recovery plan"""
        try:
            with st.spinner("Generating recovery plan..."):
                response = requests.post(
                    f"{self.api_base}/advisor/escalations/{escalation_id}/generate-recovery-plan",
                    timeout=25
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.markdown("### 📋 Generated Recovery Plan")
                    st.markdown(data.get("plan", ""))
                else:
                    st.error("Failed to generate plan")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def _render_students(self):
        """Render students list"""
        st.markdown("## 👥 Students")
        
        try:
            response = requests.get(f"{self.api_base}/advisor/students", timeout=10)
            
            if response.status_code != 200:
                st.error("Failed to load students")
                return
            
            students = response.json()
            
            if not students:
                st.info("No students found")
                return
            
            # Display students
            for student in students:
                self._render_student_card(student)
        
        except Exception as e:
            logger.error(f"Error rendering students: {e}")
            st.error(f"Error: {str(e)}")
    
    def _render_student_card(self, student: Dict):
        """Render student profile card"""
        student_id = student.get("student_id", "unknown")
        name = student.get("name", "Unknown")
        risk_level = student.get("risk_level", "low")
        
        risk_colors = {
            "low": "#10b981",
            "medium": "#f59e0b",
            "high": "#ef4444",
            "critical": "#dc2626"
        }
        
        risk_color = risk_colors.get(risk_level, "#6b7280")
        
        with st.expander(f"{name} ({student_id}) - Risk: {risk_level.upper()}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Major:** {student.get('major', 'Undeclared')}")
                st.markdown(f"**GPA:** {student.get('gpa', 'N/A')}")
                st.markdown(f"**Risk Level:** {risk_level.title()}")
            
            with col2:
                st.markdown(f"**Total Escalations:** {student.get('total_escalations', 0)}")
                st.markdown(f"**Last Interaction:** {student.get('last_interaction', 'Never')}")
            
            if student.get("current_courses"):
                st.markdown("**Current Courses:**")
                st.markdown(", ".join(student["current_courses"]))
    
    def _render_ai_tools(self):
        """Render AI-powered advisor tools"""
        st.markdown("## 🤖 AI Tools")
        st.markdown("Use AI to assist with advising tasks")
        
        tool_type = st.selectbox(
            "Select Tool",
            [
                "Generate Outreach Email",
                "Create Meeting Invitation",
                "Generate Session Summary",
                "Create Recovery Plan",
                "Generate Guidance Notes"
            ]
        )
        
        st.markdown(f"### {tool_type}")
        st.info("Select an escalation from the Escalations tab to use AI tools")

