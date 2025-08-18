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
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    modules: Optional[List[Module]]
    instructor_id: Optional[str]

class CourseOut(CourseBase):
    id: str
