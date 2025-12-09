"""
Course Comparison Module
Provides intelligent comparison of courses with LLM-generated insights
"""

import logging
from typing import List, Dict, Any
import os
import requests

logger = logging.getLogger(__name__)


class CourseComparator:
    """Compare courses and generate insights"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.5-flash"
    
    def compare_courses(self, courses: List[Dict], comparison_criteria: List[str] = None) -> Dict[str, Any]:
        """
        Compare multiple courses and generate insights
        
        Args:
            courses: List of course objects with metadata
            comparison_criteria: Optional list of specific criteria to compare
        
        Returns:
            Dict with comparison table, insights, and recommendations
        """
        try:
            if not courses or len(courses) < 2:
                return {
                    "error": "Need at least 2 courses to compare",
                    "comparison_table": None,
                    "insights": None,
                    "recommendation": None
                }
            
            # Generate structured comparison
            table = self._generate_comparison_table(courses)
            
            # Generate AI insights
            insights = self._generate_insights(courses, comparison_criteria)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(courses)
            
            return {
                "comparison_table": table,
                "insights": insights,
                "recommendation": recommendation,
                "course_count": len(courses)
            }
            
        except Exception as e:
            logger.error(f"Error comparing courses: {e}")
            return {
                "error": str(e),
                "comparison_table": None,
                "insights": None,
                "recommendation": None
            }
    
    def _generate_comparison_table(self, courses: List[Dict]) -> Dict[str, Any]:
        """Generate structured comparison table"""
        table = {
            "headers": ["Field"] + [f"Course {i+1}" for i in range(len(courses))],
            "rows": []
        }
        
        # Define comparison fields
        fields = [
            ("title", "Course Title"),
            ("code", "Course Code"),
            ("institution", "Institution"),
            ("subject_area", "Subject Area"),
            ("credits", "Credits"),
            ("delivery_mode", "Delivery Mode"),
            ("start_date", "Start Date"),
            ("instructor", "Instructor"),
            ("url", "Registration URL")
        ]
        
        for field_key, field_label in fields:
            row = {"field": field_label, "values": []}
            
            for course in courses:
                metadata = course.get("metadata", {})
                value = metadata.get(field_key, "N/A")
                row["values"].append(value)
            
            table["rows"].append(row)
        
        # Add description row
        desc_row = {"field": "Description", "values": []}
        for course in courses:
            desc = course.get("text", "No description available")
            # Truncate to first 200 chars
            desc_row["values"].append(desc[:200] + "..." if len(desc) > 200 else desc)
        table["rows"].append(desc_row)
        
        return table
    
    def _generate_insights(self, courses: List[Dict], criteria: List[str] = None) -> str:
        """Generate AI-powered insights about course differences"""
        try:
            # Build course summaries
            course_summaries = []
            for i, course in enumerate(courses, 1):
                metadata = course.get("metadata", {})
                summary = f"""
Course {i}:
- Title: {metadata.get('title', 'Unknown')}
- Institution: {metadata.get('institution', 'Unknown')}
- Code: {metadata.get('code', 'N/A')}
- Credits: {metadata.get('credits', 'N/A')}
- Delivery: {metadata.get('delivery_mode', 'N/A')}
- Instructor: {metadata.get('instructor', 'TBA')}
- Description: {course.get('text', 'N/A')[:300]}
"""
                course_summaries.append(summary)
            
            prompt = f"""You are an academic advisor comparing courses for a student. Analyze these courses and provide insights.

COURSES TO COMPARE:
{chr(10).join(course_summaries)}

COMPARISON CRITERIA:
{', '.join(criteria) if criteria else 'General comparison'}

Provide a detailed comparison analysis covering:
1. **Key Differences**: What makes each course unique?
2. **Difficulty Level**: Which might be more challenging?
3. **Prerequisites**: Any mentioned prerequisites or assumed knowledge?
4. **Best For**: What type of student would benefit most from each?
5. **Workload**: Expected time commitment if mentioned
6. **Career Relevance**: How each relates to career paths

Format your response with clear sections and bullet points.
Keep it concise but insightful (300-400 words).
"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=20)
            
            if response.status_code == 429:
                return "AI comparison temporarily unavailable due to rate limiting. Please try again in a moment."
            
            response.raise_for_status()
            
            data = response.json()
            insights = data['choices'][0]['message']['content'].strip()
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return "Unable to generate AI insights at this time."
    
    def _generate_recommendation(self, courses: List[Dict]) -> str:
        """Generate personalized recommendation"""
        try:
            # Build compact course info
            course_info = []
            for i, course in enumerate(courses, 1):
                metadata = course.get("metadata", {})
                info = f"Course {i}: {metadata.get('title', 'Unknown')} at {metadata.get('institution', 'Unknown')}"
                course_info.append(info)
            
            prompt = f"""You are an academic advisor. Based on these courses, give a brief recommendation (2-3 sentences) about which might be best for different student goals.

COURSES:
{chr(10).join(course_info)}

Provide a quick recommendation considering factors like:
- Institution reputation
- Course delivery mode
- Credits offered
- Instructor presence

Be concise and practical."""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.3
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 429:
                return "Recommendation temporarily unavailable."
            
            response.raise_for_status()
            
            data = response.json()
            recommendation = data['choices'][0]['message']['content'].strip()
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "Unable to generate recommendation at this time."
    
    def compare_universities(self, courses: List[Dict]) -> Dict[str, Any]:
        """Compare courses grouped by university"""
        try:
            # Group courses by institution
            by_institution = {}
            for course in courses:
                institution = course.get("metadata", {}).get("institution", "Unknown")
                if institution not in by_institution:
                    by_institution[institution] = []
                by_institution[institution].append(course)
            
            # Generate comparison
            comparison = {
                "institutions": list(by_institution.keys()),
                "course_counts": {inst: len(courses) for inst, courses in by_institution.items()},
                "summary": self._generate_university_comparison(by_institution)
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing universities: {e}")
            return {"error": str(e)}
    
    def _generate_university_comparison(self, by_institution: Dict[str, List[Dict]]) -> str:
        """Generate comparison summary for universities"""
        try:
            summary_parts = []
            
            for institution, courses in by_institution.items():
                # Count delivery modes
                modes = {}
                for course in courses:
                    mode = course.get("metadata", {}).get("delivery_mode", "Unknown")
                    modes[mode] = modes.get(mode, 0) + 1
                
                summary = f"**{institution}**: {len(courses)} courses available"
                if modes:
                    mode_str = ", ".join([f"{count} {mode}" for mode, count in modes.items()])
                    summary += f" ({mode_str})"
                
                summary_parts.append(summary)
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating university comparison: {e}")
            return "Unable to generate comparison summary."

