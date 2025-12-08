# routers/courses.py
from fastapi import APIRouter, HTTPException
from utils.schema import (
    CourseRecommendationRequest, 
    CourseRecommendationResponse,
    InitCoursesRequest,
    InitCoursesResponse
)
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
        logger.info("Creating new RAG Pipeline instance for courses")
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline

@router.post("/init", response_model=InitCoursesResponse)
async def initialize_courses(request: InitCoursesRequest = InitCoursesRequest()):
    """
    Initialize the course catalog by ingesting courses from JSON into vector database
    """
    try:
        pipeline = get_rag_pipeline()
        
        logger.info(f"Course initialization requested: path={request.courses_json_path}, force_rebuild={request.force_rebuild}")
        
        # Check if already populated (unless force rebuild)
        if not request.force_rebuild and pipeline.courses_collection.count() > 0:
            count = pipeline.courses_collection.count()
            logger.info(f"Courses already initialized with {count} courses, skipping")
            return InitCoursesResponse(
                status="success",
                message=f"Already initialized with {count} courses",
                count=count,
                skipped=True
            )
        
        # Perform initialization
        result = pipeline.initialize_courses(
            courses_json_path=request.courses_json_path,
            force_rebuild=request.force_rebuild
        )
        
        # Check if the result indicates an error
        if result.get("status") == "error":
            logger.error(f"Course initialization failed: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Course initialization complete: {result.get('message')}")
        
        return InitCoursesResponse(
            status=result.get("status", "success"),
            message=result.get("message", "Initialization complete"),
            count=result.get("count", 0),
            skipped=result.get("skipped", False)
        )
        
    except Exception as e:
        logger.error(f"Course init error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Course initialization failed: {str(e)}")

@router.post("/recommend", response_model=CourseRecommendationResponse)
async def recommend_courses(request: CourseRecommendationRequest):
    """
    Get personalized course recommendations based on student interests and goals
    """
    try:
        pipeline = get_rag_pipeline()
        
        # Check if courses are loaded
        if pipeline.courses_collection.count() == 0:
            logger.warning("Course recommendation attempted but courses not loaded")
            return CourseRecommendationResponse(
                recommendations="The course catalog is not loaded yet. Please initialize the courses first.",
                courses=[],
                count=0
            )
        
        logger.info(f"Processing course recommendation query: '{request.query[:50]}...' with top_k={request.top_k}")
        
        # Query courses from vector database
        result = pipeline.query_courses(request.query, request.top_k)
        courses = result.get("courses", [])
        
        if not courses:
            logger.info("No relevant courses found")
            return CourseRecommendationResponse(
                recommendations="I couldn't find any courses matching your interests. Could you provide more details about what you're looking for?",
                courses=[],
                count=0
            )
        
        logger.info(f"Found {len(courses)} relevant courses")
        
        # Generate personalized recommendations using LLM
        recommendations = pipeline.llm_client.generate_course_recommendations(
            student_query=request.query,
            retrieved_courses=courses,
            student_context=request.student_context
        )
        
        logger.info("Successfully generated course recommendations")
        
        return CourseRecommendationResponse(
            recommendations=recommendations,
            courses=courses,
            count=len(courses)
        )
        
    except Exception as e:
        logger.error(f"Course recommendation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Course recommendation failed: {str(e)}")

@router.get("/status")
async def get_courses_status():
    """Check if courses are loaded and get count"""
    try:
        pipeline = get_rag_pipeline()
        count = pipeline.courses_collection.count()
        
        logger.info(f"Courses status check: count={count}")
        
        return {
            "is_loaded": count > 0,
            "count": count,
            "status": "ready" if count > 0 else "empty"
        }
    except Exception as e:
        logger.error(f"Error checking courses status: {e}")
        return {
            "is_loaded": False,
            "count": 0,
            "status": "error",
            "error": str(e)
        }

@router.get("/search")
async def search_courses(query: str, limit: int = 5):
    """
    Simple course search endpoint (without LLM recommendations)
    Returns raw course matches from vector database
    """
    try:
        pipeline = get_rag_pipeline()
        
        if pipeline.courses_collection.count() == 0:
            return {
                "courses": [],
                "message": "Course catalog not loaded"
            }
        
        result = pipeline.query_courses(query, limit)
        
        return {
            "courses": result.get("courses", []),
            "count": len(result.get("courses", [])),
            "message": result.get("message", "")
        }
        
    except Exception as e:
        logger.error(f"Course search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

