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
    script_path = os.path.join(SCRIPT_DIR, "skillhub.sh")

    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()

        # Get SKILLHUB_URL from environment variable
        skillhub_url = os.getenv('SKILLHUB_URL', 'http://localhost:8000')

        # Replace the default SKILLHUB_URL in the script
        script_content = script_content.replace(
            'SKILLHUB_URL="http://localhost:8000"',
            f'SKILLHUB_URL="{settings.SKILLHUB_URL}"'
        )

        return Response(
            content=script_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": 'attachment; filename="skillhub.sh"'
            }
        )
    except FileNotFoundError:
        return Response(
            content="Script file not found",
            status_code=404,
            media_type="text/plain"
        )
