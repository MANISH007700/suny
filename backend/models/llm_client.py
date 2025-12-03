import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.5-flash"
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    def get_system_prompt(self) -> str:
        return """You are an AI Academic Advisor for SUNY (State University of New York).

Your role is to help students with:
- Course selection and planning
- Prerequisites and co-requisites
- Graduation requirements
- Major and minor requirements
- Academic policies and procedures

IMPORTANT RULES:
1. Use ONLY the retrieved context from the provided PDF documents
2. If information is not in the context, clearly state "I don't have that information in the available documents"
3. Always cite your sources by mentioning the document name
4. Be specific and provide detailed answers when information is available
5. If asked about overlapping requirements, analyze all relevant documents
6. Format your response clearly with bullet points or numbered lists when appropriate

Remember: You must base your answers strictly on the provided context."""

    def generate_response(self, question: str, context: List[Dict], top_k: int = 5) -> Dict:
        """
        Generate response using Gemini 2.5 Flash via OpenRouter
        
        Args:
            question: User's question
            context: List of retrieved document chunks with metadata
            top_k: Number of context chunks to include
        
        Returns:
            Dict with 'answer' and 'citations'
        """
        try:
            # Build context string from retrieved chunks
            context_str = self._build_context_string(context[:top_k])
            import pdb; pdb.set_trace()
            # Build messages
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"""Context from SUNY documents:
{context_str}

Student Question: {question}

Please provide a detailed answer based on the context above. Include specific citations."""}
            ]
            
            # Make API request
            headers = self._get_headers()
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            logger.info(f"Sending request to OpenRouter with model: {self.model}")
            response = requests.post(self.base_url, headers=headers, json=payload)

            # Handle rate limiting from OpenRouter gracefully
            if response.status_code == 429:
                logger.warning("Received 429 Too Many Requests from OpenRouter")
                friendly_message = (
                    "I'm currently being rate-limited by the AI provider (OpenRouter), "
                    "so I can't process new questions for a short time.\n\n"
                    "Please wait 30–60 seconds and then try your question again."
                )
                
                citations = self._extract_citations(context[:top_k])
                return {
                    "answer": friendly_message,
                    "citations": citations
                }

            # Raise for all other error codes
            response.raise_for_status()
            
            data = response.json()
            answer = data['choices'][0]['message']['content']
            
            # Extract citations from context
            citations = self._extract_citations(context[:top_k])
            
            logger.info("Successfully generated response")
            return {
                "answer": answer,
                "citations": citations
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Headers required for OpenRouter requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("APP_BASE_URL", "http://localhost:8501"),
            "X-Title": "SUNY Academic Guidance System"
        }
    
    def _build_context_string(self, context: List[Dict]) -> str:
        """Build formatted context string from retrieved chunks"""
        context_parts = []
        for i, chunk in enumerate(context, 1):
            doc_name = chunk.get('metadata', {}).get('source', 'Unknown')
            text = chunk.get('text', '')
            context_parts.append(f"[Document {i}: {doc_name}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def _extract_citations(self, context: List[Dict]) -> List[Dict]:
        """Extract citation information from context"""
        citations = []
        for chunk in context:
            metadata = chunk.get('metadata', {})
            citations.append({
                "doc_id": metadata.get('source', 'Unknown'),
                "snippet": chunk.get('text', '')[:200] + "..."
            })
        return citations