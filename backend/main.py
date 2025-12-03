from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import academic_guidance, study_tools, advisor
import logging


from dotenv import load_dotenv
load_dotenv(override=True)

import os
API_KEY = os.getenv("OPENROUTER_API_KEY")
print(API_KEY)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Academic Guidance RAG API",
    description="RAG-powered academic guidance system for SUNY",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(academic_guidance.router, prefix="/academic", tags=["academic"])
app.include_router(study_tools.router, prefix="/study", tags=["study"])
app.include_router(advisor.router, prefix="/advisor", tags=["advisor"])

@app.get("/")
async def root():
    return {
        "message": "Academic Guidance RAG API",
        "status": "running",
        "endpoints": ["/academic/chat", "/init"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)