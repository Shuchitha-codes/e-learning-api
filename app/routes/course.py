from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder
from typing import List
import shutil, os

from bson import ObjectId
from app.dependencies import get_database
from app.db import db
from app.models.course import CourseCreate, CourseUpdate, CourseOut

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------- Create Course -------------------
@router.post("/", response_model=CourseOut, summary="Create Course (JSON only)")
async def create_course(
    course_data: CourseCreate,  # JSON body
    db=Depends(get_database)
):
    try:
        course_dict = jsonable_encoder(course_data)
        result = await db["courses"].insert_one(course_dict)
        return CourseOut(id=str(result.inserted_id), **course_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------- Get All Courses -------------------
def _normalize_course(doc: dict) -> dict:
    """
    Coerce a Mongo course document into the shape CourseOut expects.
    Fills missing fields with safe defaults so Pydantic validation succeeds.
    """
    if not doc:
        return doc
    c = dict(doc)
    c["id"] = str(c.pop("_id"))  # map Mongo _id -> id

    # defaults
    c.setdefault("tags", [])
    modules = []
    for m in c.get("modules", []):
        m = dict(m)
        m.setdefault("title", "Untitled Module")   # <-- fill missing title
        m.setdefault("lessons", [])
        lessons = []
        for l in m["lessons"]:
            l = dict(l)
            l.setdefault("quizzes", [])           # ensure quizzes list exists
            lessons.append(l)
        m["lessons"] = lessons
        modules.append(m)
    c["modules"] = modules
    return c

# ------------------- Get All Courses -------------------
@router.get("/", response_model=List[CourseOut], summary="Get All Courses")
async def get_courses(db=Depends(get_database)):
    items: List[CourseOut] = []
    async for course in db["courses"].find():
        normalized = _normalize_course(course)
        items.append(CourseOut(**normalized))
    return items

# ------------------- Get Course by ID -------------------
@router.get("/{course_id}", response_model=CourseOut, summary="Get Course by ID")
async def get_course(course_id: str, db=Depends(get_database)):
    try:
        oid = ObjectId(course_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid course ID")

    course = await db["courses"].find_one({"_id": oid})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    normalized = _normalize_course(course)
    return CourseOut(**normalized)


# ------------------- Update Course -------------------
courses_collection = db["courses"]

@router.put("/courses/{course_id}")
async def update_course(course_id: str, course: CourseUpdate):
    # Convert ObjectId
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="Invalid course ID")

    # Only update provided fields
    update_data = {k: v for k, v in course.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    result = await courses_collection.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")

    return {"message": "Course updated successfully", "updated_fields": update_data}


# ------------------- Delete Course -------------------
@router.delete("/{course_id}", summary="Delete Course")
async def delete_course(course_id: str, db=Depends(get_database)):
    try:
        oid = ObjectId(course_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid course ID")

    result = await db["courses"].delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted successfully"}


# ------------------- Upload File to a Specific Lesson -------------------
@router.post(
    "/{course_id}/modules/{module_id}/lessons/{lesson_id}/upload",
    summary="Upload file for a specific lesson",
)
async def upload_lesson_file(
    course_id: str,
    module_id: str,
    lesson_id: str,
    file: UploadFile = File(...),
    db=Depends(get_database),
):
    try:
        oid = ObjectId(course_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid course ID")

    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = path

    result = await db["courses"].update_one(
        {"_id": oid, "modules.id": module_id, "modules.lessons.id": lesson_id},
        {"$set": {"modules.$[mod].lessons.$[les].file_url": file_url}},
        array_filters=[{"mod.id": module_id}, {"les.id": lesson_id}]
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Course/module/lesson not found")

    return {"message": "File uploaded successfully", "file_url": file_url}
