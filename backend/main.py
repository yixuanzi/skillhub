from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db
from api.auth import router as auth_router


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


@app.get("/")
async def root():
    return {"message": "SkillHub MVP API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
