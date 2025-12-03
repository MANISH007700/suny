from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
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
    [{"question": "...", "answer": "..."}, ...]
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