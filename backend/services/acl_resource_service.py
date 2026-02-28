"""Resource ACL service for managing access control rules.

This module provides the business logic layer for resource ACL operations,
including creation, retrieval, update, deletion, and permission checking.
"""
from sqlalchemy.orm import Session, joinedload
from models.acl import ACLRule, ACLRuleRole, AccessMode
from models.resource import Resource
from models.user import Role
from schemas.acl_resource import (
    ACLRuleCreate,
    ACLRuleUpdate,
    ACLRuleResponse,
    RoleBindingCreate,
    RoleBindingResponse,
    ConditionSchema,
    PermissionCheckRequest,
    PermissionCheckResponse
)
from core.exceptions import ValidationException, NotFoundException
from typing import Optional, List, Dict, Any
import json


class ACLResourceService:
    """Service class for resource ACL management operations."""

    @staticmethod
    def create(db: Session, acl_data: ACLRuleCreate) -> ACLRuleResponse:
        """Create a new ACL rule for a resource.

        Args:
            db: Database session
            acl_data: ACL rule creation data

        Returns:
            Created ACL rule response

        Raises:
            NotFoundException: If resource or role not found
            ValidationException: If validation fails
        """
        # Verify resource exists
        resource = db.query(Resource).filter(Resource.id == acl_data.resource_id).first()
        if not resource:
            raise NotFoundException(f"Resource with id '{acl_data.resource_id}' not found")

        # Check if ACL rule already exists for this resource
        existing = db.query(ACLRule).filter(ACLRule.resource_id == acl_data.resource_id).first()
        if existing:
            raise ValidationException(f"ACL rule for resource '{acl_data.resource_id}' already exists")

        # Convert conditions to dict if present
        conditions_dict = None
        if acl_data.conditions:
            conditions_dict = acl_data.conditions.model_dump(exclude_none=True)

        # Create ACL rule
        new_acl_rule = ACLRule(
            resource_id=acl_data.resource_id,
            resource_name=acl_data.resource_name,
            access_mode=acl_data.access_mode,
            conditions=conditions_dict
        )

        db.add(new_acl_rule)
        db.flush()  # Get the ID before creating role bindings

        # Create role bindings if provided (for RBAC mode)
        if acl_data.role_bindings and acl_data.access_mode == AccessMode.RBAC:
            for binding_data in acl_data.role_bindings:
                # Verify role exists
                role = db.query(Role).filter(Role.id == binding_data.role_id).first()
                if not role:
                    raise NotFoundException(f"Role with id '{binding_data.role_id}' not found")

                role_binding = ACLRuleRole(
                    acl_rule_id=new_acl_rule.id,
                    role_id=binding_data.role_id,
                    permissions=binding_data.permissions
                )
                db.add(role_binding)

        db.commit()
        db.refresh(new_acl_rule)

        return ACLResourceService._to_response(db, new_acl_rule)

    @staticmethod
    def get_by_id(db: Session, acl_rule_id: str) -> Optional[ACLRuleResponse]:
        """Get ACL rule by ID.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID

        Returns:
            ACL rule response or None if not found
        """
        acl_rule = db.query(ACLRule).options(
            joinedload(ACLRule.role_bindings)
        ).filter(ACLRule.id == acl_rule_id).first()

        if not acl_rule:
            return None

        return ACLResourceService._to_response(db, acl_rule)

    @staticmethod
    def get_by_resource_id(db: Session, resource_id: str) -> Optional[ACLRuleResponse]:
        """Get ACL rule by resource ID.

        Args:
            db: Database session
            resource_id: Resource UUID

        Returns:
            ACL rule response or None if not found
        """
        acl_rule = db.query(ACLRule).options(
            joinedload(ACLRule.role_bindings)
        ).filter(ACLRule.resource_id == resource_id).first()

        if not acl_rule:
            return None

        return ACLResourceService._to_response(db, acl_rule)

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[ACLRuleResponse]:
        """List all ACL rules with pagination.

        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of ACL rule responses
        """
        acl_rules = db.query(ACLRule).options(
            joinedload(ACLRule.role_bindings)
        ).offset(skip).limit(limit).all()

        return [ACLResourceService._to_response(db, rule) for rule in acl_rules]

    @staticmethod
    def list_by_mode(db: Session, access_mode: AccessMode, skip: int = 0, limit: int = 100) -> List[ACLRuleResponse]:
        """List ACL rules by access mode.

        Args:
            db: Database session
            access_mode: Access mode to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of filtered ACL rule responses
        """
        acl_rules = db.query(ACLRule).filter(
            ACLRule.access_mode == access_mode
        ).options(
            joinedload(ACLRule.role_bindings)
        ).offset(skip).limit(limit).all()

        return [ACLResourceService._to_response(db, rule) for rule in acl_rules]

    @staticmethod
    def count_all(db: Session) -> int:
        """Count total number of ACL rules."""
        return db.query(ACLRule).count()

    @staticmethod
    def count_by_mode(db: Session, access_mode: AccessMode) -> int:
        """Count ACL rules by access mode."""
        return db.query(ACLRule).filter(ACLRule.access_mode == access_mode).count()

    @staticmethod
    def update(db: Session, acl_rule_id: str, acl_data: ACLRuleUpdate) -> ACLRuleResponse:
        """Update an existing ACL rule.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            acl_data: ACL rule update data

        Returns:
            Updated ACL rule response

        Raises:
            NotFoundException: If ACL rule not found
        """
        acl_rule = db.query(ACLRule).filter(ACLRule.id == acl_rule_id).first()
        if not acl_rule:
            raise NotFoundException(f"ACL rule with id '{acl_rule_id}' not found")

        # Update fields
        if acl_data.access_mode is not None:
            acl_rule.access_mode = acl_data.access_mode

        if acl_data.conditions is not None:
            acl_rule.conditions = acl_data.conditions.model_dump(exclude_none=True)

        db.commit()
        db.refresh(acl_rule)

        return ACLResourceService._to_response(db, acl_rule)

    @staticmethod
    def delete(db: Session, acl_rule_id: str) -> bool:
        """Delete an ACL rule.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If ACL rule not found
        """
        acl_rule = db.query(ACLRule).filter(ACLRule.id == acl_rule_id).first()
        if not acl_rule:
            raise NotFoundException(f"ACL rule with id '{acl_rule_id}' not found")

        db.delete(acl_rule)
        db.commit()

        return True

    @staticmethod
    def add_role_binding(
        db: Session,
        acl_rule_id: str,
        role_binding_data: RoleBindingCreate
    ) -> RoleBindingResponse:
        """Add a role binding to an ACL rule.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            role_binding_data: Role binding data

        Returns:
            Created role binding response

        Raises:
            NotFoundException: If ACL rule or role not found
            ValidationException: If role binding already exists
        """
        # Verify ACL rule exists
        acl_rule = db.query(ACLRule).filter(ACLRule.id == acl_rule_id).first()
        if not acl_rule:
            raise NotFoundException(f"ACL rule with id '{acl_rule_id}' not found")

        # Verify role exists
        role = db.query(Role).filter(Role.id == role_binding_data.role_id).first()
        if not role:
            raise NotFoundException(f"Role with id '{role_binding_data.role_id}' not found")

        # Check if role binding already exists
        existing = db.query(ACLRuleRole).filter(
            ACLRuleRole.acl_rule_id == acl_rule_id,
            ACLRuleRole.role_id == role_binding_data.role_id
        ).first()
        if existing:
            raise ValidationException(
                f"Role binding for role '{role_binding_data.role_id}' already exists"
            )

        # Create role binding
        new_binding = ACLRuleRole(
            acl_rule_id=acl_rule_id,
            role_id=role_binding_data.role_id,
            permissions=role_binding_data.permissions
        )

        db.add(new_binding)
        db.commit()
        db.refresh(new_binding)

        return ACLResourceService._to_binding_response(new_binding, role.name)

    @staticmethod
    def remove_role_binding(db: Session, acl_rule_id: str, role_id: str) -> bool:
        """Remove a role binding from an ACL rule.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            role_id: Role UUID

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If role binding not found
        """
        binding = db.query(ACLRuleRole).filter(
            ACLRuleRole.acl_rule_id == acl_rule_id,
            ACLRuleRole.role_id == role_id
        ).first()

        if not binding:
            raise NotFoundException(
                f"Role binding for role '{role_id}' not found in ACL rule '{acl_rule_id}'"
            )

        db.delete(binding)
        db.commit()

        return True

    @staticmethod
    def update_role_binding(
        db: Session,
        acl_rule_id: str,
        role_id: str,
        permissions: List[str]
    ) -> RoleBindingResponse:
        """Update permissions for a role binding.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            role_id: Role UUID
            permissions: New list of permissions

        Returns:
            Updated role binding response

        Raises:
            NotFoundException: If role binding not found
        """
        binding = db.query(ACLRuleRole).filter(
            ACLRuleRole.acl_rule_id == acl_rule_id,
            ACLRuleRole.role_id == role_id
        ).first()

        if not binding:
            raise NotFoundException(
                f"Role binding for role '{role_id}' not found in ACL rule '{acl_rule_id}'"
            )

        binding.permissions = permissions
        db.commit()
        db.refresh(binding)

        role = db.query(Role).filter(Role.id == role_id).first()
        role_name = role.name if role else None

        return ACLResourceService._to_binding_response(binding, role_name)

    @staticmethod
    def check_permission(
        db: Session,
        resource_id: str,
        current_user
    ) -> PermissionCheckResponse:
        """Check if a user has permission to access a resource.

        Args:
            db: Database session
            resource_id: Resource UUID
            check_data: Permission check request data

        Returns:
            Permission check response with allowed/rejected decision

        Raises:
            NotFoundException: If ACL rule or resource not found
        """
        # Get ACL rule for resource
        #db.query(Resource).filter(Resource.name == resource_name).first()
        acl_rule = db.query(ACLRule).options(
             joinedload(ACLRule.role_bindings)
        ).filter(ACLRule.resource_id == resource_id).first()

        if not acl_rule:
            # No ACL rule means no access
            return PermissionCheckResponse(
                allowed=False,
                reason="No ACL rule found for resource",
                access_mode="none"
            )

        # Check access mode
        if acl_rule.access_mode == AccessMode.ANY:
            return PermissionCheckResponse(
                allowed=True,
                reason="Public access (any mode)",
                access_mode="any"
            )

        # RBAC mode - check user permissions
        if acl_rule.access_mode == AccessMode.RBAC:
            # Get user's roles
            from models.user import User
            user = db.query(User).options(
                joinedload(User.roles)
            ).filter(User.id == current_user.id).first()

            if not user:
                return PermissionCheckResponse(
                    allowed=False,
                    reason="User not found",
                    access_mode="rbac"
                )

            # Check conditions - user whitelist
            if acl_rule.conditions:
                conditions = acl_rule.conditions
                if "users" in conditions and conditions["users"]:
                    if current_user.username in conditions["users"]:
                        return PermissionCheckResponse(
                            allowed=True,
                            reason="User in whitelist",
                            access_mode="rbac",
                            matched_conditions={"users": current_user.username}
                        )

                # Check conditions - role whitelist
                if "roles" in conditions and conditions["roles"]:
                    user_role_ids = [str(role.id) for role in user.roles]
                    if any(role_id in conditions["roles"] for role_id in user_role_ids):
                        return PermissionCheckResponse(
                            allowed=True,
                            reason="User's role in whitelist",
                            access_mode="rbac",
                            matched_conditions={"roles": list(set(user_role_ids) & set(conditions["roles"]))}
                        )



            return PermissionCheckResponse(
                allowed=False,
                reason=f"Permission '{current_user.username}' not granted",
                access_mode="rbac"
            )

        return PermissionCheckResponse(
            allowed=False,
            reason="Unknown access mode",
            access_mode="unknown"
        )

    @staticmethod
    def _to_response(db: Session, acl_rule: ACLRule) -> ACLRuleResponse:
        """Convert ACLRule model to response schema."""
        role_bindings = []
        for binding in acl_rule.role_bindings:
            role = db.query(Role).filter(Role.id == binding.role_id).first()
            role_bindings.append(ACLResourceService._to_binding_response(binding, role.name if role else None))

        return ACLRuleResponse(
            id=acl_rule.id,
            resource_id=acl_rule.resource_id,
            resource_name=acl_rule.resource_name,
            access_mode=acl_rule.access_mode,
            conditions=acl_rule.conditions,
            created_at=acl_rule.created_at,
            role_bindings=role_bindings
        )

    @staticmethod
    def _to_binding_response(binding: ACLRuleRole, role_name: Optional[str] = None) -> RoleBindingResponse:
        """Convert ACLRuleRole model to response schema."""
        return RoleBindingResponse(
            id=binding.id,
            role_id=binding.role_id,
            role_name=role_name,
            permissions=binding.permissions,
            created_at=binding.created_at
        )
