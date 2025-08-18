from fastapi import APIRouter, Depends
from pymongo.database import Database
import redis
from app.dependencies import get_database, get_redis
from app.services.analytics_service import AnalyticsService
from app.models.analytics import CoursePerformanceResponse, StudentLearningPatternResponse, PlatformOverviewResponse

router = APIRouter()

@router.get("/courses/{course_id}/performance", response_model=CoursePerformanceResponse)
async def course_performance(course_id: str, db: Database = Depends(get_database), redis_client: redis.Redis = Depends(get_redis)):
    service = AnalyticsService(db, redis_client)
    return await service.course_performance(course_id)

@router.get("/students/{student_id}/learning-patterns", response_model=StudentLearningPatternResponse)
async def learning_patterns(student_id: str, db: Database = Depends(get_database), redis_client: redis.Redis = Depends(get_redis)):
    service = AnalyticsService(db, redis_client)
    return await service.student_learning_patterns(student_id)

@router.get("/platform/overview", response_model=PlatformOverviewResponse)
async def platform_overview(db: Database = Depends(get_database), redis_client: redis.Redis = Depends(get_redis)):
    service = AnalyticsService(db, redis_client)
    return await service.platform_overview()
