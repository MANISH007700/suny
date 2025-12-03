# routers/advisor.py
from fastapi import APIRouter, HTTPException
from utils.schema import (
    Escalation, 
    EscalationResponse, 
    UpdateEscalationRequest,
    CreateEscalationRequest,
    StudentProfile,
    EscalationStatus,
    RiskLevel
)
from typing import List, Optional
import json
import os
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Storage paths
ESCALATIONS_FILE = "./backend/data/escalations.json"
STUDENTS_FILE = "./backend/data/student_profiles.json"
os.makedirs("./backend/data", exist_ok=True)

# === Storage Functions ===

def load_escalations() -> List[dict]:
    """Load escalations from JSON file"""
    if os.path.exists(ESCALATIONS_FILE):
        try:
            with open(ESCALATIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_escalations(escalations: List[dict]):
    """Save escalations to JSON file"""
    with open(ESCALATIONS_FILE, 'w') as f:
        json.dump(escalations, f, indent=2)

def load_student_profiles() -> dict:
    """Load student profiles from JSON file"""
    if os.path.exists(STUDENTS_FILE):
        try:
            with open(STUDENTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_student_profiles(profiles: dict):
    """Save student profiles to JSON file"""
    with open(STUDENTS_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)

def get_or_create_student_profile(student_id: str) -> dict:
    """Get existing student profile or create new one"""
    profiles = load_student_profiles()
    
    if student_id not in profiles:
        # Create default profile
        profiles[student_id] = {
            "student_id": student_id,
            "name": f"Student {student_id}",
            "major": "-",
            "gpa": None,
            "completed_courses": [],
            "current_courses": [],
            "risk_level": "low",
            "total_escalations": 0,
            "last_interaction": datetime.now().isoformat()
        }
        save_student_profiles(profiles)
    
    return profiles[student_id]

def update_student_profile(student_id: str, updates: dict):
    """Update student profile"""
    profiles = load_student_profiles()
    if student_id in profiles:
        profiles[student_id].update(updates)
        profiles[student_id]["last_interaction"] = datetime.now().isoformat()
        save_student_profiles(profiles)

# === API Endpoints ===

@router.get("/health")
async def health():
    """Health check for advisor endpoints"""
    return {
        "status": "healthy",
        "escalations_count": len(load_escalations()),
        "students_count": len(load_student_profiles())
    }

@router.get("/escalations", response_model=List[Escalation])
async def get_all_escalations(
    status: Optional[str] = None,
    student_id: Optional[str] = None,
    priority_min: Optional[int] = None
):
    """Get all escalations with optional filters"""
    try:
        escalations = load_escalations()
        
        # Apply filters
        if status:
            escalations = [e for e in escalations if e.get("status") == status]
        if student_id:
            escalations = [e for e in escalations if e.get("student_id") == student_id]
        if priority_min:
            escalations = [e for e in escalations if e.get("priority", 1) >= priority_min]
        
        # Sort by priority (descending) and created_at (newest first)
        escalations.sort(key=lambda x: (-x.get("priority", 1), x.get("created_at", "")), reverse=True)
        
        logger.info(f"Retrieved {len(escalations)} escalations")
        return escalations
        
    except Exception as e:
        logger.error(f"Error retrieving escalations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/escalations/{escalation_id}", response_model=EscalationResponse)
async def get_escalation_details(escalation_id: str):
    """Get detailed escalation with student profile"""
    try:
        escalations = load_escalations()
        escalation = next((e for e in escalations if e["id"] == escalation_id), None)
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Get student profile
        student_profile = get_or_create_student_profile(escalation["student_id"])
        
        return {
            "escalation": escalation,
            "student_profile": student_profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving escalation details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/escalations", response_model=Escalation)
async def create_escalation(request: CreateEscalationRequest):
    """Create a new escalation"""
    try:
        escalation_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        escalation = {
            "id": escalation_id,
            "student_id": request.student_id,
            "question": request.question,
            "ai_response": request.ai_response,
            "conversation_history": [msg.dict() for msg in request.conversation_history],
            "status": "pending",
            "escalation_reason": request.escalation_reason,
            "created_at": now,
            "updated_at": now,
            "advisor_notes": [],
            "assigned_to": None,
            "priority": request.priority
        }
        
        # Save escalation
        escalations = load_escalations()
        escalations.append(escalation)
        save_escalations(escalations)
        
        # Update student profile
        profile = get_or_create_student_profile(request.student_id)
        profile["total_escalations"] = profile.get("total_escalations", 0) + 1
        
        # Calculate risk level based on escalation patterns
        if profile["total_escalations"] >= 5:
            profile["risk_level"] = "high"
        elif profile["total_escalations"] >= 3:
            profile["risk_level"] = "medium"
        
        update_student_profile(request.student_id, profile)
        
        logger.info(f"Created escalation {escalation_id} for student {request.student_id}")
        return escalation
        
    except Exception as e:
        logger.error(f"Error creating escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/escalations/{escalation_id}", response_model=Escalation)
async def update_escalation(escalation_id: str, request: UpdateEscalationRequest):
    """Update an escalation (status, notes, assignment, priority)"""
    try:
        escalations = load_escalations()
        escalation_idx = next(
            (i for i, e in enumerate(escalations) if e["id"] == escalation_id),
            None
        )
        
        if escalation_idx is None:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        escalation = escalations[escalation_idx]
        
        # Update fields
        if request.status:
            escalation["status"] = request.status
        if request.note:
            escalation["advisor_notes"].append({
                "note": request.note,
                "timestamp": datetime.now().isoformat()
            })
        if request.assigned_to is not None:
            escalation["assigned_to"] = request.assigned_to
        if request.priority is not None:
            escalation["priority"] = request.priority
        
        escalation["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        escalations[escalation_idx] = escalation
        save_escalations(escalations)
        
        logger.info(f"Updated escalation {escalation_id}")
        return escalation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/students", response_model=List[StudentProfile])
async def get_all_students():
    """Get all student profiles"""
    try:
        profiles = load_student_profiles()
        return list(profiles.values())
    except Exception as e:
        logger.error(f"Error retrieving students: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/students/{student_id}", response_model=StudentProfile)
async def get_student_profile(student_id: str):
    """Get specific student profile"""
    try:
        profile = get_or_create_student_profile(student_id)
        return profile
    except Exception as e:
        logger.error(f"Error retrieving student profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/students/{student_id}", response_model=StudentProfile)
async def update_student(student_id: str, updates: dict):
    """Update student profile information"""
    try:
        profile = get_or_create_student_profile(student_id)
        profile.update(updates)
        update_student_profile(student_id, profile)
        
        logger.info(f"Updated student profile {student_id}")
        return profile
    except Exception as e:
        logger.error(f"Error updating student profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get summary statistics for dashboard"""
    try:
        escalations = load_escalations()
        profiles = load_student_profiles()
        
        # Calculate statistics
        pending_count = len([e for e in escalations if e.get("status") == "pending"])
        in_progress_count = len([e for e in escalations if e.get("status") == "in_progress"])
        resolved_count = len([e for e in escalations if e.get("status") == "resolved"])
        
        high_risk_students = len([p for p in profiles.values() if p.get("risk_level") in ["high", "critical"]])
        
        # Get students with multiple escalations
        repeat_students = [
            {
                "student_id": p["student_id"],
                "name": p.get("name", "Unknown"),
                "escalation_count": p.get("total_escalations", 0),
                "risk_level": p.get("risk_level", "low")
            }
            for p in profiles.values()
            if p.get("total_escalations", 0) > 1
        ]
        repeat_students.sort(key=lambda x: x["escalation_count"], reverse=True)
        
        return {
            "total_escalations": len(escalations),
            "pending": pending_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "total_students": len(profiles),
            "high_risk_students": high_risk_students,
            "repeat_students": repeat_students[:10]  # Top 10
        }
        
    except Exception as e:
        logger.error(f"Error calculating dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/escalations/{escalation_id}")
async def delete_escalation(escalation_id: str):
    """Delete an escalation (for testing/cleanup)"""
    try:
        escalations = load_escalations()
        escalations = [e for e in escalations if e["id"] != escalation_id]
        save_escalations(escalations)
        
        logger.info(f"Deleted escalation {escalation_id}")
        return {"status": "success", "message": "Escalation deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== ADVISOR ASSIST TOOLS ==========

@router.post("/escalations/{escalation_id}/generate-email")
async def generate_outreach_email(escalation_id: str):
    """Generate personalized outreach email for student"""
    try:
        escalations = load_escalations()
        escalation = next((e for e in escalations if e["id"] == escalation_id), None)
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Get student profile
        student_profile = get_or_create_student_profile(escalation["student_id"])
        
        # Import LLM client
        from models.llm_client import LLMClient
        llm_client = LLMClient()
        
        # Generate email
        email_content = llm_client.generate_outreach_email(escalation, student_profile)
        
        logger.info(f"Generated outreach email for escalation {escalation_id}")
        return {
            "status": "success",
            "email": email_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating outreach email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/escalations/{escalation_id}/generate-meeting")
async def generate_meeting_invitation(escalation_id: str, details: dict = None):
    """Generate meeting invitation for student"""
    try:
        escalations = load_escalations()
        escalation = next((e for e in escalations if e["id"] == escalation_id), None)
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Get student profile
        student_profile = get_or_create_student_profile(escalation["student_id"])
        
        # Import LLM client
        from models.llm_client import LLMClient
        llm_client = LLMClient()
        
        # Generate meeting invitation
        meeting_content = llm_client.generate_meeting_invitation(escalation, student_profile, details)
        
        logger.info(f"Generated meeting invitation for escalation {escalation_id}")
        return {
            "status": "success",
            "invitation": meeting_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating meeting invitation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/escalations/{escalation_id}/generate-summary")
async def generate_session_summary(escalation_id: str, request: dict = None):
    """Generate advising session summary"""
    try:
        escalations = load_escalations()
        escalation = next((e for e in escalations if e["id"] == escalation_id), None)
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Get student profile
        student_profile = get_or_create_student_profile(escalation["student_id"])
        
        # Import LLM client
        from models.llm_client import LLMClient
        llm_client = LLMClient()
        
        # Get session notes if provided
        session_notes = request.get("notes", "") if request else ""
        
        # Generate summary
        summary_content = llm_client.generate_session_summary(escalation, student_profile, session_notes)
        
        logger.info(f"Generated session summary for escalation {escalation_id}")
        return {
            "status": "success",
            "summary": summary_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating session summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/escalations/{escalation_id}/generate-recovery-plan")
async def generate_recovery_plan(escalation_id: str):
    """Generate academic recovery plan for student"""
    try:
        escalations = load_escalations()
        escalation = next((e for e in escalations if e["id"] == escalation_id), None)
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Get student profile
        student_profile = get_or_create_student_profile(escalation["student_id"])
        
        # Import LLM client
        from models.llm_client import LLMClient
        llm_client = LLMClient()
        
        # Generate recovery plan
        plan_content = llm_client.generate_recovery_plan(escalation, student_profile)
        
        logger.info(f"Generated recovery plan for escalation {escalation_id}")
        return {
            "status": "success",
            "plan": plan_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recovery plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/escalations/{escalation_id}/generate-guidance")
async def generate_guidance_notes(escalation_id: str, request: dict = None):
    """Generate personalized guidance notes based on policies"""
    try:
        escalations = load_escalations()
        escalation = next((e for e in escalations if e["id"] == escalation_id), None)
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Get student profile
        student_profile = get_or_create_student_profile(escalation["student_id"])
        
        # Import LLM client
        from models.llm_client import LLMClient
        llm_client = LLMClient()
        
        # Get policy context if provided
        policy_context = request.get("policy_context", "") if request else ""
        
        # Generate guidance notes
        guidance_content = llm_client.generate_guidance_notes(escalation, student_profile, policy_context)
        
        logger.info(f"Generated guidance notes for escalation {escalation_id}")
        return {
            "status": "success",
            "guidance": guidance_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating guidance notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

