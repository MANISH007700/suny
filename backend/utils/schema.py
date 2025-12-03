from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., description="User's academic question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")

class Citation(BaseModel):
    """Citation information"""
    doc_id: str = Field(..., description="Source document identifier")
    snippet: str = Field(..., description="Text snippet from the document")

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="Generated answer")
    citations: List[Citation] = Field(..., description="List of citations")

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