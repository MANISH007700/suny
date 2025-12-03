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
    """Chat endpoint for RAG queries"""
    try:
        pipeline = get_rag_pipeline()
        
        # Check if vector store is populated
        if not pipeline.is_vector_store_populated():
            logger.warning("Chat attempted but vector store is empty")
            return ChatResponse(
                answer="The knowledge base is empty. Please initialize the system first.",
                citations=[]
            )
        
        logger.info(f"Processing query: '{request.question[:50]}...' with top_k={request.top_k}")
        
        # Perform RAG query
        result = pipeline.query(request.question, request.top_k)
        
        logger.info(f"Query successful, returned {len(result.get('citations', []))} citations")
        
        return ChatResponse(
            answer=result.get("answer", "No answer generated"),
            citations=result.get("citations", [])
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