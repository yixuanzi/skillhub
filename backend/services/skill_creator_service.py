"""Skill Creator service for generating skill content.

This module provides the business logic for generating skill content based on
resources (base mode) or existing skills (sop mode).

Security Policy:
- All resources and skills referenced must be accessible to the user
- Resource access follows standard ACL rules (public, owner, admin, ACL-granted)
"""
import os
from sqlalchemy.orm import Session
from models.resource import Resource, ResourceType
from models.skill_list import SkillList
from models.user import User
from schemas.skill_creator import SkillCreatorRequest, SkillCreatorResponse, SkillCreatorType
from core.exceptions import ValidationException, NotFoundException
from typing import List, Tuple
import json
import anyio
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions,AssistantMessage,ResultMessage,TextBlock,ToolUseBlock

def display_message(message) -> None:
    """显示 Agent 返回的消息

    Args:
        message: Agent SDK 返回的消息对象
    """
    # 处理助手消息
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                pass
                #print(block.text)
            elif isinstance(block, ToolUseBlock):
                # 显示工具调用（可选，用于调试）
                # print(f"[工具调用: {block.name}]")
                pass

    # 处理最终结果消息
    elif isinstance(message, ResultMessage):
        if message.result:
            #print(f"\n{message.result}")
            return message.result
        # 可选：显示成本信息
        if message.total_cost_usd and message.total_cost_usd > 0:
            pass
            #print(f"\n[成本: ${message.total_cost_usd:.4f}]")

class SkillCreatorService:
    """Service class for skill generation operations."""
    agent_cache={} # cache for agents

    @staticmethod
    async def _generate_skill_documentation(content: str,agentname:str) -> str:
        """Generate standardized SKILL.md documentation using Claude Agent SDK.

        Args:
            content: Resource/skill information as context

        Returns:
            Generated SKILL.md markdown content

        Raises:
            Exception: If Agent SDK call fails
        """
        # Read the agent system prompt
        try:
            if not SkillCreatorService.agent_cache.get(agentname,None):
                agent_prompt_path = Path(__file__).parent.parent / "scripts" / f"{agentname}.md"
                system_prompt = agent_prompt_path.read_text(encoding="utf-8")
                # Configure Agent options
                agent = ClaudeAgentOptions(
                        cwd=os.getcwd(),
                        allowed_tools=[], # 不使用任何工具
                        system_prompt=system_prompt
                    )
            else:
                agent = SkillCreatorService.agent_cache.get(agentname)
        except Exception as e:
            raise Exception(f"Failed to read agent prompt from {agent_prompt_path}: {e}")

        # Build user prompt with content context
        user_prompt = f"""
```
{content}
```

Generate the SKILL.md content following the format specified in your instructions and user require.(do not write the content to file)"""

        try:
            skill_doc = ""
            # Call Claude Agent SDK
            async for message in query(
                prompt=user_prompt,
                options=agent,
            ):
                if isinstance(message, (AssistantMessage, ResultMessage)):
                    finalrs=display_message(message)
                    if finalrs:
                        skill_doc += f"{finalrs}\n"

            return skill_doc

        except Exception as e:
            raise Exception(f"Failed to generate SKILL.md documentation: {e}")

    @staticmethod
    async def generate_content(
        db: Session,
        request: SkillCreatorRequest,
        user: User
    ) -> Tuple[str, str]:
        """Generate skill content based on request type.

        Args:
            db: Database session
            request: Skill creator request
            user: User object for access control

        Returns:
            Tuple of (content, skill) where:
            - content: Generated markdown content from resources/skills
            - skill: Generated standardized SKILL.md documentation

        Raises:
            ValidationException: If validation fails or access denied
            NotFoundException: If referenced resources/skills not found
        """
        try:
            if request.type == SkillCreatorType.BASE:
                context_conf = await SkillCreatorService._generate_from_resources(db, request, user)
                skill = await SkillCreatorService._generate_skill_documentation(f"<resource_list>{context_conf}</resource_list>","agent_res")
            else:
                context_conf = SkillCreatorService._generate_from_skills(db, request, user)
                skill = await SkillCreatorService._generate_skill_documentation(f"<skill_list>{context_conf}</skill_list><user_requirement>{request.userinput}</user_requirement>","agent_skill")

        except Exception as e:
            # If skill generation fails, return empty skill instead of failing
            skill = f"# SKILL.md Generation Failed\n\nError: {str(e)}\n\n## Raw Content\n\n{context_conf}"

        return skill, context_conf

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
        2. Each skill section separated by #-----------

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

        # Add referenced skills
        for skill_id in request.skill_id_list:
            skill = db.query(SkillList).filter(SkillList.id == skill_id).first()
            if not skill:
                raise NotFoundException(f"Skill with id '{skill_id}' not found")

            # Build skill section
            skill_part = f"name: {skill.name}\ndescription: {skill.description or ''}\n<skill_content>\n{skill.content or ''}</skill_content>\n"

            content_parts.append(skill_part)

        # Join with separator
        return "\n#-----------\n".join(content_parts)
