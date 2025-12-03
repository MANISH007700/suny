from fastapi import APIRouter, HTTPException
from utils.schema import ChatRequest, ChatResponse, InitRequest, InitResponse
from models.rag_pipeline import RAGPipeline
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Global RAG pipeline instance
rag_pipeline = None

def get_rag_pipeline():
    """Get or create RAG pipeline instance"""
    global rag_pipeline
    if rag_pipeline is None:
        logger.info("Creating RAG pipeline instance")
        rag_pipeline = RAGPipeline()
    return rag_pipeline

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for academic guidance
    
    Args:
        request: ChatRequest with question and top_k
    
    Returns:
        ChatResponse with answer and citations
    """
    try:
        logger.info(f"Received chat request: {request.question[:50]}...")
        
        pipeline = get_rag_pipeline()
        result = pipeline.query(request.question, request.top_k)
        
        return ChatResponse(
            answer=result['answer'],
            citations=result['citations']
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/init", response_model=InitResponse)
async def initialize(request: InitRequest = InitRequest()):
    """
    Initialize the RAG system by loading and processing PDFs
    
    Args:
        request: InitRequest with optional pdf_dir and force_rebuild
    
    Returns:
        InitResponse with status and count
    """
    try:
        logger.info(f"Initializing RAG system from {request.pdf_dir}")
        
        pipeline = get_rag_pipeline()
        result = pipeline.initialize_from_pdfs(request.pdf_dir)
        
        return InitResponse(
            status=result['status'],
            message=result['message'],
            count=result['count']
        )
        
    except Exception as e:
        logger.error(f"Error in init endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    """Health check endpoint"""
    try:
        pipeline = get_rag_pipeline()
        return {
            "status": "healthy",
            "vector_store": pipeline.vector_store_type,
            "embedding_model": "all-mpnet-base-v2"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    """Get vector store status"""
    try:
        pipeline = get_rag_pipeline()
        is_populated = pipeline.is_vector_store_populated()
        
        count = 0
        if pipeline.vector_store_type == "chroma":
            count = pipeline.vector_store.count()
        
        return {
            "is_populated": is_populated,
            "count": count,
            "vector_store_type": pipeline.vector_store_type
        }
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))