# routers/academic_guidance.py
from fastapi import APIRouter, HTTPException
from utils.schema import ChatRequest, ChatResponse, InitRequest, InitResponse
from models.rag_pipeline import RAGPipeline
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Singleton pattern
_rag_pipeline = None

def get_rag_pipeline():
    global _rag_pipeline
    if _rag_pipeline is None:
        logger.info("Creating new RAG Pipeline instance")
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.query(request.question, request.top_k)
        return ChatResponse(answer=result["answer"], citations=result["citations"])
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/init", response_model=InitResponse)
async def initialize(request: InitRequest = InitRequest()):
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.initialize_from_pdfs(
            pdf_dir=request.pdf_dir or "./backend/data/pdfs/",
            force_rebuild=request.force_rebuild
        )
        
        already_populated = pipeline.is_vector_store_populated() and not request.force_rebuild
        
        return InitResponse(
            status="success",
            message="Already initialized — skipping rebuild" if already_populated and not request.force_rebuild else result["message"],
            count=result.get("count", 0),
            skipped=already_populated
        )
    except Exception as e:
        logger.error(f"Init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    try:
        pipeline = get_rag_pipeline()
        return {
            "status": "healthy",
            "vector_store": pipeline.vector_store_type,
            "embedding_model": "all-mpnet-base-v2"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    try:
        pipeline = get_rag_pipeline()
        populated = pipeline.is_vector_store_populated()
        count = pipeline.vector_store.count() if pipeline.vector_store_type == "chroma" else 0
        return {
            "is_populated": populated,
            "count": count,
            "vector_store_type": pipeline.vector_store_type
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {"is_populated": False, "count": 0, "vector_store_type": "error"}