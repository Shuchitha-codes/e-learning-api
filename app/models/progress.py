# app/models/progress.py


from pydantic import BaseModel
from typing import List, Optional

class LessonProgress(BaseModel):
    lesson_id: str
    completed: bool = False
    time_spent_seconds: int = 0
    quiz_scores: Optional[List[int]] = []

class CourseProgress(BaseModel):
    course_id: str
    lessons: List[LessonProgress] = []
    completion_percentage: float = 0.0
