from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db
from api.auth import router as auth_router
from api.resource import router as resource_router
from api.acl_resource import router as acl_resource_router
from api.gateway import router as gateway_router
from api.skill_list import router as skill_list_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    init_db()
    yield
    # Shutdown (if needed)
    pass


app = FastAPI(
    title="SkillHub API",
    description="SkillHub MVP Backend API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(resource_router, prefix="/api/v1")
app.include_router(acl_resource_router, prefix="/api/v1")
app.include_router(gateway_router, prefix="/api/v1")
app.include_router(skill_list_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "SkillHub MVP API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        #reload=True,  # Enable auto-reload for development
        log_level="info"
    )
