# routers/academic_guidance.py
from fastapi import APIRouter, HTTPException
from utils.schema import ChatRequest, ChatResponse, InitRequest, InitResponse
from models.rag_pipeline import RAGPipeline
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Singleton pattern for RAG Pipeline
_rag_pipeline = None

def get_rag_pipeline():
    """Get or create RAG Pipeline singleton"""
    global _rag_pipeline
    if _rag_pipeline is None:
        logger.info("Creating new RAG Pipeline instance")
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline

@router.get("/health")
async def health():
    """Health check endpoint"""
    try:
        pipeline = get_rag_pipeline()
        return {
            "status": "healthy",
            "vector_store_type": pipeline.vector_store_type,
            "embedding_model": "all-mpnet-base-v2"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    """Check if vector store is populated and get document count"""
    try:
        pipeline = get_rag_pipeline()
        is_populated = pipeline.is_vector_store_populated()
        count = pipeline.get_vector_store_count()
        
        logger.info(f"Status check: populated={is_populated}, count={count}")
        
        return {
            "is_populated": is_populated,
            "count": count,
            "status": "ready" if is_populated else "empty",
            "vector_store_type": pipeline.vector_store_type
        }
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return {
            "is_populated": False,
            "count": 0,
            "status": "error",
            "error": str(e),
            "vector_store_type": "unknown"
        }

@router.post("/init", response_model=InitResponse)
async def initialize(request: InitRequest = InitRequest()):
    """Initialize the RAG system by processing PDFs"""
    try:
        pipeline = get_rag_pipeline()
        
        # Log the initialization request
        logger.info(f"Initialization requested: pdf_dir={request.pdf_dir}, force_rebuild={request.force_rebuild}")
        
        # Check if already populated (unless force rebuild)
        if not request.force_rebuild and pipeline.is_vector_store_populated():
            count = pipeline.get_vector_store_count()
            logger.info(f"Vector store already populated with {count} chunks, skipping initialization")
            return InitResponse(
                status="success",
                message=f"Already initialized with {count} chunks",
                count=count,
                skipped=True
            )
        
        # Perform initialization
        result = pipeline.initialize_from_pdfs(
            pdf_dir=request.pdf_dir or "./backend/data/pdfs/",
            force_rebuild=request.force_rebuild
        )
        
        # Check if the result indicates an error
        if result.get("status") == "error":
            logger.error(f"Initialization failed: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Initialization complete: {result.get('message')}")
        
        return InitResponse(
            status=result.get("status", "success"),
            message=result.get("message", "Initialization complete"),
            count=result.get("count", 0),
            skipped=result.get("skipped", False)
        )
        
    except Exception as e:
        logger.error(f"Init error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for RAG queries with automatic escalation detection"""
    try:
        pipeline = get_rag_pipeline()
        
        # Check if vector store is populated
        if not pipeline.is_vector_store_populated():
            logger.warning("Chat attempted but vector store is empty")
            return ChatResponse(
                answer="The knowledge base is empty. Please initialize the system first.",
                citations=[],
                escalation_id=None
            )
        
        logger.info(f"Processing query: '{request.question[:50]}...' with top_k={request.top_k}")
        
        # Perform RAG query
        result = pipeline.query(request.question, request.top_k)
        answer = result.get("answer", "No answer generated")
        citations = result.get("citations", [])
        context = result.get("context", [])
        
        logger.info(f"Query successful, returned {len(citations)} citations")
        
        # Check if escalation is needed
        escalation_id = None
        if request.student_id:
            should_escalate, escalation_reason = pipeline.llm_client.detect_escalation_needed(
                request.question, answer, context
            )
            
            if should_escalate:
                # Create escalation
                from datetime import datetime
                import uuid
                import json
                import os
                
                escalation_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                escalation_data = {
                    "id": escalation_id,
                    "student_id": request.student_id,
                    "question": request.question,
                    "ai_response": answer,
                    "conversation_history": [
                        {"role": "user", "content": request.question, "timestamp": now},
                        {"role": "assistant", "content": answer, "timestamp": now}
                    ],
                    "status": "pending",
                    "escalation_reason": escalation_reason,
                    "created_at": now,
                    "updated_at": now,
                    "advisor_notes": [],
                    "assigned_to": None,
                    "priority": 3 if "urgent" in request.question.lower() else 2
                }
                
                # Save escalation
                escalations_file = "./backend/data/escalations.json"
                os.makedirs("./backend/data", exist_ok=True)
                
                escalations = []
                if os.path.exists(escalations_file):
                    try:
                        with open(escalations_file, 'r') as f:
                            escalations = json.load(f)
                    except:
                        pass
                
                escalations.append(escalation_data)
                with open(escalations_file, 'w') as f:
                    json.dump(escalations, f, indent=2)
                
                logger.info(f"Created escalation {escalation_id} - Reason: {escalation_reason}")
        
        return ChatResponse(
            answer=answer,
            citations=citations,
            escalation_id=escalation_id
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

# Debug endpoints (optional - remove in production)
@router.get("/debug/vector-store")
async def debug_vector_store():
    """Debug endpoint to inspect vector store contents"""
    try:
        pipeline = get_rag_pipeline()
        
        if pipeline.vector_store_type == "chroma":
            # Get sample documents
            results = pipeline.vector_store.get(
                limit=5,
                include=["metadatas", "documents"]
            )
            
            return {
                "type": "chroma",
                "total_count": pipeline.vector_store.count(),
                "sample_count": len(results.get("ids", [])),
                "sample_ids": results.get("ids", [])[:5],
                "sample_sources": [m.get("source") for m in results.get("metadatas", [])][:5],
                "sample_chunks": [
                    {
                        "id": id_,
                        "source": meta.get("source"),
                        "chunk_index": meta.get("chunk_index"),
                        "text_preview": doc[:150] + "..."
                    }
                    for id_, meta, doc in zip(
                        results.get("ids", [])[:5],
                        results.get("metadatas", [])[:5],
                        results.get("documents", [])[:5]
                    )
                ]
            }
        else:
            return {
                "type": "pinecone",
                "message": "Debug not fully implemented for Pinecone"
            }
            
    except Exception as e:
        logger.error(f"Debug error: {e}")
        return {"error": str(e)}

@router.post("/debug/test-retrieval")
async def test_retrieval(request: dict):
    """Test retrieval with a sample query"""
    query = request.get("query", "computer science requirements")
    
    try:
        pipeline = get_rag_pipeline()
        
        # Generate embedding
        query_embedding = pipeline.embedding_model.embed_text(query)
        logger.info(f"Generated query embedding with dimension: {len(query_embedding)}")
        
        # Query vector store
        results = pipeline.vector_store.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["metadatas", "documents", "distances"]
        )
        
        retrieved_docs = []
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results.get('distances', [[]])[0]
        ):
            retrieved_docs.append({
                "source": meta.get("source"),
                "chunk_index": meta.get("chunk_index"),
                "distance": float(dist) if dist is not None else None,
                "text_preview": doc[:200] + "..."
            })
        
        return {
            "query": query,
            "embedding_dim": len(query_embedding),
            "results_count": len(results['documents'][0]),
            "retrieved_docs": retrieved_docs
        }
        
    except Exception as e:
        logger.error(f"Test retrieval error: {e}", exc_info=True)
        return {"error": str(e)}