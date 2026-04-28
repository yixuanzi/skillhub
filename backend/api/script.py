"""Script API endpoints for serving utility scripts.

This module provides FastAPI endpoints for serving shell scripts and utilities,
allowing clients to download scripts with environment-specific configurations.
"""
from fastapi import APIRouter, Response
from sqlalchemy.orm import Session
from typing import Optional
from config import settings
import os
import sys

router = APIRouter(prefix="/script", tags=["Script"])

SCRIPT_DIR = os.path.join(os.getcwd(), "scripts")

@router.get("/health/")
async def health():
    return {"status": "healthy","version": "1.0.0","message": "SkillHub Service is running","SKILLHUB_URL": settings.SKILLHUB_URL}

@router.get("/bash")
async def get_bash_script():
    """Get the SkillHub bash script with environment-specific configuration.

    This endpoint serves the skillhub.sh script with the SKILLHUB_URL
    replaced with the value from the environment variable.

    The script can be used to interact with SkillHub gateway resources
    from the command line.

    Returns:
        Shell script content with environment-specific SKILLHUB_URL

    Example:
        curl http://localhost:8000/api/v1/script/bash -o skillhub.sh
        chmod +x skillhub.sh
        ./skillhub.sh -h
    """
    script_path = os.path.join(SCRIPT_DIR, "skillhub")

    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()

        # Get SKILLHUB_URL from environment variable
        skillhub_url = os.getenv('SKILLHUB_URL', 'http://localhost:8000')

        # Replace the default SKILLHUB_URL in the script
        script_content = script_content.replace(
            "{SKILLHUB_URL}",
            settings.SKILLHUB_URL
        )

        return Response(
            content=script_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": 'attachment; filename="skillhub"'
            }
        )
    except FileNotFoundError:
        return Response(
            content="Script file not found",
            status_code=404,
            media_type="text/plain"
        )


@router.get("/install")
async def get_install_guide():
    """Get the SkillHub installation guide for AI agents.

    This endpoint serves the install.md guide which contains
    instructions for AI agents to install the SkillHub CLI tool.

    The guide includes:
    - Step-by-step installation instructions
    - Complete installation script
    - Usage examples
    - Environment variable configuration
    - Troubleshooting tips

    Returns:
        Markdown installation guide

    Example:
        curl http://localhost:8000/api/v1/script/install -o install.md
        cat install.md
    """
    install_path = os.path.join(SCRIPT_DIR, "install.md")

    try:
        with open(install_path, 'r', encoding='utf-8') as f:
            install_content = f.read()

        # Replace the default SKILLHUB_URL in the script
        install_content = install_content.replace(
            "{SKILLHUB_URL}",
            settings.SKILLHUB_URL
        )
        return Response(
            content=install_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": 'attachment; filename="install.md"'
            }
        )
    except FileNotFoundError:
        return Response(
            content="Install guide not found",
            status_code=404,
            media_type="text/plain"
        )
