# Skill Market Management Module - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a complete skill market management module with CRUD operations, authentication, filtering, and pagination.

**Architecture:** FastAPI backend with SQLAlchemy ORM, following the existing resource module pattern. Three-layer architecture (API → Service → Model) with Pydantic schemas for validation.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Pytest, JWT authentication

---

## Task 1: Create SkillList SQLAlchemy Model

**Files:**
- Create: `backend/models/skill_list.py`
- Modify: `backend/models/__init__.py`

**Step 1: Create the model file**

Write: `backend/models/skill_list.py`

```python
"""SkillList model for managing AI agent skills.

This module defines the SkillList model which represents skills in the skill market,
including metadata, content, categorization, and versioning.
"""
from sqlalchemy import Column, String, Text, DateTime, Index
from database import Base
import uuid
from datetime import timezone, datetime


class SkillList(Base):
    """SkillList model for managing AI agent skills.

    Skills represent reusable AI agent capabilities with documentation,
    categorization, and version tracking.
    """
    __tablename__ = "skill_list"

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic Fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    desc = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Markdown documentation
    author = Column(String(255), nullable=False, index=True)

    # Additional Features
    category = Column(String(100), nullable=True, index=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    version = Column(String(50), default="1.0.0")

    # Timestamps
    create_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_time = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                      onupdate=lambda: datetime.now(timezone.utc))

    # Indexes
    __table_args__ = (
        Index('ix_skill_list_category', 'category'),
        Index('ix_skill_list_author', 'author'),
    )
```

**Step 2: Update models/__init__.py**

Read: `backend/models/__init__.py`

Add the import at the end of the file:
```python
from models.skill_list import SkillList
```

**Step 3: Verify model imports**

Run: `cd backend && python -c "from models.skill_list import SkillList; print('Model imported successfully')"`

Expected: "Model imported successfully"

**Step 4: Commit**

```bash
git add backend/models/skill_list.py backend/models/__init__.py
git commit -m "feat(models): add SkillList model for skill market management"
```

---

## Task 2: Create Pydantic Schemas

**Files:**
- Create: `backend/schemas/skill_list.py`

**Step 1: Create schema file**

Write: `backend/schemas/skill_list.py`

```python
"""Pydantic schemas for skill market management API.

This module defines the request/response schemas used by the skill list API endpoints,
including base models for create, update, and response operations.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Base Schema
class SkillListBase(BaseModel):
    """Base schema for skill list data."""
    name: str = Field(..., min_length=1, max_length=255)
    desc: Optional[str] = Field(None, max_length=10000)
    content: Optional[str] = Field(None, max_length=100000)
    author: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    version: str = Field(default="1.0.0", max_length=50)


# Create Schema
class SkillListCreate(SkillListBase):
    """Schema for creating a new skill."""
    pass


# Update Schema
class SkillListUpdate(BaseModel):
    """Schema for updating an existing skill."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    desc: Optional[str] = Field(None, max_length=10000)
    content: Optional[str] = Field(None, max_length=100000)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    version: Optional[str] = Field(None, max_length=50)


# Response Schema
class SkillListResponse(SkillListBase):
    """Schema for skill list response."""
    id: str
    create_time: datetime
    last_time: datetime

    class Config:
        from_attributes = True


# List Response Schema (paginated)
class SkillListListResponse(BaseModel):
    """Schema for paginated skill list response."""
    items: list[SkillListResponse]
    total: int
    page: int
    size: int
```

**Step 2: Verify schemas import correctly**

Run: `cd backend && python -c "from schemas.skill_list import SkillListCreate, SkillListUpdate, SkillListResponse; print('Schemas imported successfully')"`

Expected: "Schemas imported successfully"

**Step 3: Commit**

```bash
git add backend/schemas/skill_list.py
git commit -m "feat(schemas): add Pydantic schemas for skill market management"
```

---

## Task 3: Implement SkillList Service Layer

**Files:**
- Create: `backend/services/skill_list_service.py`

**Step 1: Create service file with all methods**

Write: `backend/services/skill_list_service.py`

```python
"""SkillList service for skill market management operations.

This module provides the business logic layer for skill CRUD operations,
including creation, retrieval, update, and deletion of skills.
"""
from sqlalchemy.orm import Session
from models.skill_list import SkillList
from schemas.skill_list import SkillListCreate, SkillListUpdate, SkillListResponse
from core.exceptions import ValidationException, NotFoundException
from typing import Optional, List


class SkillListService:
    """Service class for skill market management operations."""

    @staticmethod
    def create(db: Session, skill_data: SkillListCreate) -> SkillListResponse:
        """Create a new skill.

        Args:
            db: Database session
            skill_data: Skill creation data

        Returns:
            Created skill response

        Raises:
            ValidationException: If skill with the same name already exists
        """
        # Check name uniqueness
        existing = db.query(SkillList).filter(SkillList.name == skill_data.name).first()
        if existing:
            raise ValidationException(f"Skill with name '{skill_data.name}' already exists")

        # Create skill
        new_skill = SkillList(
            name=skill_data.name,
            desc=skill_data.desc,
            content=skill_data.content,
            author=skill_data.author,
            category=skill_data.category,
            tags=skill_data.tags,
            version=skill_data.version
        )

        db.add(new_skill)
        db.commit()
        db.refresh(new_skill)

        return SkillListResponse.model_validate(new_skill)

    @staticmethod
    def get_by_id(db: Session, skill_id: str) -> Optional[SkillList]:
        """Get skill by ID.

        Args:
            db: Database session
            skill_id: Skill UUID

        Returns:
            SkillList object or None if not found
        """
        return db.query(SkillList).filter(SkillList.id == skill_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[SkillList]:
        """Get skill by name.

        Args:
            db: Database session
            name: Skill name

        Returns:
            SkillList object or None if not found
        """
        return db.query(SkillList).filter(SkillList.name == name).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[SkillList]:
        """List all skills with pagination.

        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of skills
        """
        return db.query(SkillList).order_by(SkillList.create_time.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_category(db: Session, category: str, skip: int = 0, limit: int = 100) -> List[SkillList]:
        """List skills by category.

        Args:
            db: Database session
            category: Category to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered skills
        """
        return db.query(SkillList).filter(
            SkillList.category == category
        ).order_by(SkillList.create_time.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_author(db: Session, author: str, skip: int = 0, limit: int = 100) -> List[SkillList]:
        """List skills by author.

        Args:
            db: Database session
            author: Author to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered skills
        """
        return db.query(SkillList).filter(
            SkillList.author == author
        ).order_by(SkillList.create_time.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_tags(db: Session, tags: str, skip: int = 0, limit: int = 100) -> List[SkillList]:
        """List skills by tags (comma-separated).

        Args:
            db: Database session
            tags: Comma-separated tags to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered skills
        """
        # Split tags and filter
        tag_list = [t.strip() for t in tags.split(',')]
        query = db.query(SkillList)

        # Filter: skills that contain ANY of the specified tags
        for tag in tag_list:
            query = query.filter(SkillList.tags.like(f'%{tag}%'))

        return query.order_by(SkillList.create_time.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def count_all(db: Session) -> int:
        """Count total number of skills.

        Args:
            db: Database session

        Returns:
            Total count of skills
        """
        return db.query(SkillList).count()

    @staticmethod
    def count_by_category(db: Session, category: str) -> int:
        """Count skills by category.

        Args:
            db: Database session
            category: Category to filter by

        Returns:
            Count of filtered skills
        """
        return db.query(SkillList).filter(SkillList.category == category).count()

    @staticmethod
    def count_by_author(db: Session, author: str) -> int:
        """Count skills by author.

        Args:
            db: Database session
            author: Author to filter by

        Returns:
            Count of filtered skills
        """
        return db.query(SkillList).filter(SkillList.author == author).count()

    @staticmethod
    def count_by_tags(db: Session, tags: str) -> int:
        """Count skills by tags.

        Args:
            db: Database session
            tags: Comma-separated tags to filter by

        Returns:
            Count of filtered skills
        """
        tag_list = [t.strip() for t in tags.split(',')]
        query = db.query(SkillList)

        for tag in tag_list:
            query = query.filter(SkillList.tags.like(f'%{tag}%'))

        return query.count()

    @staticmethod
    def update(db: Session, skill_id: str, skill_data: SkillListUpdate) -> SkillListResponse:
        """Update an existing skill.

        Args:
            db: Database session
            skill_id: Skill UUID
            skill_data: Skill update data

        Returns:
            Updated skill response

        Raises:
            NotFoundException: If skill is not found
            ValidationException: If new name conflicts with existing skill
        """
        skill = db.query(SkillList).filter(SkillList.id == skill_id).first()
        if not skill:
            raise NotFoundException(f"Skill with id '{skill_id}' not found")

        # Check name uniqueness (if changing name)
        if skill_data.name and skill_data.name != skill.name:
            existing = db.query(SkillList).filter(
                SkillList.name == skill_data.name
            ).first()
            if existing:
                raise ValidationException(f"Skill with name '{skill_data.name}' already exists")
            skill.name = skill_data.name

        # Update fields
        if skill_data.desc is not None:
            skill.desc = skill_data.desc
        if skill_data.content is not None:
            skill.content = skill_data.content
        if skill_data.author is not None:
            skill.author = skill_data.author
        if skill_data.category is not None:
            skill.category = skill_data.category
        if skill_data.tags is not None:
            skill.tags = skill_data.tags
        if skill_data.version is not None:
            skill.version = skill_data.version

        db.commit()
        db.refresh(skill)

        return SkillListResponse.model_validate(skill)

    @staticmethod
    def delete(db: Session, skill_id: str) -> bool:
        """Delete a skill.

        Args:
            db: Database session
            skill_id: Skill UUID

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If skill is not found
        """
        skill = db.query(SkillList).filter(SkillList.id == skill_id).first()
        if not skill:
            raise NotFoundException(f"Skill with id '{skill_id}' not found")

        db.delete(skill)
        db.commit()

        return True
```

**Step 2: Verify service imports correctly**

Run: `cd backend && python -c "from services.skill_list_service import SkillListService; print('Service imported successfully')"`

Expected: "Service imported successfully"

**Step 3: Commit**

```bash
git add backend/services/skill_list_service.py
git commit -m "feat(services): add SkillListService for skill market management"
```

---

## Task 4: Implement API Router

**Files:**
- Create: `backend/api/skill_list.py`
- Modify: `backend/main.py`

**Step 1: Create API router**

Write: `backend/api/skill_list.py`

```python
"""SkillList API endpoints for skill market management operations.

This module provides FastAPI endpoints for skill CRUD operations including:
- Create skill
- List skills (with pagination and filtering)
- Get skill by ID
- Update skill
- Delete skill
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated

from database import get_db
from schemas.skill_list import (
    SkillListCreate,
    SkillListUpdate,
    SkillListResponse,
    SkillListListResponse
)
from services.skill_list_service import SkillListService
from core.deps import get_current_active_user
from models.user import User

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.post("/", response_model=SkillListResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new skill.

    Args:
        skill_data: Skill creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created skill response

    Raises:
        HTTPException 400: If validation fails (e.g., duplicate name)
    """
    from core.exceptions import ValidationException

    try:
        return SkillListService.create(db, skill_data)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=SkillListListResponse)
async def list_skills(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    category: str | None = Query(None, description="Filter by category"),
    tags: str | None = Query(None, description="Filter by tags (comma-separated)"),
    author: str | None = Query(None, description="Filter by author"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all skills with optional filtering.

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        category: Optional category filter
        tags: Optional tags filter (comma-separated)
        author: Optional author filter
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of skills
    """
    skip = (page - 1) * size

    # Apply filters based on provided parameters
    if category:
        skills = SkillListService.list_by_category(db, category, skip, size)
        total = SkillListService.count_by_category(db, category)
    elif tags:
        skills = SkillListService.list_by_tags(db, tags, skip, size)
        total = SkillListService.count_by_tags(db, tags)
    elif author:
        skills = SkillListService.list_by_author(db, author, skip, size)
        total = SkillListService.count_by_author(db, author)
    else:
        skills = SkillListService.list_all(db, skip, size)
        total = SkillListService.count_all(db)

    return SkillListListResponse(
        items=[SkillListResponse.model_validate(s) for s in skills],
        total=total,
        page=page,
        size=size
    )


@router.get("/{skill_id}", response_model=SkillListResponse)
async def get_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific skill by ID.

    Args:
        skill_id: Skill UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Skill response

    Raises:
        HTTPException 404: If skill is not found
    """
    skill = SkillListService.get_by_id(db, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id '{skill_id}' not found"
        )
    return SkillListResponse.model_validate(skill)


@router.put("/{skill_id}", response_model=SkillListResponse)
async def update_skill(
    skill_id: str,
    skill_data: SkillListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a skill.

    Args:
        skill_id: Skill UUID
        skill_data: Skill update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated skill response

    Raises:
        HTTPException 404: If skill is not found
        HTTPException 400: If validation fails (e.g., duplicate name)
    """
    from core.exceptions import NotFoundException, ValidationException

    try:
        return SkillListService.update(db, skill_id, skill_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a skill.

    Args:
        skill_id: Skill UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: If skill is not found
    """
    from core.exceptions import NotFoundException

    try:
        SkillListService.delete(db, skill_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return None
```

**Step 2: Register router in main.py**

Read: `backend/main.py`

Add the import at the top (after other router imports):
```python
from api.skill_list import router as skill_list_router
```

Add the router registration in the app (after other routers):
```python
app.include_router(skill_list_router, prefix="/api/v1")
```

**Step 3: Verify FastAPI app starts**

Run: `cd backend && python -c "from main import app; print('App loaded successfully')"`

Expected: "App loaded successfully"

**Step 4: Commit**

```bash
git add backend/api/skill_list.py backend/main.py
git commit -m "feat(api): add skill market API endpoints"
```

---

## Task 5: Initialize Database Table

**Step 1: Create database migration script**

Write: `backend/scripts/create_skill_list_table.py`

```python
"""Script to create the skill_list table."""
from database import engine, Base
from models.skill_list import SkillList


def create_table():
    """Create the skill_list table."""
    print("Creating skill_list table...")
    Base.metadata.create_all(bind=engine, tables=[SkillList.__table__])
    print("skill_list table created successfully!")


if __name__ == "__main__":
    create_table()
```

**Step 2: Run the table creation script**

Run: `cd backend && python scripts/create_skill_list_table.py`

Expected: "skill_list table created successfully!"

**Step 3: Verify table exists**

Run: `cd backend && python -c "from models.skill_list import SkillList; print(f'Table name: {SkillList.__tablename__}')"`

Expected: "Table name: skill_list"

**Step 4: Commit**

```bash
git add backend/scripts/create_skill_list_table.py
git commit -m "feat(db): add script to create skill_list table"
```

---

## Task 6: Write Unit Tests for Service Layer

**Files:**
- Create: `backend/tests/test_skill_list_service.py`

**Step 1: Create service tests**

Write: `backend/tests/test_skill_list_service.py`

```python
"""Unit tests for SkillListService.

Tests the business logic layer for skill market management operations.
"""
import pytest
from sqlalchemy.orm import Session
from models.skill_list import SkillList
from schemas.skill_list import SkillListCreate, SkillListUpdate
from services.skill_list_service import SkillListService
from core.exceptions import ValidationException, NotFoundException


class TestSkillListServiceCreate:
    """Tests for skill creation."""

    def test_create_skill_success(self, db: Session):
        """Test successful skill creation."""
        data = SkillListCreate(
            name="Test Skill",
            desc="A test skill",
            content="# Test Content",
            author="Test Author",
            category="test",
            tags="test,unit",
            version="1.0.0"
        )

        result = SkillListService.create(db, data)

        assert result.id is not None
        assert result.name == "Test Skill"
        assert result.author == "Test Author"
        assert result.category == "test"
        assert result.tags == "test,unit"

    def test_create_skill_duplicate_name_raises_error(self, db: Session):
        """Test that creating a skill with duplicate name raises ValidationException."""
        data = SkillListCreate(
            name="Duplicate Skill",
            desc="First skill",
            author="Author 1"
        )

        # Create first skill
        SkillListService.create(db, data)

        # Try to create duplicate
        duplicate_data = SkillListCreate(
            name="Duplicate Skill",
            desc="Second skill",
            author="Author 2"
        )

        with pytest.raises(ValidationException) as exc_info:
            SkillListService.create(db, duplicate_data)

        assert "already exists" in str(exc_info.value)


class TestSkillListServiceGet:
    """Tests for skill retrieval."""

    def test_get_by_id_found(self, db: Session):
        """Test getting a skill by ID when it exists."""
        data = SkillListCreate(
            name="Get Test Skill",
            desc="Test",
            author="Author"
        )
        created = SkillListService.create(db, data)

        result = SkillListService.get_by_id(db, created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Get Test Skill"

    def test_get_by_id_not_found(self, db: Session):
        """Test getting a skill by ID when it doesn't exist."""
        result = SkillListService.get_by_id(db, "non-existent-id")
        assert result is None

    def test_get_by_name_found(self, db: Session):
        """Test getting a skill by name when it exists."""
        data = SkillListCreate(
            name="Name Test Skill",
            desc="Test",
            author="Author"
        )
        SkillListService.create(db, data)

        result = SkillListService.get_by_name(db, "Name Test Skill")

        assert result is not None
        assert result.name == "Name Test Skill"


class TestSkillListServiceList:
    """Tests for skill listing and filtering."""

    def test_list_all_with_pagination(self, db: Session):
        """Test listing all skills with pagination."""
        # Create multiple skills
        for i in range(5):
            data = SkillListCreate(
                name=f"Skill {i}",
                desc="Test",
                author="Author"
            )
            SkillListService.create(db, data)

        skills = SkillListService.list_all(db, skip=0, limit=3)

        assert len(skills) == 3

    def test_list_by_category(self, db: Session):
        """Test filtering skills by category."""
        data1 = SkillListCreate(
            name="Data Skill",
            category="data-processing",
            author="Author"
        )
        data2 = SkillListCreate(
            name="AI Skill",
            category="ai-integration",
            author="Author"
        )
        SkillListService.create(db, data1)
        SkillListService.create(db, data2)

        skills = SkillListService.list_by_category(db, "data-processing")

        assert len(skills) == 1
        assert skills[0].category == "data-processing"

    def test_list_by_author(self, db: Session):
        """Test filtering skills by author."""
        data1 = SkillListCreate(
            name="Skill by John",
            author="John Doe"
        )
        data2 = SkillListCreate(
            name="Skill by Jane",
            author="Jane Doe"
        )
        SkillListService.create(db, data1)
        SkillListService.create(db, data2)

        skills = SkillListService.list_by_author(db, "John Doe")

        assert len(skills) == 1
        assert skills[0].author == "John Doe"

    def test_list_by_tags(self, db: Session):
        """Test filtering skills by tags."""
        data1 = SkillListCreate(
            name="ETL Skill",
            tags="etl,postgres,data",
            author="Author"
        )
        data2 = SkillListCreate(
            name="AI Skill",
            tags="ai,ml",
            author="Author"
        )
        SkillListService.create(db, data1)
        SkillListService.create(db, data2)

        skills = SkillListService.list_by_tags(db, "etl,data")

        assert len(skills) == 1
        assert "ETL" in skills[0].name

    def test_count_all(self, db: Session):
        """Test counting all skills."""
        initial_count = SkillListService.count_all(db)

        for i in range(3):
            data = SkillListCreate(
                name=f"Skill {i}",
                author="Author"
            )
            SkillListService.create(db, data)

        final_count = SkillListService.count_all(db)
        assert final_count == initial_count + 3


class TestSkillListServiceUpdate:
    """Tests for skill updates."""

    def test_update_skill_success(self, db: Session):
        """Test successful skill update."""
        data = SkillListCreate(
            name="Original Name",
            desc="Original desc",
            author="Author"
        )
        created = SkillListService.create(db, data)

        update_data = SkillListUpdate(
            name="Updated Name",
            desc="Updated desc"
        )
        result = SkillListService.update(db, created.id, update_data)

        assert result.name == "Updated Name"
        assert result.desc == "Updated desc"

    def test_update_skill_duplicate_name_raises_error(self, db: Session):
        """Test that updating to a duplicate name raises ValidationException."""
        data1 = SkillListCreate(
            name="Skill One",
            author="Author"
        )
        data2 = SkillListCreate(
            name="Skill Two",
            author="Author"
        )
        skill1 = SkillListService.create(db, data1)
        SkillListService.create(db, data2)

        update_data = SkillListUpdate(name="Skill Two")

        with pytest.raises(ValidationException) as exc_info:
            SkillListService.update(db, skill1.id, update_data)

        assert "already exists" in str(exc_info.value)

    def test_update_skill_not_found_raises_error(self, db: Session):
        """Test that updating non-existent skill raises NotFoundException."""
        update_data = SkillListUpdate(name="New Name")

        with pytest.raises(NotFoundException) as exc_info:
            SkillListService.update(db, "non-existent-id", update_data)

        assert "not found" in str(exc_info.value)


class TestSkillListServiceDelete:
    """Tests for skill deletion."""

    def test_delete_skill_success(self, db: Session):
        """Test successful skill deletion."""
        data = SkillListCreate(
            name="To Delete",
            author="Author"
        )
        created = SkillListService.create(db, data)

        result = SkillListService.delete(db, created.id)

        assert result is True

        # Verify deletion
        skill = SkillListService.get_by_id(db, created.id)
        assert skill is None

    def test_delete_skill_not_found_raises_error(self, db: Session):
        """Test that deleting non-existent skill raises NotFoundException."""
        with pytest.raises(NotFoundException) as exc_info:
            SkillListService.delete(db, "non-existent-id")

        assert "not found" in str(exc_info.value)
```

**Step 2: Run service tests**

Run: `cd backend && pytest tests/test_skill_list_service.py -v`

Expected: All tests pass

**Step 3: Commit**

```bash
git add backend/tests/test_skill_list_service.py
git commit -m "test(services): add unit tests for SkillListService"
```

---

## Task 7: Write Integration Tests for API Layer

**Files:**
- Create: `backend/tests/test_skill_list_api.py`

**Step 1: Create API tests**

Write: `backend/tests/test_skill_list_api.py`

```python
"""Integration tests for skill market API endpoints.

Tests the FastAPI endpoints for skill CRUD operations.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app


client = TestClient(app)


class TestCreateSkill:
    """Tests for POST /api/v1/skills"""

    def test_create_skill_success(self, db: Session, auth_headers: dict):
        """Test successful skill creation."""
        data = {
            "name": "API Test Skill",
            "desc": "Created via API",
            "content": "# Test",
            "author": "API Author",
            "category": "test",
            "tags": "api,test",
            "version": "1.0.0"
        }

        response = client.post("/api/v1/skills/", json=data, headers=auth_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "API Test Skill"
        assert result["author"] == "API Author"
        assert "id" in result

    def test_create_skill_duplicate_name_returns_400(self, db: Session, auth_headers: dict):
        """Test that creating duplicate skill returns 400."""
        data = {
            "name": "Duplicate API Skill",
            "author": "Author"
        }

        # Create first skill
        client.post("/api/v1/skills/", json=data, headers=auth_headers)

        # Try to create duplicate
        response = client.post("/api/v1/skills/", json=data, headers=auth_headers)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_skill_unauthorized_returns_401(self, db: Session):
        """Test that creating skill without auth returns 401."""
        data = {
            "name": "Unauthorized Skill",
            "author": "Author"
        }

        response = client.post("/api/v1/skills/", json=data)

        assert response.status_code == 401


class TestListSkills:
    """Tests for GET /api/v1/skills"""

    def test_list_skills_success(self, db: Session, auth_headers: dict):
        """Test successful skill listing."""
        response = client.get("/api/v1/skills/", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result

    def test_list_skills_with_pagination(self, db: Session, auth_headers: dict):
        """Test listing skills with pagination parameters."""
        response = client.get("/api/v1/skills/?page=1&size=10", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["page"] == 1
        assert result["size"] == 10

    def test_list_skills_with_category_filter(self, db: Session, auth_headers: dict):
        """Test filtering skills by category."""
        # Create skills with different categories
        data1 = {
            "name": "Data Skill",
            "category": "data",
            "author": "Author"
        }
        data2 = {
            "name": "AI Skill",
            "category": "ai",
            "author": "Author"
        }
        client.post("/api/v1/skills/", json=data1, headers=auth_headers)
        client.post("/api/v1/skills/", json=data2, headers=auth_headers)

        response = client.get("/api/v1/skills/?category=data", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert all(skill["category"] == "data" for skill in result["items"])

    def test_list_skills_unauthorized_returns_401(self, db: Session):
        """Test that listing skills without auth returns 401."""
        response = client.get("/api/v1/skills/")
        assert response.status_code == 401


class TestGetSkill:
    """Tests for GET /api/v1/skills/{id}"""

    def test_get_skill_found(self, db: Session, auth_headers: dict):
        """Test getting existing skill by ID."""
        # Create a skill first
        data = {
            "name": "Get Test Skill",
            "author": "Author"
        }
        create_response = client.post("/api/v1/skills/", json=data, headers=auth_headers)
        skill_id = create_response.json()["id"]

        # Get the skill
        response = client.get(f"/api/v1/skills/{skill_id}", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == skill_id
        assert result["name"] == "Get Test Skill"

    def test_get_skill_not_found_returns_404(self, db: Session, auth_headers: dict):
        """Test getting non-existent skill returns 404."""
        response = client.get("/api/v1/skills/non-existent-id", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUpdateSkill:
    """Tests for PUT /api/v1/skills/{id}"""

    def test_update_skill_success(self, db: Session, auth_headers: dict):
        """Test successful skill update."""
        # Create a skill first
        data = {
            "name": "Update Test Skill",
            "desc": "Original",
            "author": "Author"
        }
        create_response = client.post("/api/v1/skills/", json=data, headers=auth_headers)
        skill_id = create_response.json()["id"]

        # Update the skill
        update_data = {
            "name": "Updated Name",
            "desc": "Updated description"
        }
        response = client.put(f"/api/v1/skills/{skill_id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Name"
        assert result["desc"] == "Updated description"

    def test_update_skill_not_found_returns_404(self, db: Session, auth_headers: dict):
        """Test updating non-existent skill returns 404."""
        update_data = {"name": "New Name"}
        response = client.put("/api/v1/skills/non-existent-id", json=update_data, headers=auth_headers)

        assert response.status_code == 404


class TestDeleteSkill:
    """Tests for DELETE /api/v1/skills/{id}"""

    def test_delete_skill_success(self, db: Session, auth_headers: dict):
        """Test successful skill deletion."""
        # Create a skill first
        data = {
            "name": "Delete Test Skill",
            "author": "Author"
        }
        create_response = client.post("/api/v1/skills/", json=data, headers=auth_headers)
        skill_id = create_response.json()["id"]

        # Delete the skill
        response = client.delete(f"/api/v1/skills/{skill_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/skills/{skill_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_skill_not_found_returns_404(self, db: Session, auth_headers: dict):
        """Test deleting non-existent skill returns 404."""
        response = client.delete("/api/v1/skills/non-existent-id", headers=auth_headers)

        assert response.status_code == 404
```

**Step 2: Run API tests**

Run: `cd backend && pytest tests/test_skill_list_api.py -v`

Expected: All tests pass

**Step 3: Commit**

```bash
git add backend/tests/test_skill_list_api.py
git commit -m "test(api): add integration tests for skill market endpoints"
```

---

## Task 8: Verify All Tests Pass

**Step 1: Run all skill list tests**

Run: `cd backend && pytest tests/test_skill_list*.py -v`

Expected: All tests pass

**Step 2: Run all backend tests to ensure no regressions**

Run: `cd backend && pytest tests/ -v`

Expected: All tests pass

**Step 3: Verify API documentation**

Start server: `cd backend && python main.py`

Visit: `http://localhost:8000/docs`

Verify: All skill endpoints are visible and documented

Stop server: `Ctrl+C`

**Step 4: Final commit**

```bash
git add backend/
git commit -m "feat(skill-market): complete skill market management module

- Add SkillList model with UUID, timestamps, and indexes
- Add Pydantic schemas for validation
- Add SkillListService with CRUD operations
- Add API endpoints with authentication
- Add comprehensive unit and integration tests
- Support filtering by category, author, and tags
- Support pagination for list endpoints
```

---

## Task 9: Update API Documentation

**Files:**
- Modify: `docs/api-design.md`

**Step 1: Add skill market endpoints documentation**

Read: `docs/api-design.md`

Add section after resources section:

```markdown
### Skill Market Endpoints

#### Create Skill
**POST** `/api/v1/skills`

Creates a new skill in the skill market.

**Request Body:**
```json
{
  "name": "string (1-255, required)",
  "desc": "string (optional, max 10000)",
  "content": "string (optional, max 100000)",
  "author": "string (1-255, required)",
  "category": "string (optional, max 100)",
  "tags": "string (optional, comma-separated, max 500)",
  "version": "string (optional, default '1.0.0')"
}
```

**Response:** `201 Created` with skill object

#### List Skills
**GET** `/api/v1/skills`

Lists skills with pagination and optional filtering.

**Query Parameters:**
- `page` (optional): Page number, default 1
- `size` (optional): Page size, default 20, max 100
- `category` (optional): Filter by category
- `tags` (optional): Filter by tags (comma-separated)
- `author` (optional): Filter by author

**Response:** `200 OK` with paginated list

#### Get Skill
**GET** `/api/v1/skills/{id}`

Gets a specific skill by ID.

**Response:** `200 OK` with skill object or `404 Not Found`

#### Update Skill
**PUT** `/api/v1/skills/{id}`

Updates an existing skill. All fields optional.

**Response:** `200 OK` with updated skill or `404 Not Found`

#### Delete Skill
**DELETE** `/api/v1/skills/{id}`

Deletes a skill.

**Response:** `204 No Content` or `404 Not Found`
```

**Step 2: Commit documentation**

```bash
git add docs/api-design.md
git commit -m "docs(api): add skill market endpoints documentation"
```

---

## Task 10: Verify Implementation Complete

**Step 1: Create verification checklist**

Run the following checks:

1. ✅ Model created with all fields
2. ✅ Schemas created with validation
3. ✅ Service layer implemented
4. ✅ API endpoints working
5. ✅ Database table created
6. ✅ All tests passing
7. ✅ Documentation updated
8. ✅ Authentication required on all endpoints
9. ✅ Pagination working
10. ✅ Filtering by category, author, tags working

**Step 2: Run final test suite**

Run: `cd backend && pytest tests/test_skill_list*.py -v --tb=short --cov=services/skill_list_service --cov=api/skill_list --cov-report=term-missing`

Expected: All tests pass with >80% coverage

**Step 3: Test API manually with curl or Postman**

Create skill:
```bash
curl -X POST http://localhost:8000/api/v1/skills/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Skill",
    "author": "Test Author",
    "category": "test",
    "tags": "test,api"
  }'
```

List skills:
```bash
curl http://localhost:8000/api/v1/skills/ \
  -H "Authorization: Bearer <token>"
```

**Step 4: Final verification commit**

```bash
echo "# Skill Market Module - Complete

## Implementation Status
✅ Database schema (skill_list table)
✅ SQLAlchemy model (models/skill_list.py)
✅ Pydantic schemas (schemas/skill_list.py)
✅ Service layer (services/skill_list_service.py)
✅ API endpoints (api/skill_list.py)
✅ Unit tests (tests/test_skill_list_service.py)
✅ Integration tests (tests/test_skill_list_api.py)
✅ API documentation (docs/api-design.md)

## Features
- CRUD operations for skills
- Authentication required on all endpoints
- Pagination support
- Filtering by category, author, and tags
- Version tracking
- Comprehensive test coverage

## Files Created/Modified
- backend/models/skill_list.py (NEW)
- backend/schemas/skill_list.py (NEW)
- backend/services/skill_list_service.py (NEW)
- backend/api/skill_list.py (NEW)
- backend/tests/test_skill_list_service.py (NEW)
- backend/tests/test_skill_list_api.py (NEW)
- backend/scripts/create_skill_list_table.py (NEW)
- backend/models/__init__.py (MODIFIED)
- backend/main.py (MODIFIED)
- docs/api-design.md (MODIFIED)
" > IMPLEMENTATION_COMPLETE.md

git add IMPLEMENTATION_COMPLETE.md
git commit -m "docs: mark skill market module implementation complete"
```

---

## Notes for Implementation

1. **Follow TDD**: Write tests first, then implementation
2. **Use existing patterns**: Mirror the resource module exactly
3. **Commit frequently**: Each task should end with a commit
4. **Run tests often**: After each step, verify tests pass
5. **Check documentation**: Review docs/development.md for coding standards
6. **Validate assumptions**: If something seems wrong, verify with existing code

## Testing Checklist

Before marking complete, ensure:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No regressions in other tests
- [ ] API documentation is accessible at /docs
- [ ] Authentication works correctly
- [ ] Pagination works
- [ ] All filters work (category, author, tags)
- [ ] Error handling works correctly
- [ ] Test coverage > 80%

## Success Criteria

The implementation is complete when:
1. ✅ All CRUD endpoints working
2. ✅ Authentication required on all endpoints
3. ✅ Pagination and filtering functional
4. ✅ Test coverage > 80%
5. ✅ Consistent with existing codebase patterns
6. ✅ Documentation updated
