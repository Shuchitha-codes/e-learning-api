from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class CoursePerformanceResponse(BaseModel):
    course_id: str
    avg_score: float
    last_cached: datetime

class StudentLearningPatternResponse(BaseModel):
    student_id: str
    lessons_completed: int
    avg_quiz_score: float
    engagement_level: str
    last_cached: datetime

class PlatformOverviewResponse(BaseModel):
    total_students: int
    total_courses: int
    avg_completion_rate: float
    most_popular_courses: List[Dict]
    last_cached: datetime
