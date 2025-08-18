from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder
from typing import List
import shutil, os

from bson import ObjectId
from app.dependencies import get_database
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
@router.get("/", response_model=List[CourseOut], summary="Get All Courses")
async def get_courses(db=Depends(get_database)):
    courses = []
    async for course in db["courses"].find():
        courses.append(CourseOut(id=str(course["_id"]), **course))
    return courses


# ------------------- Get Course by ID -------------------
@router.get("/{course_id}", response_model=CourseOut, summary="Get Course by ID")
async def get_course(course_id: str, db=Depends(get_database)):
    try:
        oid = ObjectId(course_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid course ID")

    course = await db["courses"].find_one({"_id": oid})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseOut(id=str(course["_id"]), **course)


# ------------------- Update Course -------------------
@router.put("/{course_id}", response_model=CourseOut, summary="Update Course (JSON only)")
async def update_course(
    course_id: str,
    course_data: CourseUpdate,  # JSON body for updates
    db=Depends(get_database)
):
    try:
        oid = ObjectId(course_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid course ID")

    try:
        update_dict = jsonable_encoder(course_data, exclude_unset=True)
        result = await db["courses"].update_one({"_id": oid}, {"$set": update_dict})

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Course not found or no changes made")

        updated = await db["courses"].find_one({"_id": oid})
        return CourseOut(id=str(updated["_id"]), **updated)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
