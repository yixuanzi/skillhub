"""Resource ACL service for managing access control rules.

This module provides the business logic layer for resource ACL operations,
including creation, retrieval, update, deletion, and permission checking.

Security Policy:
- ACL write operations (create/update/delete) are restricted to:
    * Resource owner
    * Users with 'admin' or 'super_admin' role
- ACL read operations return rules for resources user has access to
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from models.acl import ACLRule, ACLRuleRole, AccessMode
from models.resource import Resource
from models.user import Role, User
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

# Admin role names
ADMIN_ROLES = {"admin", "super_admin"}


def _is_admin_user(user: Optional[User]) -> bool:
    """Check if user has admin or super_admin role.

    Args:
        user: User object with roles relationship

    Returns:
        True if user has admin or super_admin role
    """
    if not user or not user.roles:
        return False
    user_role_names = {role.name for role in user.roles}
    return bool(user_role_names & ADMIN_ROLES)


def _check_acl_permission(db: Session, resource_id: str, user: Optional[User]) -> bool:
    """Check if user has permission to modify ACL rules for a resource.

    A user can modify ACL rules if:
    - The user is an admin (has admin or super_admin role)
    - The user is the resource owner

    Args:
        db: Database session
        resource_id: Resource UUID
        user: User object to check permission for

    Returns:
        True if user has permission

    Raises:
        ValidationException: If user lacks permission
        NotFoundException: If resource is not found
    """
    # Get resource with owner info
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise NotFoundException(f"Resource with id '{resource_id}' not found")

    # Admin users can modify any ACL
    if _is_admin_user(user):
        return True

    # Owner can modify their resource's ACL
    if user and resource.owner_id == user.id:
        return True

    raise ValidationException("You do not have permission to modify ACL rules for this resource")


class ACLResourceService:
    """Service class for resource ACL management operations."""

    @staticmethod
    def create(db: Session, acl_data: ACLRuleCreate, user: Optional[User] = None) -> ACLRuleResponse:
        """Create a new ACL rule for a resource.

        Only the resource owner or admin users can create ACL rules.

        Args:
            db: Database session
            acl_data: ACL rule creation data
            user: User object for permission check

        Returns:
            Created ACL rule response

        Raises:
            NotFoundException: If resource or role not found
            ValidationException: If validation fails or user lacks permission
        """
        # Check permission - only resource owner or admin can create ACL rules
        _check_acl_permission(db, acl_data.resource_id, user)

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
    def list_accessible(
        db: Session,
        user: Optional[User],
        skip: int = 0,
        limit: int = 100,
        access_mode: Optional[AccessMode] = None
    ) -> tuple[List[ACLRuleResponse], int]:
        """List ACL rules for resources the user has been granted access to.

        - Admin users can see all ACL rules
        - Regular users can only see ACL rules for resources where:
            * access_mode = ANY (public access)
            * access_mode = RBAC AND user is in the authorized users/roles list

        This implementation uses SQLite JSON functions for efficient filtering.

        Args:
            db: Database session
            user: User object to check permissions for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            access_mode: Optional access mode filter

        Returns:
            Tuple of (list of accessible ACL rule responses, total count)
        """
        from sqlalchemy import func, or_, and_

        # Admin users can see all ACL rules
        if _is_admin_user(user):
            query = db.query(ACLRule).options(
                joinedload(ACLRule.role_bindings)
            )
            if access_mode:
                query = query.filter(ACLRule.access_mode == access_mode)

            total = query.count()
            acl_rules = query.offset(skip).limit(limit).all()
            return [ACLResourceService._to_response(db, rule) for rule in acl_rules], total

        # Regular users: filter using SQLite JSON functions
        # Build filter for authorized access:
        # 1. access_mode = 'any' OR
        # 2. (access_mode = 'rbac' AND
        #    (conditions->>'$.users' LIKE '%username%' OR
        #     json_each(conditions, '$.roles') value = user_role_id))

        # Get user's role IDs
        user_role_ids = [str(role.id) for role in user.roles] if user.roles else []
        username_literal = user.username.replace("'", "''")  # Escape single quotes

        # Build the JSON filter conditions
        # ANY mode: always accessible
        any_mode_filter = ACLRule.access_mode == AccessMode.ANY

        # RBAC mode: check if user is in conditions.users OR conditions.roles
        # Using json_extract to check arrays
        rbac_user_filter = and_(
            ACLRule.access_mode == AccessMode.RBAC,
            or_(
                # Check if username is in conditions.users array
                func.json_extract(ACLRule.conditions, '$.users').like(f'%{username_literal}%'),
                # Check if any of user's roles are in conditions.roles array
                *[func.json_extract(ACLRule.conditions, '$.roles').like(f'%{role_id}%')
                 for role_id in user_role_ids]
            )
        )

        query = db.query(ACLRule).options(
            joinedload(ACLRule.role_bindings)
        ).filter(
            or_(any_mode_filter, rbac_user_filter)
        )

        if access_mode:
            query = query.filter(ACLRule.access_mode == access_mode)

        total = query.count()
        acl_rules = query.offset(skip).limit(limit).all()

        return [ACLResourceService._to_response(db, rule) for rule in acl_rules], total

    @staticmethod
    def _user_has_acl_access(db: Session, acl_rule: ACLRule, user: User) -> bool:
        """Check if user has been granted access via ACL rule.

        Args:
            db: Database session
            acl_rule: ACL rule to check
            user: User object to check access for

        Returns:
            True if user has access via this ACL rule
        """
        # ANY mode means public access
        if acl_rule.access_mode == AccessMode.ANY:
            return True

        # RBAC mode - check user permissions
        if acl_rule.access_mode == AccessMode.RBAC:
            # Check conditions - user whitelist
            if acl_rule.conditions:
                conditions = acl_rule.conditions
                if "users" in conditions and conditions["users"]:
                    if user.username in conditions["users"]:
                        return True

                # Check conditions - role whitelist
                if "roles" in conditions and conditions["roles"]:
                    user_role_ids = [str(role.id) for role in user.roles] if user.roles else []
                    if any(role_id in conditions["roles"] for role_id in user_role_ids):
                        return True

        return False

    @staticmethod
    def get_by_id_for_user(db: Session, acl_rule_id: str, user: User) -> ACLRuleResponse:
        """Get ACL rule by ID with permission check.

        - Admin users can get any ACL rule
        - Regular users can only get ACL rules where they have been granted access

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            user: User object for permission check

        Returns:
            ACL rule response

        Raises:
            NotFoundException: If ACL rule not found
            ValidationException: If user lacks permission
        """
        acl_rule = db.query(ACLRule).options(
            joinedload(ACLRule.role_bindings)
        ).filter(ACLRule.id == acl_rule_id).first()

        if not acl_rule:
            raise NotFoundException(f"ACL rule with id '{acl_rule_id}' not found")

        # Admin users can access any ACL rule
        if _is_admin_user(user):
            return ACLResourceService._to_response(db, acl_rule)

        # Regular users can only access if granted by ACL
        if not ACLResourceService._user_has_acl_access(db, acl_rule, user):
            raise ValidationException("You do not have permission to access this ACL rule")

        return ACLResourceService._to_response(db, acl_rule)

    @staticmethod
    def get_by_resource_id_for_user(db: Session, resource_id: str, user: User) -> ACLRuleResponse:
        """Get ACL rule by resource ID with permission check.

        - Admin users can get any ACL rule
        - Regular users can only get ACL rules where they have been granted access

        Args:
            db: Database session
            resource_id: Resource UUID
            user: User object for permission check

        Returns:
            ACL rule response

        Raises:
            NotFoundException: If ACL rule not found
            ValidationException: If user lacks permission
        """
        acl_rule = db.query(ACLRule).options(
            joinedload(ACLRule.role_bindings)
        ).filter(ACLRule.resource_id == resource_id).first()

        if not acl_rule:
            raise NotFoundException(f"ACL rule for resource '{resource_id}' not found")

        # Admin users can access any ACL rule
        if _is_admin_user(user):
            return ACLResourceService._to_response(db, acl_rule)

        # Regular users can only access if granted by ACL
        if not ACLResourceService._user_has_acl_access(db, acl_rule, user):
            raise ValidationException("You do not have permission to access this ACL rule")

        return ACLResourceService._to_response(db, acl_rule)

    @staticmethod
    def update(db: Session, acl_rule_id: str, acl_data: ACLRuleUpdate, user: Optional[User] = None) -> ACLRuleResponse:
        """Update an existing ACL rule.

        Only the resource owner or admin users can update ACL rules.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            acl_data: ACL rule update data
            user: User object for permission check

        Returns:
            Updated ACL rule response

        Raises:
            NotFoundException: If ACL rule not found
            ValidationException: If user lacks permission
        """
        acl_rule = db.query(ACLRule).filter(ACLRule.id == acl_rule_id).first()
        if not acl_rule:
            raise NotFoundException(f"ACL rule with id '{acl_rule_id}' not found")

        # Check permission - only resource owner or admin can update ACL rules
        _check_acl_permission(db, acl_rule.resource_id, user)

        # Update fields
        if acl_data.access_mode is not None:
            acl_rule.access_mode = acl_data.access_mode

        if acl_data.conditions is not None:
            acl_rule.conditions = acl_data.conditions.model_dump(exclude_none=True)

        db.commit()
        db.refresh(acl_rule)

        return ACLResourceService._to_response(db, acl_rule)

    @staticmethod
    def delete(db: Session, acl_rule_id: str, user: Optional[User] = None) -> bool:
        """Delete an ACL rule.

        Only the resource owner or admin users can delete ACL rules.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            user: User object for permission check

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If ACL rule not found
            ValidationException: If user lacks permission
        """
        acl_rule = db.query(ACLRule).filter(ACLRule.id == acl_rule_id).first()
        if not acl_rule:
            raise NotFoundException(f"ACL rule with id '{acl_rule_id}' not found")

        # Check permission - only resource owner or admin can delete ACL rules
        _check_acl_permission(db, acl_rule.resource_id, user)

        db.delete(acl_rule)
        db.commit()

        return True

    @staticmethod
    def add_role_binding(
        db: Session,
        acl_rule_id: str,
        role_binding_data: RoleBindingCreate,
        user: Optional[User] = None
    ) -> RoleBindingResponse:
        """Add a role binding to an ACL rule.

        Only the resource owner or admin users can add role bindings.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            role_binding_data: Role binding data
            user: User object for permission check

        Returns:
            Created role binding response

        Raises:
            NotFoundException: If ACL rule or role not found
            ValidationException: If validation fails or user lacks permission
        """
        # Verify ACL rule exists
        acl_rule = db.query(ACLRule).filter(ACLRule.id == acl_rule_id).first()
        if not acl_rule:
            raise NotFoundException(f"ACL rule with id '{acl_rule_id}' not found")

        # Check permission - only resource owner or admin can modify ACL rules
        _check_acl_permission(db, acl_rule.resource_id, user)

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
    def remove_role_binding(db: Session, acl_rule_id: str, role_id: str, user: Optional[User] = None) -> bool:
        """Remove a role binding from an ACL rule.

        Only the resource owner or admin users can remove role bindings.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            role_id: Role UUID
            user: User object for permission check

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If role binding not found
            ValidationException: If user lacks permission
        """
        binding = db.query(ACLRuleRole).filter(
            ACLRuleRole.acl_rule_id == acl_rule_id,
            ACLRuleRole.role_id == role_id
        ).first()

        if not binding:
            raise NotFoundException(
                f"Role binding for role '{role_id}' not found in ACL rule '{acl_rule_id}'"
            )

        # Get ACL rule to check permission
        acl_rule = db.query(ACLRule).filter(ACLRule.id == acl_rule_id).first()
        if acl_rule:
            # Check permission - only resource owner or admin can modify ACL rules
            _check_acl_permission(db, acl_rule.resource_id, user)

        db.delete(binding)
        db.commit()

        return True

    @staticmethod
    def update_role_binding(
        db: Session,
        acl_rule_id: str,
        role_id: str,
        permissions: List[str],
        user: Optional[User] = None
    ) -> RoleBindingResponse:
        """Update permissions for a role binding.

        Only the resource owner or admin users can update role bindings.

        Args:
            db: Database session
            acl_rule_id: ACL rule UUID
            role_id: Role UUID
            permissions: New list of permissions
            user: User object for permission check

        Returns:
            Updated role binding response

        Raises:
            NotFoundException: If role binding not found
            ValidationException: If user lacks permission
        """
        binding = db.query(ACLRuleRole).filter(
            ACLRuleRole.acl_rule_id == acl_rule_id,
            ACLRuleRole.role_id == role_id
        ).first()

        if not binding:
            raise NotFoundException(
                f"Role binding for role '{role_id}' not found in ACL rule '{acl_rule_id}'"
            )

        # Get ACL rule to check permission
        acl_rule = db.query(ACLRule).filter(ACLRule.id == acl_rule_id).first()
        if acl_rule:
            # Check permission - only resource owner or admin can modify ACL rules
            _check_acl_permission(db, acl_rule.resource_id, user)

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
