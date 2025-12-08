from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., description="User's academic question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    student_id: Optional[str] = Field(default=None, description="Student identifier for tracking")

class Citation(BaseModel):
    """Citation information"""
    doc_id: str = Field(..., description="Source document identifier")
    snippet: str = Field(..., description="Text snippet from the document")

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="Generated answer")
    citations: List[Citation] = Field(..., description="List of citations")
    escalation_id: Optional[str] = Field(default=None, description="ID if question was escalated")

class InitRequest(BaseModel):
    """Request model for initialization"""
    pdf_dir: Optional[str] = Field(default="./data/pdfs/", description="Directory containing PDFs")
    force_rebuild: bool = Field(default=False, description="Force rebuild even if data exists")

class InitResponse(BaseModel):
    """Response model for initialization"""
    status: str = Field(..., description="Status of initialization")
    message: str = Field(..., description="Detailed message")
    count: int = Field(..., description="Number of chunks processed")
    skipped: bool = Field(default=False, description="Whether initialization was skipped")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    vector_store: str
    embedding_model: str

# === ADVISOR PERSONA SCHEMAS ===

class EscalationStatus(str, Enum):
    """Status of an escalation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class RiskLevel(str, Enum):
    """Student risk level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ConversationMessage(BaseModel):
    """Individual message in conversation"""
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO timestamp")
    
    class Config:
        from_attributes = True

class StudentProfile(BaseModel):
    """Student profile information"""
    student_id: str = Field(..., description="Unique student ID")
    name: str = Field(default="Unknown Student", description="Student name")
    major: str = Field(default="Undeclared", description="Student major")
    gpa: Optional[float] = Field(default=None, description="Current GPA")
    completed_courses: List[str] = Field(default=[], description="List of completed courses")
    current_courses: List[str] = Field(default=[], description="Current enrolled courses")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Academic risk level")
    total_escalations: int = Field(default=0, description="Total number of escalations")
    last_interaction: Optional[str] = Field(default=None, description="Last interaction timestamp")

class AdvisorNote(BaseModel):
    """Advisor note with timestamp"""
    note: str = Field(..., description="Note content")
    timestamp: str = Field(..., description="When note was added")
    
    class Config:
        from_attributes = True

class Escalation(BaseModel):
    """Escalated student question"""
    id: str = Field(..., description="Unique escalation ID")
    student_id: str = Field(..., description="Student who asked the question")
    question: str = Field(..., description="Original question")
    ai_response: str = Field(..., description="AI's response")
    conversation_history: List[ConversationMessage] = Field(default=[], description="Full conversation")
    status: EscalationStatus = Field(default=EscalationStatus.PENDING, description="Current status")
    escalation_reason: str = Field(..., description="Why this was escalated")
    created_at: str = Field(..., description="When escalation was created")
    updated_at: str = Field(..., description="Last update timestamp")
    advisor_notes: List[AdvisorNote] = Field(default=[], description="Notes from advisors")
    assigned_to: Optional[str] = Field(default=None, description="Assigned advisor")
    priority: int = Field(default=1, description="Priority level 1-5")
    
    class Config:
        from_attributes = True

class EscalationResponse(BaseModel):
    """Response with escalation and student profile"""
    escalation: Escalation
    student_profile: StudentProfile

class UpdateEscalationRequest(BaseModel):
    """Request to update escalation"""
    status: Optional[EscalationStatus] = None
    note: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[int] = None

class CreateEscalationRequest(BaseModel):
    """Request to manually create an escalation"""
    student_id: str
    question: str
    ai_response: str
    conversation_history: List[ConversationMessage] = []
    escalation_reason: str = "Manual escalation"
    priority: int = 1

class AudioTranscriptionResponse(BaseModel):
    """Response model for audio transcription"""
    text: str = Field(..., description="Transcribed text from audio")
    success: bool = Field(..., description="Whether transcription was successful")
    error: Optional[str] = Field(default=None, description="Error message if any")

# === COURSE RECOMMENDATION SCHEMAS ===

class CourseRecommendationRequest(BaseModel):
    """Request model for course recommendations"""
    query: str = Field(..., description="Student's question or interest about courses")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of courses to retrieve")
    student_context: Optional[dict] = Field(default=None, description="Optional student context (major, level, interests)")

class CourseMetadata(BaseModel):
    """Course metadata"""
    course_id: str = Field(..., description="Course ID")
    title: str = Field(..., description="Course title")
    institution: str = Field(..., description="Institution name")
    code: str = Field(..., description="Course code")
    subject_area: str = Field(..., description="Subject area")
    credits: str = Field(..., description="Number of credits")
    level: str = Field(default="", description="Course level")
    start_date: str = Field(default="", description="Start date")
    delivery_mode: str = Field(default="", description="Delivery mode")
    instructor: str = Field(default="", description="Instructor name")
    url: str = Field(default="", description="Course URL")

class CourseRecommendationResponse(BaseModel):
    """Response model for course recommendations"""
    recommendations: str = Field(..., description="Formatted course recommendations")
    courses: List[dict] = Field(..., description="List of retrieved courses with metadata")
    count: int = Field(..., description="Number of courses found")

class InitCoursesRequest(BaseModel):
    """Request model for course initialization"""
    courses_json_path: Optional[str] = Field(
        default="/Users/DLP-I516-206/Desktop/ubi-code/suny/suny_courses_data/suny_all_courses_html.json",
        description="Path to courses JSON file"
    )
    force_rebuild: bool = Field(default=False, description="Force rebuild even if data exists")

class InitCoursesResponse(BaseModel):
    """Response model for course initialization"""
    status: str = Field(..., description="Status of initialization")
    message: str = Field(..., description="Detailed message")
    count: int = Field(..., description="Number of courses processed")
    skipped: bool = Field(default=False, description="Whether initialization was skipped")