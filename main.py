
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import auth  # make sure path is correct

app = FastAPI(title="E-Learning API")

# include auth router
app.include_router(auth.router, prefix="/auth", tags=["Auth"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting E-Learning API...")
    yield
    # Shutdown
    print("Shutting down E-Learning API...")
    await close_connections()

# Create FastAPI app with lifespan management
app = FastAPI(
    title="E-Learning API",
    version="1.0.0",
    description="API for managing courses, progress, analytics, and authentication",
    lifespan=lifespan
)

# Test endpoints first without importing problematic routes
@app.get("/")
def root():
    return {"message": "E-Learning API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "E-Learning API is running",
        "version": "1.0.0"
    }

# Test Redis connection
@app.get("/test-redis")
async def test_redis_connection():
    try:
        from app.dependencies import ping_redis
        is_alive = await ping_redis()
        return {"redis_connected": is_alive}
    except Exception as e:
        return {"redis_connected": False, "error": str(e)}

# Test MongoDB connection
@app.get("/test-mongodb")
async def test_mongodb_connection():
    try:
        from app.dependencies import get_database
        db = await get_database()
        # Try to ping MongoDB
        await db.command("ping")
        return {"mongodb_connected": True}
    except Exception as e:
        return {"mongodb_connected": False, "error": str(e)}

if __name__ == "__main__":
    print("Starting E-Learning API in minimal mode...")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)


# main.py
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.openapi.models import HTTPBearer as HTTPBearerModel
from fastapi.openapi.utils import get_openapi

from app.routes import auth, course, analytics, progress, cache, test_redis
from app.dependencies import close_connections

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting E-Learning API...")
    yield
    # Shutdown
    print("Shutting down E-Learning API...")
    await close_connections()

# Create FastAPI app with lifespan management
app = FastAPI(
    title="E-Learning API",
    version="1.0.0",
    description="API for managing courses, progress, analytics, and authentication",
    lifespan=lifespan
)

# Add JWT security
security = HTTPBearer()

# Include routers with prefixes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(course.router, prefix="/courses", tags=["Courses"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(progress.router, prefix="/progress", tags=["Progress"])
app.include_router(cache.router, prefix="/cache", tags=["Cache"])
# from app.routes.test_redis import router as test_redis_router
# app.include_router(test_redis_router, tags=["Test"])

# Custom OpenAPI to add extra metadata and JWT security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add JWT security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token"
        }
    }

    # Add security to protected endpoints (exclude auth endpoints)
    for path in openapi_schema["paths"]:
        if not path.startswith("/auth/"):  # Don't require auth for auth endpoints
            for method in openapi_schema["paths"][path]:
                if method.lower() != "options":
                    openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    # Add a logo (optional)
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Root endpoint
@app.get("/", tags=["Root"])
def root():
    return {"message": "E-Learning API is running"}


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "message": "E-Learning API is running",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
