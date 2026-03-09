"""Skill Creator service for generating skill content.

This module provides the business logic for generating skill content based on
resources (base mode) or existing skills (sop mode).

Security Policy:
- All resources and skills referenced must be accessible to the user
- Resource access follows standard ACL rules (public, owner, admin, ACL-granted)
"""
from sqlalchemy.orm import Session
from models.resource import Resource, ResourceType
from models.skill_list import SkillList
from models.user import User
from schemas.skill_creator import SkillCreatorRequest, SkillCreatorResponse, SkillCreatorType
from core.exceptions import ValidationException, NotFoundException
from typing import List
import json


class SkillCreatorService:
    """Service class for skill generation operations."""

    @staticmethod
    async def generate_content(
        db: Session,
        request: SkillCreatorRequest,
        user: User
    ) -> str:
        """Generate skill content based on request type.

        Args:
            db: Database session
            request: Skill creator request
            user: User object for access control

        Returns:
            Generated markdown content

        Raises:
            ValidationException: If validation fails or access denied
            NotFoundException: If referenced resources/skills not found
        """
        if request.type == SkillCreatorType.BASE:
            return await SkillCreatorService._generate_from_resources(db, request, user)
        else:
            return SkillCreatorService._generate_from_skills(db, request, user)

    @staticmethod
    async def _generate_from_resources(
        db: Session,
        request: SkillCreatorRequest,
        user: User
    ) -> str:
        """Generate skill content from resource list (base mode).

        Format for each resource:
        name: resource.name
        desc: resource.desc
        type: resource.type
        url: resource.url
        method: resource.ext.method (if type is third_party)
        tools: [mcp tools] (if type is mcp)
        document: resource.api_description

        Args:
            db: Database session
            request: Skill creator request
            user: User object for access control

        Returns:
            Generated markdown content

        Raises:
            ValidationException: If access denied to any resource
            NotFoundException: If any resource not found
        """
        from services.resource_service import ResourceService
        from services.mcp_service import MCPService

        if not request.resource_id_list:
            raise ValidationException("resource_id_list is required for base mode")

        content_parts = []

        for resource_id in request.resource_id_list:
            # Get resource with access control
            resource = ResourceService.get_accessible(db, resource_id, user)

            # Build resource section
            resource_part = f"name: {resource.name}\ndesc: {resource.desc or ''}\ntype: {resource.type.value if hasattr(resource.type, 'value') else resource.type}"

            # Add method if available (for third_party type)
            if resource.ext and isinstance(resource.ext, dict):
                method = resource.ext.get('method')
                if method:
                    resource_part += f"\nmethod: {method}"

            # Add tools for MCP type resources
            if resource.type == ResourceType.MCP:
                try:
                    tools = await MCPService.list_tools(db=db, resource_name=resource.name)
                    if tools:
                        tools_json = json.dumps(tools, ensure_ascii=False, indent=2)
                        resource_part += f"\ntools: {tools_json}"
                except Exception as e:
                    # If MCP tools fetch fails, add a note instead of failing
                    resource_part += f"\ntools: # Unable to fetch MCP tools: {str(e)}"
                

            if resource.type != ResourceType.MCP:resource_part += f"url: {resource.url or ''}\n"
            # Add API description
            if resource.api_description:
                resource_part += f"\ndocument: {resource.api_description}"

            content_parts.append(resource_part)

        # Join with separator
        return "\n#-----------\n".join(content_parts)

    @staticmethod
    def _generate_from_skills(
        db: Session,
        request: SkillCreatorRequest,
        user: User
    ) -> str:
        """Generate SOP skill content from existing skill list (sop mode).

        Format:
        1. User requirements section (from userinput)
        2. Each skill section separated by -----------

        Format for each skill:
        name: skill.name
        description: skill.description
        content: skill.content

        Args:
            db: Database session
            request: Skill creator request
            user: User object for access control

        Returns:
            Generated markdown content

        Raises:
            ValidationException: If access denied to any skill
            NotFoundException: If any skill not found
        """
        if not request.skill_id_list:
            raise ValidationException("skill_id_list is required for sop mode")

        content_parts = []

        # Add user requirements section
        if request.userinput:
            content_parts.append(request.userinput)

        # Add referenced skills
        for skill_id in request.skill_id_list:
            skill = db.query(SkillList).filter(SkillList.id == skill_id).first()
            if not skill:
                raise NotFoundException(f"Skill with id '{skill_id}' not found")

            # Build skill section
            skill_part = f"name: {skill.name}\ndescription: {skill.description or ''}\ncontent: {skill.content or ''}"

            content_parts.append(skill_part)

        # Join with separator
        return "\n#-----------\n".join(content_parts)
