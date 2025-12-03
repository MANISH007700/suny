from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import date
import json
import requests

router = APIRouter()

class FlashcardRequest(BaseModel):
    topic: str = "key concepts"
    count: int = 5
    context: str

class QuizRequest(BaseModel):
    topic: str = "key concepts"
    num_questions: int = 5
    context: str

class ScheduleRequest(BaseModel):
    exam_date: date
    hours_per_day: int = 3
    topics: List[str] = []
    context: str

@router.post("/flashcards")
async def generate_flashcards(req: FlashcardRequest):
    from models.llm_client import LLMClient
    llm = LLMClient()
    
    prompt = f"""
    Generate {req.count} high-quality flashcards from the following study material.
    Topic focus: {req.topic}

    Material:
    {req.context[:25000]}

    Return ONLY a valid JSON array like:
    [{{"question": "...", "answer": "..."}}, ...]
    """

    try:
        messages = [
            {"role": "system", "content": "You are an expert study coach. Create clear, effective short flashcards."},
            {"role": "user", "content": prompt}
        ]
        payload = {"model": llm.model, "messages": messages, "temperature": 0.2, "max_tokens": 5000}
        import requests
        resp = requests.post(llm.base_url, headers=llm._get_headers(), json=payload)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content']
        
        # Clean JSON
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
            
        flashcards = json.loads(json_str)
        return {"flashcards": flashcards}
    except Exception as e:
        raise HTTPException(500, f"Flashcard generation failed: {str(e)}")

@router.post("/quiz")
async def generate_quiz(req: QuizRequest):
    from models.llm_client import LLMClient
    llm = LLMClient()
    
    prompt = f"""
    Create {req.num_questions} challenging but fair multiple-choice questions from the documents.
    Topic: {req.topic}

    Study material:
    {req.context[:25000]}

    Return valid JSON:
    [
      {{
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "correct_index": 0,
        "explanation": "..."
      }}
    ]
    """

    try:
        messages = [
            {"role": "system", "content": "You are a master quiz creator."},
            {"role": "user", "content": prompt}
        ]
        payload = {"model": llm.model, "messages": messages, "temperature": 0.5, "max_tokens": 2000}
        import requests
        resp = requests.post(llm.base_url, headers=llm._get_headers(), json=payload)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content']
        
        json_str = content
        if "```json" in content: json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content: json_str = content.split("```")[1].split("```")[0]
            
        quiz = json.loads(json_str)
        return {"quiz": quiz}
    except Exception as e:
        raise HTTPException(500, f"Quiz generation failed: {str(e)}")

@router.post("/summary")
async def summarize(req: Dict):
    from models.llm_client import LLMClient
    llm = LLMClient()
    messages = [
        {"role": "system", "content": "Summarize clearly and concisely."},
        {"role": "user", "content": f"Summarize this study material in 300-500 words:\n\n{req.get('context', '')[:30000]}"}
    ]
    payload = {"model": llm.model, "messages": messages, "temperature": 0.2}
    resp = requests.post(llm.base_url, headers=llm._get_headers(), json=payload)
    resp.raise_for_status()
    return {"summary": resp.json()['choices'][0]['message']['content']}

@router.post("/explain")
async def explain(req: Dict):
    from models.llm_client import LLMClient
    llm = LLMClient()
    messages = [
        {"role": "system", "content": "Explain concepts like a world-class professor."},
        {"role": "user", "content": f"Explain '{req['concept']}' clearly using this material:\n\n{req.get('context', '')[:20000]}"}
    ]
    payload = {"model": llm.model, "messages": messages, "temperature": 0.4}
    resp = requests.post(llm.base_url, headers=llm._get_headers(), json=payload)
    resp.raise_for_status()
    return {"explanation": resp.json()['choices'][0]['message']['content']}

@router.post("/schedule")
async def create_schedule(req: ScheduleRequest):
    from models.llm_client import LLMClient
    llm = LLMClient()
    
    today = date.today()
    days_remaining = max((req.exam_date - today).days, 1)
    topics_text = ", ".join(req.topics) if req.topics else "key topics from the material"
    
    prompt = f"""
    You are an elite study planner. Build a focused day-by-day schedule to prepare for an exam in {days_remaining} day(s).
    Exam date: {req.exam_date.isoformat()}
    Available study hours per day: {req.hours_per_day}
    Focus topics: {topics_text}

    Material to leverage:
    {req.context[:25000]}

    Return ONLY valid JSON with this structure:
    [
      {{"day": "Day 1 (Mon)", "focus": "Topic", "tasks": ["task 1","task 2"], "hours": 3}},
      ...
    ]
    Ensure the plan spans all {days_remaining} day(s) leading up to the exam and balances review + practice.
    """
    
    try:
        messages = [
            {"role": "system", "content": "You create realistic, motivating study plans based on provided material."},
            {"role": "user", "content": prompt}
        ]
        payload = {"model": llm.model, "messages": messages, "temperature": 0.3, "max_tokens": 2000}
        resp = requests.post(llm.base_url, headers=llm._get_headers(), json=payload)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content']
        
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        
        schedule = json.loads(json_str)
        return {"schedule": schedule, "days": days_remaining}
    except Exception as e:
        raise HTTPException(500, f"Schedule generation failed: {str(e)}")