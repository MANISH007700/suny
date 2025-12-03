# 🎯 Advisor Dashboard - User Guide

## Overview

The Advisor Dashboard is a comprehensive escalation management system that allows academic advisors to monitor and respond to student questions that have been automatically escalated by the AI system or manually flagged.

## Features

### 1. **Escalation Queue Dashboard**

The main dashboard displays all escalated student questions with:

- **Real-time Statistics**: View counts of total escalations, pending, in progress, resolved, and high-risk students
- **Filtering Options**: Filter by status, priority level, or student ID
- **Priority-based Sorting**: Escalations are automatically sorted by priority and date

### 2. **Escalation Details**

Each escalation displays:

- ✅ **Student Question**: The original question that triggered escalation
- 🤖 **AI Response**: What the AI assistant responded with
- ⚠️ **Escalation Reason**: Why this was escalated (e.g., sensitive topic, lack of information)
- 💬 **Full Conversation History**: Complete chat history between student and AI
- 👤 **Student Profile Snapshot**: Real-time student information

### 3. **Student Profile Display**

For each escalation, advisors can view:

- Student name and ID
- Current major
- GPA
- Completed courses
- Current enrolled courses
- Risk level (Low, Medium, High, Critical)
- Total number of escalations
- Last interaction date

### 4. **Action Capabilities**

Advisors can:

- ✏️ **Update Status**: Change escalation status (pending → in progress → resolved → closed)
- 📝 **Add Notes**: Leave detailed notes for follow-up or other advisors
- 👥 **Assign**: Assign escalation to specific advisors
- ⭐ **Set Priority**: Adjust priority level (1-5 stars)
- 📊 **Track Progress**: Monitor resolution timeline

### 5. **Repeat Student Tracking**

The dashboard automatically identifies:

- Students with multiple escalations
- High-risk students requiring immediate attention
- Patterns indicating students who need proactive outreach

## Automatic Escalation Triggers

The system automatically escalates questions when:

1. **Sensitive Topics Detected**:
   - Financial aid/scholarships
   - Withdrawal/academic probation
   - Mental health/crisis situations
   - Disability accommodations
   - Appeals/waivers
   - Transfer credits

2. **AI Uncertainty**:
   - Response contains "I don't have that information"
   - Response indicates lack of relevant documents
   - Very brief responses (<20 words)

3. **Low Context Quality**:
   - Insufficient relevant documents retrieved (<2 documents)

## How to Use

### Accessing the Dashboard

1. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```

2. Start the frontend:
   ```bash
   cd frontend
   streamlit run app.py
   ```

3. In the sidebar, toggle to **"👨‍🏫 Advisor"** mode

4. Navigate to the **"🎯 Advisor Dashboard"** tab

### Handling an Escalation

1. **Review the escalation**: Click on an escalation to expand details
2. **Check student profile**: Review the student's academic standing and history
3. **Read conversation history**: Understand the full context of the interaction
4. **Take action**:
   - Update status to "in progress" while working on it
   - Add notes documenting your findings or recommendations
   - Assign to yourself or another advisor if needed
   - Adjust priority if urgent
5. **Mark as resolved**: Once handled, update status to "resolved"

### Sample Workflow

**Example: Financial Aid Question**

1. Student asks: "I need help with financial aid - my scholarship was denied"
2. AI responds but lacks specific information → **Auto-escalated**
3. Advisor sees escalation marked as **Priority 4** (sensitive topic)
4. Advisor reviews student profile → sees student is high-risk
5. Advisor:
   - Updates status to "in progress"
   - Adds note: "Scheduled meeting with Financial Aid Office for Dec 5"
   - Assigns to "Financial Aid Coordinator"
6. After meeting, marks as "resolved" with outcome note

## API Endpoints

The Advisor Dashboard is powered by these backend endpoints:

### Escalations
- `GET /advisor/escalations` - Get all escalations (with optional filters)
- `GET /advisor/escalations/{id}` - Get specific escalation with student profile
- `POST /advisor/escalations` - Create new escalation (manual)
- `PATCH /advisor/escalations/{id}` - Update escalation status/notes
- `DELETE /advisor/escalations/{id}` - Delete escalation

### Students
- `GET /advisor/students` - Get all student profiles
- `GET /advisor/students/{id}` - Get specific student profile
- `PATCH /advisor/students/{id}` - Update student profile

### Dashboard
- `GET /advisor/dashboard/stats` - Get summary statistics

## Data Storage

The system stores data in JSON files:

- **Escalations**: `backend/data/escalations.json`
- **Student Profiles**: `backend/data/student_profiles.json`

For production use, consider migrating to a proper database (PostgreSQL, MongoDB, etc.)

## Risk Level Calculation

Student risk levels are automatically calculated based on:

- **Low**: 0-2 escalations, good academic standing
- **Medium**: 3-4 escalations
- **High**: 5+ escalations
- **Critical**: Multiple high-priority escalations + failing courses

## Best Practices

1. **Regular Monitoring**: Check dashboard at least twice daily for pending escalations
2. **Quick Response**: Respond to high-priority escalations within 24 hours
3. **Detailed Notes**: Document all actions and recommendations
4. **Proactive Outreach**: Contact repeat students before they escalate further
5. **Collaboration**: Use assignment feature to route to appropriate specialists
6. **Follow-up**: Don't mark as resolved until student confirms issue is addressed

## Testing

Sample data has been pre-loaded with:
- 5 sample escalations (various statuses and priorities)
- 5 sample student profiles (different majors and risk levels)

You can test all features immediately upon starting the system.

## Customization

To customize escalation triggers, edit:
- `backend/models/llm_client.py` → `detect_escalation_needed()` method

To adjust risk calculation, edit:
- `backend/routers/advisor.py` → `create_escalation()` function

## Support

For issues or feature requests, please contact the development team.

---

**Built for SUNY Academic Guidance System**  
*Powered by RAG + Gemini 2.5 Flash*

