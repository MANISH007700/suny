# routers/admin.py
"""
Administrator Analytics Dashboard Router
Provides comprehensive analytics for system usage, student behavior, and quality monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import logging
import random

logger = logging.getLogger(__name__)
router = APIRouter()

# Storage paths
ESCALATIONS_FILE = "./backend/data/escalations.json"
STUDENTS_FILE = "./backend/data/student_profiles.json"
ANALYTICS_DATA_FILE = "./backend/data/analytics_data.json"

# === Helper Functions ===

def load_json_file(filepath: str, default=None):
    """Load JSON file with error handling"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return default if default is not None else {}
    return default if default is not None else {}

def save_json_file(filepath: str, data):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def initialize_analytics_data():
    """Initialize or load analytics data with mock historical data"""
    analytics_data = load_json_file(ANALYTICS_DATA_FILE, default=None)
    
    if analytics_data is None or not analytics_data.get("question_logs"):
        # Generate mock historical data for past 30 days
        analytics_data = generate_mock_analytics_data()
        save_json_file(ANALYTICS_DATA_FILE, analytics_data)
    
    return analytics_data

def generate_mock_analytics_data():
    """Generate realistic mock analytics data for demonstrations"""
    
    # Topics and their relative frequencies
    topics = {
        "Course Requirements": 120,
        "Registration & Enrollment": 95,
        "Prerequisites": 85,
        "Graduation Requirements": 75,
        "Financial Aid": 60,
        "Transfer Credits": 45,
        "Academic Standing": 40,
        "Major/Minor Planning": 65,
        "Course Scheduling": 80,
        "Academic Policies": 55,
        "Tutoring Services": 30,
        "Study Abroad": 25,
        "Internships": 35,
        "Career Planning": 28
    }
    
    # Student IDs pool
    student_ids = [f"STUDENT_{str(i).zfill(3)}" for i in range(1, 51)]
    
    # Generate question logs for past 30 days
    question_logs = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    total_questions = 0
    for topic, base_count in topics.items():
        # Add some randomness to counts
        count = base_count + random.randint(-10, 10)
        total_questions += count
        
        for _ in range(count):
            # Random timestamp in past 30 days
            days_ago = random.randint(0, 30)
            hours = random.randint(8, 22)  # Peak hours 8am-10pm
            minutes = random.randint(0, 59)
            
            timestamp = end_date - timedelta(days=days_ago, hours=(24-hours), minutes=(60-minutes))
            
            # Random student
            student_id = random.choice(student_ids)
            
            # Generate question log
            question_logs.append({
                "id": f"q-{len(question_logs)+1}",
                "student_id": student_id,
                "topic": topic,
                "timestamp": timestamp.isoformat(),
                "response_time_seconds": round(random.uniform(2.5, 15.0), 2),
                "satisfaction_rating": random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0],
                "escalated": random.random() < 0.08,  # 8% escalation rate
                "flagged_incorrect": random.random() < 0.05,  # 5% flagged as incorrect
                "conversation_length": random.randint(1, 8),  # Number of exchanges
                "hour_of_day": hours,
                "day_of_week": timestamp.strftime("%A")
            })
    
    # Generate feedback data
    feedback_logs = []
    common_issues = [
        "AI couldn't find relevant information",
        "Answer was too generic",
        "Needed more specific policy details",
        "Information was outdated",
        "Question required human judgment",
        "Response lacked clarity",
        "Missing context about special circumstances"
    ]
    
    for log in question_logs:
        if log["flagged_incorrect"]:
            feedback_logs.append({
                "question_id": log["id"],
                "student_id": log["student_id"],
                "topic": log["topic"],
                "issue": random.choice(common_issues),
                "timestamp": log["timestamp"]
            })
    
    return {
        "question_logs": question_logs,
        "feedback_logs": feedback_logs,
        "last_updated": datetime.now().isoformat(),
        "total_questions": total_questions
    }

# === API Endpoints ===

@router.get("/health")
async def health():
    """Health check for admin endpoints"""
    return {"status": "healthy", "service": "admin_analytics"}

@router.get("/analytics/overview")
async def get_analytics_overview():
    """
    Get high-level overview metrics for the administrator dashboard
    """
    try:
        analytics_data = initialize_analytics_data()
        escalations = load_json_file(ESCALATIONS_FILE, default=[])
        students = load_json_file(STUDENTS_FILE, default={})
        
        question_logs = analytics_data.get("question_logs", [])
        
        # Calculate key metrics
        total_questions = len(question_logs)
        total_students = len(students)
        total_escalations = len(escalations)
        
        # Active users (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        active_users_week = len(set(
            log["student_id"] for log in question_logs 
            if log["timestamp"] > week_ago
        ))
        
        # Active users (last 30 days)
        month_ago = (datetime.now() - timedelta(days=30)).isoformat()
        active_users_month = len(set(
            log["student_id"] for log in question_logs 
            if log["timestamp"] > month_ago
        ))
        
        # Escalation rate
        escalated_count = sum(1 for log in question_logs if log.get("escalated", False))
        escalation_rate = (escalated_count / total_questions * 100) if total_questions > 0 else 0
        
        # Average satisfaction
        ratings = [log["satisfaction_rating"] for log in question_logs if "satisfaction_rating" in log]
        avg_satisfaction = sum(ratings) / len(ratings) if ratings else 0
        
        # Flagged responses
        flagged_count = sum(1 for log in question_logs if log.get("flagged_incorrect", False))
        accuracy_rate = ((total_questions - flagged_count) / total_questions * 100) if total_questions > 0 else 100
        
        # Risk students
        high_risk_count = sum(1 for s in students.values() if s.get("risk_level") in ["high", "critical"])
        
        return {
            "total_questions": total_questions,
            "total_students": total_students,
            "total_escalations": total_escalations,
            "active_users_week": active_users_week,
            "active_users_month": active_users_month,
            "escalation_rate": round(escalation_rate, 2),
            "avg_satisfaction": round(avg_satisfaction, 2),
            "accuracy_rate": round(accuracy_rate, 2),
            "flagged_responses": flagged_count,
            "high_risk_students": high_risk_count
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/usage-trends")
async def get_usage_trends(days: int = 30):
    """
    Get usage trends over time (questions per day, active users per day)
    """
    try:
        analytics_data = initialize_analytics_data()
        question_logs = analytics_data.get("question_logs", [])
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Group questions by date
        daily_questions = defaultdict(int)
        daily_users = defaultdict(set)
        
        for log in question_logs:
            log_date = datetime.fromisoformat(log["timestamp"]).date()
            if log_date >= start_date.date():
                date_str = log_date.isoformat()
                daily_questions[date_str] += 1
                daily_users[date_str].add(log["student_id"])
        
        # Fill in missing dates with 0
        current_date = start_date.date()
        trends = []
        while current_date <= end_date.date():
            date_str = current_date.isoformat()
            trends.append({
                "date": date_str,
                "questions": daily_questions.get(date_str, 0),
                "active_users": len(daily_users.get(date_str, set()))
            })
            current_date += timedelta(days=1)
        
        return {
            "period_days": days,
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Error getting usage trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/peak-hours")
async def get_peak_hours():
    """
    Get peak usage hours (heatmap data)
    """
    try:
        analytics_data = initialize_analytics_data()
        question_logs = analytics_data.get("question_logs", [])
        
        # Group by day of week and hour
        usage_matrix = defaultdict(lambda: defaultdict(int))
        
        for log in question_logs:
            day = log.get("day_of_week", "Unknown")
            hour = log.get("hour_of_day", 12)
            usage_matrix[day][hour] += 1
        
        # Format for heatmap
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heatmap_data = []
        
        for day in days_order:
            for hour in range(24):
                heatmap_data.append({
                    "day": day,
                    "hour": hour,
                    "count": usage_matrix[day].get(hour, 0)
                })
        
        return {
            "heatmap_data": heatmap_data,
            "days_order": days_order,
            "hours_range": list(range(24))
        }
        
    except Exception as e:
        logger.error(f"Error getting peak hours: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/top-topics")
async def get_top_topics(limit: int = 10):
    """
    Get most frequently asked topics
    """
    try:
        analytics_data = initialize_analytics_data()
        question_logs = analytics_data.get("question_logs", [])
        
        # Count topics
        topic_counter = Counter(log["topic"] for log in question_logs)
        
        # Get top topics
        top_topics = [
            {"topic": topic, "count": count, "percentage": round(count / len(question_logs) * 100, 2)}
            for topic, count in topic_counter.most_common(limit)
        ]
        
        return {
            "top_topics": top_topics,
            "total_questions": len(question_logs)
        }
        
    except Exception as e:
        logger.error(f"Error getting top topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/satisfaction-trends")
async def get_satisfaction_trends():
    """
    Get satisfaction rating distribution and trends
    """
    try:
        analytics_data = initialize_analytics_data()
        question_logs = analytics_data.get("question_logs", [])
        
        # Rating distribution
        rating_counter = Counter(log["satisfaction_rating"] for log in question_logs if "satisfaction_rating" in log)
        
        rating_distribution = [
            {"rating": i, "count": rating_counter.get(i, 0)}
            for i in range(1, 6)
        ]
        
        # Average satisfaction over time (weekly)
        weekly_satisfaction = defaultdict(list)
        for log in question_logs:
            if "satisfaction_rating" in log:
                log_date = datetime.fromisoformat(log["timestamp"])
                week_start = (log_date - timedelta(days=log_date.weekday())).date().isoformat()
                weekly_satisfaction[week_start].append(log["satisfaction_rating"])
        
        satisfaction_trend = [
            {
                "week": week,
                "avg_rating": round(sum(ratings) / len(ratings), 2),
                "count": len(ratings)
            }
            for week, ratings in sorted(weekly_satisfaction.items())
        ]
        
        return {
            "rating_distribution": rating_distribution,
            "satisfaction_trend": satisfaction_trend,
            "overall_avg": round(sum(log["satisfaction_rating"] for log in question_logs if "satisfaction_rating" in log) / len([log for log in question_logs if "satisfaction_rating" in log]), 2) if question_logs else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting satisfaction trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/escalation-analysis")
async def get_escalation_analysis():
    """
    Get detailed escalation analysis
    """
    try:
        analytics_data = initialize_analytics_data()
        question_logs = analytics_data.get("question_logs", [])
        escalations = load_json_file(ESCALATIONS_FILE, default=[])
        
        # Escalation by topic
        escalated_logs = [log for log in question_logs if log.get("escalated", False)]
        topic_counter = Counter(log["topic"] for log in escalated_logs)
        
        escalation_by_topic = [
            {"topic": topic, "count": count}
            for topic, count in topic_counter.most_common(10)
        ]
        
        # Escalation reasons
        escalation_reasons = Counter(esc.get("escalation_reason", "Unknown") for esc in escalations)
        
        escalation_reasons_list = [
            {"reason": reason, "count": count}
            for reason, count in escalation_reasons.most_common()
        ]
        
        # Escalation rate over time
        weekly_escalations = defaultdict(lambda: {"total": 0, "escalated": 0})
        for log in question_logs:
            log_date = datetime.fromisoformat(log["timestamp"])
            week_start = (log_date - timedelta(days=log_date.weekday())).date().isoformat()
            weekly_escalations[week_start]["total"] += 1
            if log.get("escalated", False):
                weekly_escalations[week_start]["escalated"] += 1
        
        escalation_rate_trend = [
            {
                "week": week,
                "rate": round(data["escalated"] / data["total"] * 100, 2) if data["total"] > 0 else 0,
                "total_questions": data["total"],
                "escalated": data["escalated"]
            }
            for week, data in sorted(weekly_escalations.items())
        ]
        
        return {
            "escalation_by_topic": escalation_by_topic,
            "escalation_reasons": escalation_reasons_list,
            "escalation_rate_trend": escalation_rate_trend,
            "total_escalations": len(escalated_logs)
        }
        
    except Exception as e:
        logger.error(f"Error getting escalation analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/accuracy-monitoring")
async def get_accuracy_monitoring():
    """
    Get accuracy monitoring data (flagged responses, common issues)
    """
    try:
        analytics_data = initialize_analytics_data()
        question_logs = analytics_data.get("question_logs", [])
        feedback_logs = analytics_data.get("feedback_logs", [])
        
        # Flagged responses by topic
        flagged_logs = [log for log in question_logs if log.get("flagged_incorrect", False)]
        topic_counter = Counter(log["topic"] for log in flagged_logs)
        
        flagged_by_topic = [
            {"topic": topic, "count": count}
            for topic, count in topic_counter.most_common(10)
        ]
        
        # Common issues
        issue_counter = Counter(fb["issue"] for fb in feedback_logs)
        common_issues = [
            {"issue": issue, "count": count}
            for issue, count in issue_counter.most_common()
        ]
        
        # Accuracy rate over time
        weekly_accuracy = defaultdict(lambda: {"total": 0, "correct": 0})
        for log in question_logs:
            log_date = datetime.fromisoformat(log["timestamp"])
            week_start = (log_date - timedelta(days=log_date.weekday())).date().isoformat()
            weekly_accuracy[week_start]["total"] += 1
            if not log.get("flagged_incorrect", False):
                weekly_accuracy[week_start]["correct"] += 1
        
        accuracy_trend = [
            {
                "week": week,
                "accuracy": round(data["correct"] / data["total"] * 100, 2) if data["total"] > 0 else 0,
                "total": data["total"]
            }
            for week, data in sorted(weekly_accuracy.items())
        ]
        
        return {
            "flagged_by_topic": flagged_by_topic,
            "common_issues": common_issues,
            "accuracy_trend": accuracy_trend,
            "total_flagged": len(flagged_logs),
            "overall_accuracy": round((len(question_logs) - len(flagged_logs)) / len(question_logs) * 100, 2) if question_logs else 100
        }
        
    except Exception as e:
        logger.error(f"Error getting accuracy monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/student-behavior")
async def get_student_behavior_insights():
    """
    Get student behavior insights (repeat help-seekers, confusion areas, engagement patterns)
    """
    try:
        analytics_data = initialize_analytics_data()
        question_logs = analytics_data.get("question_logs", [])
        students = load_json_file(STUDENTS_FILE, default={})
        
        # Students by question frequency
        student_question_count = Counter(log["student_id"] for log in question_logs)
        
        # Identify repeat help-seekers
        repeat_students = [
            {
                "student_id": student_id,
                "name": students.get(student_id, {}).get("name", "Unknown"),
                "question_count": count,
                "risk_level": students.get(student_id, {}).get("risk_level", "low")
            }
            for student_id, count in student_question_count.most_common(20)
            if count >= 5  # Students with 5+ questions
        ]
        
        # Topics generating long conversations (high friction)
        topic_conversation_lengths = defaultdict(list)
        for log in question_logs:
            topic_conversation_lengths[log["topic"]].append(log["conversation_length"])
        
        high_friction_topics = [
            {
                "topic": topic,
                "avg_conversation_length": round(sum(lengths) / len(lengths), 2),
                "question_count": len(lengths)
            }
            for topic, lengths in topic_conversation_lengths.items()
        ]
        high_friction_topics.sort(key=lambda x: x["avg_conversation_length"], reverse=True)
        
        # Most confused topics (low satisfaction + high conversation length)
        confusion_scores = defaultdict(lambda: {"ratings": [], "conv_lengths": [], "count": 0})
        for log in question_logs:
            topic = log["topic"]
            confusion_scores[topic]["ratings"].append(log.get("satisfaction_rating", 3))
            confusion_scores[topic]["conv_lengths"].append(log["conversation_length"])
            confusion_scores[topic]["count"] += 1
        
        confusion_areas = []
        for topic, data in confusion_scores.items():
            avg_rating = sum(data["ratings"]) / len(data["ratings"])
            avg_conv = sum(data["conv_lengths"]) / len(data["conv_lengths"])
            confusion_score = (5 - avg_rating) * avg_conv  # Higher = more confusion
            
            confusion_areas.append({
                "topic": topic,
                "confusion_score": round(confusion_score, 2),
                "avg_rating": round(avg_rating, 2),
                "avg_conversation_length": round(avg_conv, 2),
                "question_count": data["count"]
            })
        
        confusion_areas.sort(key=lambda x: x["confusion_score"], reverse=True)
        
        return {
            "repeat_help_seekers": repeat_students,
            "high_friction_topics": high_friction_topics[:10],
            "confusion_areas": confusion_areas[:10],
            "total_unique_students": len(student_question_count)
        }
        
    except Exception as e:
        logger.error(f"Error getting student behavior insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/risk-identification")
async def get_risk_identification():
    """
    Get at-risk student identification and patterns
    """
    try:
        students = load_json_file(STUDENTS_FILE, default={})
        analytics_data = initialize_analytics_data()
        question_logs = analytics_data.get("question_logs", [])
        escalations = load_json_file(ESCALATIONS_FILE, default=[])
        
        # Risk level distribution
        risk_distribution = Counter(s.get("risk_level", "low") for s in students.values())
        
        risk_levels = [
            {"level": level, "count": risk_distribution.get(level, 0)}
            for level in ["low", "medium", "high", "critical"]
        ]
        
        # At-risk students with details
        at_risk_students = []
        for student_id, profile in students.items():
            risk_level = profile.get("risk_level", "low")
            if risk_level in ["high", "critical"]:
                # Get student's question topics
                student_questions = [log for log in question_logs if log["student_id"] == student_id]
                topics = Counter(log["topic"] for log in student_questions)
                
                at_risk_students.append({
                    "student_id": student_id,
                    "name": profile.get("name", "Unknown"),
                    "risk_level": risk_level,
                    "gpa": profile.get("gpa"),
                    "major": profile.get("major", "Undeclared"),
                    "total_escalations": profile.get("total_escalations", 0),
                    "total_questions": len(student_questions),
                    "top_concern": topics.most_common(1)[0][0] if topics else "None",
                    "last_interaction": profile.get("last_interaction", "")[:10]
                })
        
        at_risk_students.sort(key=lambda x: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x["risk_level"], 0),
            -x["total_escalations"]
        ), reverse=True)
        
        # Patterns by major
        major_risk_patterns = defaultdict(lambda: {"low": 0, "medium": 0, "high": 0, "critical": 0, "total": 0})
        for profile in students.values():
            major = profile.get("major", "Undeclared")
            risk = profile.get("risk_level", "low")
            major_risk_patterns[major][risk] += 1
            major_risk_patterns[major]["total"] += 1
        
        major_patterns = [
            {
                "major": major,
                "risk_breakdown": {
                    "low": data["low"],
                    "medium": data["medium"],
                    "high": data["high"],
                    "critical": data["critical"]
                },
                "total_students": data["total"],
                "risk_percentage": round((data["high"] + data["critical"]) / data["total"] * 100, 2) if data["total"] > 0 else 0
            }
            for major, data in major_risk_patterns.items()
        ]
        major_patterns.sort(key=lambda x: x["risk_percentage"], reverse=True)
        
        # Completion patterns (mock data based on risk level)
        completion_patterns = {
            "on_track": len([s for s in students.values() if s.get("risk_level") == "low"]),
            "at_risk": len([s for s in students.values() if s.get("risk_level") in ["medium", "high"]]),
            "critical": len([s for s in students.values() if s.get("risk_level") == "critical"])
        }
        
        return {
            "risk_distribution": risk_levels,
            "at_risk_students": at_risk_students,
            "major_risk_patterns": major_patterns,
            "completion_patterns": completion_patterns,
            "total_at_risk": len(at_risk_students)
        }
        
    except Exception as e:
        logger.error(f"Error getting risk identification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/response-time")
async def get_response_time_analysis():
    """
    Get response time analysis
    """
    try:
        analytics_data = initialize_analytics_data()
        question_logs = analytics_data.get("question_logs", [])
        
        # Calculate average response time by topic
        topic_response_times = defaultdict(list)
        for log in question_logs:
            topic_response_times[log["topic"]].append(log.get("response_time_seconds", 0))
        
        avg_by_topic = [
            {
                "topic": topic,
                "avg_response_time": round(sum(times) / len(times), 2),
                "count": len(times)
            }
            for topic, times in topic_response_times.items()
        ]
        avg_by_topic.sort(key=lambda x: x["avg_response_time"], reverse=True)
        
        # Overall stats
        all_times = [log.get("response_time_seconds", 0) for log in question_logs]
        
        return {
            "avg_response_time_overall": round(sum(all_times) / len(all_times), 2) if all_times else 0,
            "min_response_time": round(min(all_times), 2) if all_times else 0,
            "max_response_time": round(max(all_times), 2) if all_times else 0,
            "avg_by_topic": avg_by_topic
        }
        
    except Exception as e:
        logger.error(f"Error getting response time analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/regenerate-data")
async def regenerate_analytics_data():
    """
    Regenerate mock analytics data (for testing/demo purposes)
    """
    try:
        analytics_data = generate_mock_analytics_data()
        save_json_file(ANALYTICS_DATA_FILE, analytics_data)
        
        return {
            "status": "success",
            "message": "Analytics data regenerated successfully",
            "total_questions": len(analytics_data["question_logs"])
        }
    except Exception as e:
        logger.error(f"Error regenerating analytics data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

