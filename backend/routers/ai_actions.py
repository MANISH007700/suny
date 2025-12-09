"""
AI Actions Router
Handles intelligent actions triggered by AI responses:
- Intent detection
- Auto-escalation
- File generation
- Course comparison
- Advisor communication
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

from models.intent_detector import IntentDetector, IntentType
from utils.file_generator import FileGenerator
from models.course_comparator import CourseComparator
from utils.notification_system import NotificationSystem
from utils.schema import (
    CreateEscalationRequest,
    ConversationMessage,
    Escalation
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
intent_detector = IntentDetector()
file_generator = FileGenerator()
course_comparator = CourseComparator()
notification_system = NotificationSystem()


# === REQUEST/RESPONSE MODELS ===

class DetectIntentRequest(BaseModel):
    """Request to detect intent from conversation"""
    student_id: str = Field(..., description="Student identifier")
    student_message: str = Field(..., description="Student's message")
    ai_response: str = Field(..., description="AI's response")
    context: Optional[Dict] = Field(default=None, description="Additional context (courses, data, etc.)")
    conversation_history: List[ConversationMessage] = Field(default=[], description="Full conversation history")


class IntentResponse(BaseModel):
    """Response with detected intent and suggested actions"""
    intent: str = Field(..., description="Detected intent type")
    confidence: float = Field(..., description="Confidence score 0-1")
    data: Dict = Field(..., description="Intent-specific data")
    message: str = Field(..., description="Human-readable message")
    suggested_actions: List[Dict] = Field(..., description="List of suggested actions")
    escalation_created: Optional[str] = Field(default=None, description="Escalation ID if auto-created")


class ProcessChatRequest(BaseModel):
    """Request to process a complete chat interaction"""
    student_id: str
    student_message: str
    ai_response: str
    context: Optional[Dict] = None
    conversation_history: List[ConversationMessage] = []


class DownloadRequest(BaseModel):
    """Request to generate downloadable file"""
    file_type: str = Field(..., description="csv, json, or txt")
    data: Any = Field(..., description="Data to export")
    filename: Optional[str] = None
    data_type: Optional[str] = Field(default="generic", description="courses, escalations, or generic")


class CompareCourseRequest(BaseModel):
    """Request to compare courses"""
    courses: List[Dict] = Field(..., description="List of courses to compare")
    comparison_criteria: Optional[List[str]] = None
    student_id: Optional[str] = None


class AdvisorMessageRequest(BaseModel):
    """Request to send message to advisor"""
    escalation_id: str
    message: str
    from_student: bool = True


class AdvisorMessageResponse(BaseModel):
    """Response from advisor"""
    escalation_id: str
    message_id: str
    timestamp: str
    from_student: bool


# === ENDPOINTS ===

@router.post("/detect-intent", response_model=IntentResponse)
async def detect_intent(request: DetectIntentRequest):
    """
    Detect intent from student message and AI response
    Automatically handles escalations if needed
    """
    try:
        logger.info(f"Detecting intent for student {request.student_id}")
        
        # Detect intent
        intent_result = intent_detector.detect_intent(
            student_message=request.student_message,
            ai_response=request.ai_response,
            context=request.context
        )
        
        escalation_id = None
        
        # Handle auto-escalation
        if intent_result["intent"] == IntentType.AUTO_ESCALATION.value:
            try:
                # Create escalation automatically
                from routers.advisor import create_escalation
                
                escalation_request = CreateEscalationRequest(
                    student_id=request.student_id,
                    question=request.student_message,
                    ai_response=request.ai_response,
                    conversation_history=request.conversation_history,
                    escalation_reason=intent_result["data"].get("escalation_reason", "Auto-escalated by AI"),
                    priority=intent_result["data"].get("priority", 3)
                )
                
                escalation = await create_escalation(escalation_request)
                escalation_id = escalation["id"]
                
                # Send notification to student
                notification_system.notify_escalation_created(escalation, request.student_id)
                
                logger.info(f"Auto-created escalation {escalation_id}")
                
            except Exception as e:
                logger.error(f"Error creating auto-escalation: {e}")
        
        return IntentResponse(
            intent=intent_result["intent"],
            confidence=intent_result["confidence"],
            data=intent_result["data"],
            message=intent_result["message"],
            suggested_actions=intent_result["suggested_actions"],
            escalation_created=escalation_id
        )
        
    except Exception as e:
        logger.error(f"Error detecting intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-chat", response_model=IntentResponse)
async def process_chat(request: ProcessChatRequest):
    """
    Complete chat processing pipeline:
    1. Detect intent
    2. Execute appropriate actions
    3. Return results
    
    This is the main endpoint for the student chat interface
    """
    try:
        logger.info(f"Processing chat for student {request.student_id}")
        
        # Detect intent
        detect_request = DetectIntentRequest(
            student_id=request.student_id,
            student_message=request.student_message,
            ai_response=request.ai_response,
            context=request.context,
            conversation_history=request.conversation_history
        )
        
        result = await detect_intent(detect_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_file(request: DownloadRequest):
    """
    Generate and download file in requested format
    Supports CSV, JSON, and TXT
    """
    try:
        logger.info(f"Generating {request.file_type} file")
        
        file_type = request.file_type.lower()
        
        if file_type == "csv":
            # Handle different data types
            if request.data_type == "courses":
                file_data = file_generator.generate_course_csv(request.data)
            elif request.data_type == "escalations":
                file_data = file_generator.generate_escalation_csv(request.data)
            else:
                # Generic CSV
                if not isinstance(request.data, list):
                    raise HTTPException(status_code=400, detail="CSV export requires list of dictionaries")
                file_data = file_generator.generate_csv(request.data, request.filename)
        
        elif file_type == "json":
            file_data = file_generator.generate_json(request.data, request.filename, pretty=True)
        
        elif file_type in ["txt", "text"]:
            file_data = file_generator.generate_text(request.data, request.filename, format_type="readable")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
        
        # Return file as downloadable response
        return Response(
            content=file_data["content"],
            media_type=file_data["mime_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{file_data["filename"]}"',
                "Content-Length": str(file_data["size"])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare-courses")
async def compare_courses(request: CompareCourseRequest):
    """
    Compare multiple courses and generate insights
    Returns structured comparison table and AI-generated insights
    """
    try:
        if len(request.courses) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 courses to compare")
        
        if len(request.courses) > 5:
            logger.warning(f"Comparing more than 5 courses ({len(request.courses)}), limiting to first 5")
            request.courses = request.courses[:5]
        
        logger.info(f"Comparing {len(request.courses)} courses")
        
        # Generate comparison
        comparison = course_comparator.compare_courses(
            courses=request.courses,
            comparison_criteria=request.comparison_criteria
        )
        
        if "error" in comparison:
            raise HTTPException(status_code=500, detail=comparison["error"])
        
        return {
            "status": "success",
            "comparison_table": comparison["comparison_table"],
            "insights": comparison["insights"],
            "recommendation": comparison["recommendation"],
            "course_count": comparison["course_count"],
            "student_id": request.student_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing courses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-manual-escalation", response_model=Escalation)
async def create_manual_escalation(
    student_id: str,
    question: str,
    ai_response: str,
    conversation_history: List[ConversationMessage] = [],
    reason: str = "Student requested advisor help"
):
    """
    Manually create an escalation when student clicks "Send to Advisor" button
    """
    try:
        from routers.advisor import create_escalation
        
        escalation_request = CreateEscalationRequest(
            student_id=student_id,
            question=question,
            ai_response=ai_response,
            conversation_history=conversation_history,
            escalation_reason=reason,
            priority=2  # Manual escalations get medium priority
        )
        
        escalation = await create_escalation(escalation_request)
        
        logger.info(f"Created manual escalation {escalation['id']} for student {student_id}")
        
        return escalation
        
    except Exception as e:
        logger.error(f"Error creating manual escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/escalations/student/{student_id}")
async def get_student_escalations(student_id: str):
    """
    Get all escalations for a specific student
    Used to show escalation history in student chat
    """
    try:
        from routers.advisor import get_all_escalations
        
        escalations = await get_all_escalations(student_id=student_id)
        
        return {
            "student_id": student_id,
            "escalations": escalations,
            "count": len(escalations)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving student escalations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escalations/{escalation_id}/respond")
async def student_respond_to_escalation(
    escalation_id: str,
    message: str,
    student_id: str
):
    """
    Student responds to advisor's message on an escalation
    """
    try:
        from routers.advisor import update_escalation, load_escalations, save_escalations
        from utils.schema import UpdateEscalationRequest
        
        # Load escalation
        escalations = load_escalations()
        escalation = next((e for e in escalations if e["id"] == escalation_id), None)
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Verify student owns this escalation
        if escalation.get("student_id") != student_id:
            raise HTTPException(status_code=403, detail="Not authorized to respond to this escalation")
        
        # Add student response to conversation
        student_response = {
            "role": "student",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if "responses" not in escalation:
            escalation["responses"] = []
        
        escalation["responses"].append(student_response)
        escalation["updated_at"] = datetime.now().isoformat()
        
        # Update status to in_progress if it was pending
        if escalation.get("status") == "pending":
            escalation["status"] = "in_progress"
        
        # Save changes
        for i, esc in enumerate(escalations):
            if esc["id"] == escalation_id:
                escalations[i] = escalation
                break
        
        save_escalations(escalations)
        
        # Notify assigned advisor if exists
        if escalation.get("assigned_to"):
            notification_system.notify_student_response(
                escalation_id,
                escalation.get("assigned_to"),
                student_id
            )
        
        logger.info(f"Student {student_id} responded to escalation {escalation_id}")
        
        return {
            "status": "success",
            "escalation_id": escalation_id,
            "message": "Response added successfully",
            "timestamp": student_response["timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/escalations/{escalation_id}/messages")
async def get_escalation_messages(escalation_id: str, student_id: str):
    """
    Get all messages for an escalation (advisor + student responses)
    """
    try:
        from routers.advisor import load_escalations
        
        escalations = load_escalations()
        escalation = next((e for e in escalations if e["id"] == escalation_id), None)
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Verify student owns this escalation
        if escalation.get("student_id") != student_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this escalation")
        
        messages = {
            "escalation_id": escalation_id,
            "status": escalation.get("status"),
            "advisor_notes": escalation.get("advisor_notes", []),
            "responses": escalation.get("responses", []),
            "assigned_to": escalation.get("assigned_to")
        }
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving escalation messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escalations/{escalation_id}/advisor-respond")
async def advisor_respond_to_student(
    escalation_id: str,
    message: str,
    advisor_name: str = "Advisor"
):
    """
    Advisor responds to student on an escalation
    This message will be visible to the student
    """
    try:
        from routers.advisor import load_escalations, save_escalations
        
        escalations = load_escalations()
        escalation_idx = next(
            (i for i, e in enumerate(escalations) if e["id"] == escalation_id),
            None
        )
        
        if escalation_idx is None:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        escalation = escalations[escalation_idx]
        
        # Add advisor response
        advisor_response = {
            "role": "advisor",
            "content": message,
            "advisor_name": advisor_name,
            "timestamp": datetime.now().isoformat()
        }
        
        if "responses" not in escalation:
            escalation["responses"] = []
        
        escalation["responses"].append(advisor_response)
        escalation["updated_at"] = datetime.now().isoformat()
        escalation["status"] = "in_progress"
        
        # Assign to advisor if not already assigned
        if not escalation.get("assigned_to"):
            escalation["assigned_to"] = advisor_name
        
        # Save changes
        escalations[escalation_idx] = escalation
        save_escalations(escalations)
        
        # Send notification to student
        student_id = escalation.get("student_id")
        if student_id:
            notification_system.notify_advisor_response(escalation_id, student_id, advisor_name)
        
        logger.info(f"Advisor {advisor_name} responded to escalation {escalation_id}")
        
        return {
            "status": "success",
            "escalation_id": escalation_id,
            "message": "Response sent to student",
            "timestamp": advisor_response["timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error advisor responding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for AI actions service"""
    return {
        "status": "healthy",
        "services": {
            "intent_detector": "active",
            "file_generator": "active",
            "course_comparator": "active"
        }
    }

