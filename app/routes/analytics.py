from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
import redis.asyncio as redis

from app.dependencies import get_database, get_redis
from app.services.analytics_service import AnalyticsService
from app.models.analytics import CoursePerformanceResponse, StudentLearningPatternResponse, PlatformOverviewResponse

router = APIRouter()

# Get course performance (cached 15min)
@router.get("/courses/{course_id}/performance", response_model=CoursePerformanceResponse)
async def course_performance(course_id: str, db: Database = Depends(get_database), redis_client: redis.Redis = Depends(get_redis)):
    service = AnalyticsService(db, redis_client)
    return await service.course_performance(course_id)

# Get student learning patterns (cached 30min)
@router.get("/students/{student_id}/learning-patterns", response_model=StudentLearningPatternResponse)
async def learning_patterns(student_id: str, db: Database = Depends(get_database), redis_client: redis.Redis = Depends(get_redis)):
    service = AnalyticsService(db, redis_client)
    return await service.student_learning_patterns(student_id)

# Platform overview (admin only, cached 1 hour)
@router.get("/platform/overview", response_model=PlatformOverviewResponse)
async def platform_overview(db: Database = Depends(get_database), redis_client: redis.Redis = Depends(get_redis)):
    # Add admin check here if you implement JWT roles
    service = AnalyticsService(db, redis_client)
    return await service.platform_overview()
