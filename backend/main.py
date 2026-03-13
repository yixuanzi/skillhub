from fastapi import FastAPI
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db
from api.auth import router as auth_router
from api.resource import router as resource_router
from api.acl_resource import router as acl_resource_router
from api.gateway import router as gateway_router
from api.skill_list import router as skill_list_router
from api.mtoken import router as mtoken_router
from api.api_key import router as api_key_router
from api.audit_log import router as audit_log_router
from api.user_management import router as user_management_router, role_router, permission_router
from api.skill_creator import router as skill_creator_router
from api.script import router as script_router
from middleware.audit_middleware import audit_middleware


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

# Add audit logging middleware
app.middleware("http")(audit_middleware)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(resource_router, prefix="/api/v1")
app.include_router(acl_resource_router, prefix="/api/v1")
app.include_router(gateway_router, prefix="/api/v1")
app.include_router(skill_list_router, prefix="/api/v1")
app.include_router(mtoken_router, prefix="/api/v1")
app.include_router(api_key_router, prefix="/api/v1")
app.include_router(audit_log_router, prefix="/api/v1")
app.include_router(user_management_router, prefix="/api/v1")
app.include_router(role_router, prefix="/api/v1")
app.include_router(permission_router, prefix="/api/v1")
app.include_router(skill_creator_router, prefix="/api/v1")
app.include_router(script_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "SkillHub MVP API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.SKILL_HOST,
        port=settings.SKILL_PORT,
        #reload=True,  # Enable auto-reload for development
        log_level="info"
    )
