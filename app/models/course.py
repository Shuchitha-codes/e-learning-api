from pydantic import BaseModel, HttpUrl
from typing import List, Optional

# ----------------- Quiz & Questions -----------------
class Question(BaseModel):
    question: str
    options: List[str]
    answer: str

class Quiz(BaseModel):
    id: str
    title: str
    questions: List[Question]

# ----------------- Lesson -----------------
class Lesson(BaseModel):
    id: str
    title: str
    content: str
    video_url: Optional[HttpUrl] = None
    file_url: Optional[str] = None  # <-- New field for uploaded files
    quizzes: Optional[List[Quiz]] = []

# ----------------- Module -----------------
class Module(BaseModel):
    id: str
    title: str
    lessons: List[Lesson]

# ----------------- Course -----------------
class CourseBase(BaseModel):
    title: str
    description: str
    category: str
    tags: Optional[List[str]] = []
    modules: List[Module]
    instructor_id: str

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    modules: Optional[List[str]] = None
    instructor_id: Optional[str] = None

class CourseOut(CourseBase):
    id: str
