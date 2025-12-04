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
3. Always cite your sources by mentioning the document name and page and id 
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
                "temperature": 0.1
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
    
    def detect_escalation_needed(self, question: str, answer: str, context: List[Dict]) -> tuple[bool, str]:
        """
        Use LLM to intelligently detect if a question should be escalated to human advisor.
        Makes a separate API call to Gemma model for smart escalation decision.
        
        Returns:
            (should_escalate: bool, reason: str)
        """
        try:
            # Build the escalation check prompt
            escalation_prompt = f"""You are an escalation decision system for an academic AI advisor. Your job is to determine if a student question needs human advisor review.

STUDENT QUESTION:
{question}

AI RESPONSE PROVIDED:
{answer}

NUMBER OF RELEVANT DOCUMENTS FOUND: {len(context)}

ESCALATION CRITERIA:
You should recommend ESCALATION (respond "ESCALATE") if:
1. AI response shows uncertainty or lacks information (phrases like "I don't have that information", "not in the documents", etc.)
2. Critical situations requiring immediate human intervention (mental health crisis, emergency, student wants to drop out entirely, severe academic distress)
3. Sensitive topics (financial aid, accommodations, appeals, waivers) WHERE the AI response is insufficient, unclear, or too brief
4. AI response is extremely brief (<20 words) and doesn't fully answer the question
5. No relevant documents were found (context count is 0) and answer is generic

You should recommend NO ESCALATION (respond "NO_ESCALATE") if:
1. AI provided a detailed, comprehensive answer with good information
2. Answer includes citations, sources, or specific references to documents
3. Answer is clear and directly addresses the question, even if brief
4. Question is straightforward and AI answered it well (e.g., "What's the deadline?" → "The deadline is March 15th")
5. The student received helpful, actionable information they can use

IMPORTANT: Be practical and conservative. Only escalate when the student truly needs human help. If the AI answered well, don't escalate.

Respond in this exact format:
DECISION: [ESCALATE or NO_ESCALATE]
REASON: [one sentence explaining why]

Do not include any other text."""

            # Make API call to Gemma model for escalation check
            headers = self._get_headers()
            
            payload = {
                "model": "google/gemma-3-4b-it",  # Fast, efficient model for classification
                "messages": [
                    {"role": "user", "content": escalation_prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.1  # Low temperature for consistent decisions
            }
            
            logger.info("Calling LLM for escalation decision check...")
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=5)
            
            # If API call fails, use conservative fallback (don't escalate unless obvious)
            if response.status_code != 200:
                logger.warning(f"Escalation check API call failed: {response.status_code}")
                # Simple fallback: only escalate if answer shows clear uncertainty
                if any(phrase in answer.lower() for phrase in ["i don't have", "not in the documents", "i cannot find", "unclear"]):
                    return True, "AI expressed uncertainty (fallback check)"
                return False, ""
            
            # Parse LLM response
            data = response.json()
            llm_response = data['choices'][0]['message']['content'].strip()
            
            logger.info(f"Escalation check response: {llm_response}")
            
            # Parse decision and reason
            decision_line = ""
            reason_line = ""
            
            for line in llm_response.split('\n'):
                line = line.strip()
                if line.startswith("DECISION:"):
                    decision_line = line.replace("DECISION:", "").strip().upper()
                elif line.startswith("REASON:"):
                    reason_line = line.replace("REASON:", "").strip()
            
            # Determine if should escalate
            should_escalate = "ESCALATE" in decision_line and "NO_ESCALATE" not in decision_line
            
            if should_escalate:
                reason = reason_line if reason_line else "LLM recommends human review"
                logger.info(f"Escalation decision: YES - {reason}")
                return True, reason
            else:
                logger.info("Escalation decision: NO - AI response is sufficient")
                return False, ""
                
        except Exception as e:
            logger.error(f"Error in escalation detection: {e}")
            # Conservative fallback: don't escalate on error unless answer is clearly insufficient
            if len(answer.split()) < 15 or "i don't have" in answer.lower():
                return True, "AI response appears insufficient (fallback due to check error)"
            return False, ""
    
    # ========== ADVISOR ASSIST TOOLS ==========
    
    def generate_outreach_email(self, escalation: Dict, student_profile: Dict) -> str:
        """Generate personalized outreach email to student"""
        try:
            prompt = f"""You are an academic advisor at SUNY. Generate a professional, warm, and personalized outreach email to a student.

STUDENT INFORMATION:
- Student ID: {student_profile.get('student_id', 'Unknown')}
- Name: {student_profile.get('name', 'Student')}
- Major: {student_profile.get('major', 'Undeclared')}
- GPA: {student_profile.get('gpa', 'N/A')}
- Risk Level: {student_profile.get('risk_level', 'low')}
- Total Escalations: {student_profile.get('total_escalations', 0)}

ESCALATION CONTEXT:
- Question: {escalation.get('question', '')}
- AI Response: {escalation.get('ai_response', '')}
- Escalation Reason: {escalation.get('escalation_reason', '')}
- Status: {escalation.get('status', 'pending')}
- Priority: {'⭐' * escalation.get('priority', 1)}

TASK:
Write a professional yet friendly email reaching out to the student. Address their concern, acknowledge their question, and offer to help. The tone should be:
- Supportive and encouraging
- Professional but warm
- Action-oriented (offer next steps)
- Show that you've reviewed their situation

Include:
1. Personalized greeting
2. Reference to their specific question/concern
3. Acknowledgment of their academic journey
4. Offer of assistance (meeting, phone call, etc.)
5. Your contact information placeholder
6. Professional closing

Keep it concise (200-300 words) and actionable.

Generate ONLY the email content without any additional commentary."""

            headers = self._get_headers()
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0.3
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Error generating outreach email: {e}")
            raise
    
    def generate_meeting_invitation(self, escalation: Dict, student_profile: Dict, meeting_details: Dict = None) -> str:
        """Generate meeting invitation text"""
        try:
            meeting_info = meeting_details or {}
            prompt = f"""You are an academic advisor at SUNY. Generate a professional meeting invitation for a student.

STUDENT INFORMATION:
- Name: {student_profile.get('name', 'Student')}
- Major: {student_profile.get('major', 'Undeclared')}

MEETING CONTEXT:
- Regarding: {escalation.get('question', 'Academic advising')}
- Reason for meeting: {escalation.get('escalation_reason', 'Follow-up discussion')}
- Suggested duration: {meeting_info.get('duration', '30 minutes')}
- Format: {meeting_info.get('format', 'In-person or Zoom')}

TASK:
Create a clear, professional meeting invitation that:
1. States the purpose clearly
2. Offers time flexibility
3. Explains what will be discussed
4. Provides logistics (format, duration)
5. Encourages the student to confirm or suggest alternative times
6. Maintains a welcoming, supportive tone

Keep it professional but friendly (150-200 words).

Generate ONLY the invitation text."""

            headers = self._get_headers()
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Error generating meeting invitation: {e}")
            raise
    
    def generate_session_summary(self, escalation: Dict, student_profile: Dict, session_notes: str = "") -> str:
        """Generate advising session summary"""
        try:
            prompt = f"""You are an academic advisor at SUNY. Create a comprehensive advising session summary.

STUDENT INFORMATION:
- Name: {student_profile.get('name', 'Student')}
- Student ID: {student_profile.get('student_id', 'Unknown')}
- Major: {student_profile.get('major', 'Undeclared')}
- GPA: {student_profile.get('gpa', 'N/A')}

SESSION CONTEXT:
- Initial Question/Concern: {escalation.get('question', '')}
- Discussion Points: {escalation.get('ai_response', '')}
- Escalation Reason: {escalation.get('escalation_reason', '')}

ADDITIONAL NOTES:
{session_notes if session_notes else 'Standard advising session'}

TASK:
Create a professional session summary that includes:
1. **Date & Purpose**: When and why the meeting occurred
2. **Topics Discussed**: Key points covered
3. **Student Concerns**: Main issues raised
4. **Recommendations Made**: Specific advice given
5. **Action Items**: What student should do next
6. **Follow-up**: Any scheduled next steps
7. **Overall Assessment**: Student's situation and outlook

Format it clearly with sections. Be thorough but concise (300-400 words).

Generate ONLY the summary."""

            headers = self._get_headers()
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Error generating session summary: {e}")
            raise
    
    def generate_recovery_plan(self, escalation: Dict, student_profile: Dict) -> str:
        """Generate academic recovery plan"""
        try:
            prompt = f"""You are an academic advisor at SUNY. Create a detailed academic recovery plan for a student.

STUDENT INFORMATION:
- Name: {student_profile.get('name', 'Student')}
- Major: {student_profile.get('major', 'Undeclared')}
- GPA: {student_profile.get('gpa', 'N/A')}
- Risk Level: {student_profile.get('risk_level', 'low')}
- Completed Courses: {', '.join(student_profile.get('completed_courses', [])[:5]) or 'None listed'}
- Current Courses: {', '.join(student_profile.get('current_courses', [])[:5]) or 'None listed'}

CURRENT SITUATION:
- Primary Concern: {escalation.get('question', '')}
- Escalation Reason: {escalation.get('escalation_reason', '')}
- Number of Prior Escalations: {student_profile.get('total_escalations', 0)}

TASK:
Create a comprehensive, actionable academic recovery plan that includes:

1. **Current Situation Assessment**: Brief analysis of student's status
2. **Immediate Priorities (Next 2 Weeks)**: 
   - 3-4 specific, achievable actions
3. **Short-term Goals (This Semester)**:
   - Academic objectives
   - GPA targets
   - Course completion plans
4. **Resources & Support**:
   - Tutoring centers
   - Study groups
   - Office hours
   - Mental health services (if applicable)
5. **Timeline & Milestones**:
   - Weekly check-ins
   - Mid-semester review
   - End-of-semester goals
6. **Success Metrics**:
   - How to measure progress
7. **Contingency Plans**:
   - What to do if struggling

Make it specific, realistic, and encouraging. Show a clear path forward.
Format with clear sections and bullet points.
Length: 400-500 words.

Generate ONLY the recovery plan."""

            headers = self._get_headers()
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Error generating recovery plan: {e}")
            raise
    
    def generate_guidance_notes(self, escalation: Dict, student_profile: Dict, policy_context: str = "") -> str:
        """Generate personalized guidance notes based on SUNY policies"""
        try:
            prompt = f"""You are an academic advisor at SUNY. Create personalized guidance notes for this student.

STUDENT INFORMATION:
- Name: {student_profile.get('name', 'Student')}
- Major: {student_profile.get('major', 'Undeclared')}
- Academic Standing: GPA {student_profile.get('gpa', 'N/A')}, Risk Level: {student_profile.get('risk_level', 'low')}

STUDENT'S SITUATION:
- Question/Concern: {escalation.get('question', '')}
- AI Response Provided: {escalation.get('ai_response', '')}
- Why Escalated: {escalation.get('escalation_reason', '')}

RELEVANT POLICIES:
{policy_context if policy_context else 'Standard SUNY academic policies apply'}

TASK:
Create detailed guidance notes that an advisor can reference. Include:

1. **Situation Overview**: Summary of student's concern
2. **Relevant Policies & Requirements**:
   - Specific SUNY policies that apply
   - Important deadlines
   - Prerequisite requirements
3. **Recommended Approach**:
   - Step-by-step guidance
   - What options the student has
4. **Key Points to Emphasize**:
   - Critical information student must understand
5. **Potential Challenges**:
   - Issues to watch for
   - Common misunderstandings
6. **Follow-up Items**:
   - What to monitor
   - When to check in again

Be specific, policy-focused, and practical.
Format with clear sections and bullet points.
Length: 300-400 words.

Generate ONLY the guidance notes."""

            headers = self._get_headers()
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Error generating guidance notes: {e}")
            raise