"""
File Generation Service
Generates downloadable files in various formats (CSV, JSON, TXT)
"""

import json
import csv
import io
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FileGenerator:
    """Generate files in various formats from data"""
    
    @staticmethod
    def generate_csv(data: List[Dict], filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate CSV file from list of dictionaries
        
        Args:
            data: List of dictionaries with consistent keys
            filename: Optional filename
        
        Returns:
            Dict with file content, filename, and mime type
        """
        try:
            if not data:
                return {
                    "content": "",
                    "filename": filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "mime_type": "text/csv",
                    "size": 0
                }
            
            # Create CSV in memory
            output = io.StringIO()
            
            # Get all unique keys from all dictionaries
            all_keys = set()
            for item in data:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            fieldnames = sorted(list(all_keys))
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                # Flatten nested structures
                flat_item = FileGenerator._flatten_dict(item)
                writer.writerow(flat_item)
            
            content = output.getvalue()
            
            return {
                "content": content,
                "filename": filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "mime_type": "text/csv",
                "size": len(content),
                "row_count": len(data)
            }
            
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            raise
    
    @staticmethod
    def generate_json(data: Any, filename: Optional[str] = None, pretty: bool = True) -> Dict[str, Any]:
        """
        Generate JSON file from any data structure
        
        Args:
            data: Any JSON-serializable data
            filename: Optional filename
            pretty: Whether to format with indentation
        
        Returns:
            Dict with file content, filename, and mime type
        """
        try:
            if pretty:
                content = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                content = json.dumps(data, ensure_ascii=False)
            
            return {
                "content": content,
                "filename": filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "mime_type": "application/json",
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            raise
    
    @staticmethod
    def generate_text(data: Any, filename: Optional[str] = None, format_type: str = "readable") -> Dict[str, Any]:
        """
        Generate text file from data
        
        Args:
            data: Data to convert to text
            filename: Optional filename
            format_type: "readable" or "raw"
        
        Returns:
            Dict with file content, filename, and mime type
        """
        try:
            if format_type == "readable":
                content = FileGenerator._format_readable(data)
            else:
                content = str(data)
            
            return {
                "content": content,
                "filename": filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "mime_type": "text/plain",
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"Error generating text file: {e}")
            raise
    
    @staticmethod
    def generate_course_csv(courses: List[Dict]) -> Dict[str, Any]:
        """Generate CSV specifically formatted for course data"""
        try:
            formatted_courses = []
            
            for course in courses:
                metadata = course.get("metadata", {})
                formatted_course = {
                    "Course Title": metadata.get("title", ""),
                    "Course Code": metadata.get("code", ""),
                    "Institution": metadata.get("institution", ""),
                    "Subject Area": metadata.get("subject_area", ""),
                    "Credits": metadata.get("credits", ""),
                    "Delivery Mode": metadata.get("delivery_mode", ""),
                    "Start Date": metadata.get("start_date", ""),
                    "Instructor": metadata.get("instructor", ""),
                    "URL": metadata.get("url", ""),
                    "Description": course.get("text", "")[:200]  # Truncate description
                }
                formatted_courses.append(formatted_course)
            
            return FileGenerator.generate_csv(
                formatted_courses, 
                filename=f"courses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
        except Exception as e:
            logger.error(f"Error generating course CSV: {e}")
            raise
    
    @staticmethod
    def generate_escalation_csv(escalations: List[Dict]) -> Dict[str, Any]:
        """Generate CSV specifically formatted for escalation data"""
        try:
            formatted_escalations = []
            
            for esc in escalations:
                formatted_esc = {
                    "Escalation ID": esc.get("id", ""),
                    "Student ID": esc.get("student_id", ""),
                    "Question": esc.get("question", "")[:200],
                    "Status": esc.get("status", ""),
                    "Priority": "⭐" * esc.get("priority", 1),
                    "Reason": esc.get("escalation_reason", ""),
                    "Created At": esc.get("created_at", ""),
                    "Assigned To": esc.get("assigned_to", "None"),
                    "Notes Count": len(esc.get("advisor_notes", []))
                }
                formatted_escalations.append(formatted_esc)
            
            return FileGenerator.generate_csv(
                formatted_escalations,
                filename=f"escalations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
        except Exception as e:
            logger.error(f"Error generating escalation CSV: {e}")
            raise
    
    @staticmethod
    def generate_comparison_table(courses: List[Dict]) -> str:
        """
        Generate a formatted comparison table for courses
        
        Returns:
            HTML table string
        """
        try:
            if not courses:
                return "<p>No courses to compare</p>"
            
            # Extract relevant fields for comparison
            comparison_fields = [
                ("title", "Course Title"),
                ("code", "Course Code"),
                ("institution", "Institution"),
                ("credits", "Credits"),
                ("subject_area", "Subject"),
                ("delivery_mode", "Delivery"),
                ("start_date", "Start Date"),
                ("instructor", "Instructor"),
                ("url", "URL")
            ]
            
            # Build HTML table
            html = '<table class="comparison-table" style="width:100%; border-collapse: collapse;">\n'
            html += '  <thead>\n'
            html += '    <tr style="background-color: #f0f0f0;">\n'
            html += '      <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Field</th>\n'
            
            for i, course in enumerate(courses[:4], 1):  # Limit to 4 courses
                html += f'      <th style="border: 1px solid #ddd; padding: 8px;">Course {i}</th>\n'
            
            html += '    </tr>\n'
            html += '  </thead>\n'
            html += '  <tbody>\n'
            
            for field_key, field_label in comparison_fields:
                html += '    <tr>\n'
                html += f'      <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">{field_label}</td>\n'
                
                for course in courses[:4]:
                    metadata = course.get("metadata", {})
                    value = metadata.get(field_key, "N/A")
                    
                    # Handle URL specially
                    if field_key == "url" and value != "N/A":
                        value = f'<a href="{value}" target="_blank">Course Link</a>'
                    
                    html += f'      <td style="border: 1px solid #ddd; padding: 8px;">{value}</td>\n'
                
                html += '    </tr>\n'
            
            html += '  </tbody>\n'
            html += '</table>'
            
            return html
            
        except Exception as e:
            logger.error(f"Error generating comparison table: {e}")
            return f"<p>Error generating comparison: {str(e)}</p>"
    
    @staticmethod
    def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(FileGenerator._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to string
                items.append((new_key, ', '.join(map(str, v))))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    @staticmethod
    def _format_readable(data: Any) -> str:
        """Format data in human-readable text format"""
        if isinstance(data, list):
            output = []
            for i, item in enumerate(data, 1):
                output.append(f"=== Item {i} ===")
                output.append(FileGenerator._format_readable(item))
                output.append("")
            return "\n".join(output)
        
        elif isinstance(data, dict):
            output = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    output.append(f"{key}:")
                    output.append(FileGenerator._format_readable(value))
                else:
                    output.append(f"{key}: {value}")
            return "\n".join(output)
        
        else:
            return str(data)

