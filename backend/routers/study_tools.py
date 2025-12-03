# backend/routers/study_tools.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import requests
from models.llm_client import LLMClient

# router = APIRouter(prefix="/study", tags=["study"])
router = APIRouter()

class FlashcardRequest(BaseModel):
    topic: str = "key concepts"
    count: int = 8
    context: str

class QuizRequest(BaseModel):
    topic: str = "key concepts"
    num_questions: int = 6
    context: str

class SummaryRequest(BaseModel):
    context: str

class ExplainRequest(BaseModel):
    concept: str
    context: str


@router.post("/flashcards")
async def generate_flashcards(req: FlashcardRequest):
    llm = LLMClient()

    # FIXED: Use raw string or escape braces properly
    prompt = f"""Generate {req.count} high-quality, concise flashcards from the study material below.
Focus on: {req.topic}

Study Material:
{req.context[:25000]}

Return ONLY a valid JSON array of objects with this exact structure:
[
  {{"question": "What is attention mechanism?", "answer": "A technique that..."}},
  {{"question": "Name 3 types of attention", "answer": "Self-attention, multi-head..."}}
]

Do not include any explanations, markdown, or extra text. Only valid JSON."""

    try:
        messages = [
            {"role": "system", "content": "You are an expert flashcard creator. Always respond with clean, parseable JSON only."},
            {"role": "user", "content": prompt}
        ]

        response = llm._raw_request(messages, max_tokens=4000, temperature=0.3)
        json_text = _extract_json(response)

        flashcards = json.loads(json_text)
        return {"flashcards": flashcards}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {str(e)}")


@router.post("/quiz")
async def generate_quiz(req: QuizRequest):
    llm = LLMClient()

    prompt = f"""Create {req.num_questions} high-quality multiple-choice questions from the material.
Topic focus: {req.topic}

Material:
{req.context[:25000]}

Return ONLY valid JSON in this exact format:
[
  {{
    "question": "What is the capital of France?",
    "options": ["London", "Berlin", "Paris", "Madrid"],
    "correct_index": 2,
    "explanation": "Paris is the capital city of France."
  }}
]

No markdown, no extra text, only JSON."""

    try:
        messages = [
            {"role": "system", "content": "You are a professional quiz creator. Return clean JSON only."},
            {"role": "user", "content": prompt}
        ]

        response = llm._raw_request(messages, max_tokens=3000, temperature=0.5)
        json_text = _extract_json(response)

        quiz = json.loads(json_text)
        return {"quiz": quiz}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@router.post("/summary")
async def summarize(req: SummaryRequest):
    llm = LLMClient()
    prompt = f"Summarize the following study material in 300-500 words, clearly and accurately:\n\n{req.context[:30000]}"

    try:
        messages = [{"role": "system", "content": "You are an expert summarizer."}, {"role": "user", "content": prompt}]
        response = llm._raw_request(messages, max_tokens=1000)
        return {"summary": response.strip()}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/explain")
async def explain(req: ExplainRequest):
    llm = LLMClient()
    prompt = f"Explain the concept '{req.concept}' clearly and thoroughly using only the provided study material:\n\n{req.context[:25000]}"

    try:
        messages = [{"role": "system", "content": "You are a world-class professor."}, {"role": "user", "content": prompt}]
        response = llm._raw_request(messages, max_tokens=1500, temperature=0.4)
        return {"explanation": response.strip()}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# === Helper Functions ===
def _extract_json(text: str) -> str:
    """Extract JSON from LLM response (handles code blocks)"""
    text = text.strip()
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    # If no code block, assume it's raw JSON
    start = text.find("[")
    end = text.rfind("]") + 1
    if start != -1 and end > start:
        return text[start:end]
    return text


# Add this method to LLMClient if not exists
# → Add to models/llm_client.py
def _raw_request(self, messages: List[Dict], max_tokens: int = 1000, temperature: float = 0.3) -> str:
    payload = {
        "model": self.model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8888",
        "X-Title": "SUNY Study Tools"
    }
    resp = requests.post(self.base_url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']