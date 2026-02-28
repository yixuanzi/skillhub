import pytest
from models.user import User, Role, Permission, RefreshToken
from models.skill import Skill, SkillVersion, SkillType, SkillRuntime, SkillStatus
from models.acl import ACLRule, ACLRuleRole, AuditLog, AccessMode, AuditResult
from database import SessionLocal

@pytest.fixture(scope="function")
def db():
    db = SessionLocal()
    try:
        yield db
        db.rollback()  # Rollback after each test
    finally:
        db.close()

@pytest.fixture(autouse=True)
def cleanup_db(db):
    """Auto-use fixture to clean up database before each test"""
    # Clean up all data before each test (in order of dependencies)
    db.query(AuditLog).delete()
    db.query(ACLRuleRole).delete()
    db.query(ACLRule).delete()
    db.query(SkillVersion).delete()
    db.query(Skill).delete()
    db.query(RefreshToken).delete()
    db.query(User).delete()
    db.query(Permission).delete()
    db.query(Role).delete()
    db.commit()
    yield
    # Cleanup happens in db fixture's rollback

def test_create_user(db):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_here"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_active is True

def test_create_role_with_permissions(db):
    role = Role(name="admin", description="Administrator")
    perm1 = Permission(resource="skills", action="read")
    perm2 = Permission(resource="skills", action="write")

    role.permissions.extend([perm1, perm2])
    db.add(role)
    db.commit()
    db.refresh(role)

    assert len(role.permissions) == 2
    assert "read" in [p.action for p in role.permissions]
    assert "write" in [p.action for p in role.permissions]

def test_user_role_relationship(db):
    # Create role and permissions
    role = Role(name="editor", description="Content editor")
    perm = Permission(resource="skills", action="write")
    role.permissions.append(perm)
    db.add(role)
    db.commit()

    # Create user
    user = User(
        username="editoruser",
        email="editor@example.com",
        hashed_password="hashed_password"
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)

    assert len(user.roles) == 1
    assert user.roles[0].name == "editor"

def test_refresh_token(db):
    # Create user first
    user = User(
        username="tokenuser",
        email="token@example.com",
        hashed_password="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create refresh token
    from datetime import datetime, timedelta, timezone
    token = RefreshToken(
        token_hash="hashed_token_value",
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    assert token.id is not None
    assert token.user_id == user.id
    assert token.user.id == user.id


# ============ SKILL MODEL TESTS ============

def test_create_skill(db):
    """Test creating a skill with valid data."""
    # Create a user first
    user = User(
        username="skilluser",
        email="skill@example.com",
        hashed_password="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create skill
    skill = Skill(
        name="test-skill",
        description="A test skill",
        skill_type=SkillType.BUSINESS_LOGIC,
        runtime=SkillRuntime.NODEJS,
        created_by=user.id
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)

    assert skill.id is not None
    assert skill.name == "test-skill"
    assert skill.skill_type == SkillType.BUSINESS_LOGIC
    assert skill.runtime == SkillRuntime.NODEJS
    assert skill.created_by == user.id


def test_skill_with_multiple_versions(db):
    """Test skill with multiple versions."""
    # Create user and skill
    user = User(
        username="versionuser",
        email="version@example.com",
        hashed_password="hashed_password"
    )
    db.add(user)
    db.commit()

    skill = Skill(
        name="versioned-skill",
        description="A skill with versions",
        skill_type=SkillType.API_PROXY,
        runtime=SkillRuntime.PYTHON,
        created_by=user.id
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)

    # Create multiple versions
    version1 = SkillVersion(
        skill_id=skill.id,
        version="1.0.0",
        status=SkillStatus.PUBLISHED,
        artifact_path="/artifacts/v1.0.0.zip"
    )
    version2 = SkillVersion(
        skill_id=skill.id,
        version="2.0.0",
        status=SkillStatus.BUILDING,
        artifact_path="/artifacts/v2.0.0.zip"
    )
    db.add_all([version1, version2])
    db.commit()
    db.refresh(skill)

    assert len(skill.versions) == 2
    assert skill.versions[0].version == "1.0.0"
    assert skill.versions[1].version == "2.0.0"


def test_skill_version_relationship(db):
    """Test bidirectional relationship between skill and versions."""
    user = User(
        username="reluser",
        email="rel@example.com",
        hashed_password="hashed_password"
    )
    db.add(user)
    db.commit()

    skill = Skill(
        name="relation-skill",
        description="Testing relationships",
        skill_type=SkillType.AI_LLM,
        runtime=SkillRuntime.GO,
        created_by=user.id
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)

    version = SkillVersion(
        skill_id=skill.id,
        version="1.0.0",
        status=SkillStatus.SUCCESS,
        build_log="Build completed successfully"
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    assert version.skill.id == skill.id
    assert version.skill.name == "relation-skill"


def test_skill_cascade_delete(db):
    """Test that deleting a skill cascades to its versions."""
    user = User(
        username="cascadeuser",
        email="cascade@example.com",
        hashed_password="hashed_password"
    )
    db.add(user)
    db.commit()

    skill = Skill(
        name="cascade-skill",
        description="Testing cascade delete",
        skill_type=SkillType.DATA_PROCESSING,
        runtime=SkillRuntime.PYTHON,
        created_by=user.id
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)

    version = SkillVersion(
        skill_id=skill.id,
        version="1.0.0",
        status=SkillStatus.PUBLISHED
    )
    db.add(version)
    db.commit()

    # Count versions before delete
    version_count = db.query(SkillVersion).filter_by(skill_id=skill.id).count()
    assert version_count == 1

    # Delete skill
    db.delete(skill)
    db.commit()

    # Verify versions are deleted
    version_count_after = db.query(SkillVersion).filter_by(skill_id=skill.id).count()
    assert version_count_after == 0


# ============ ACL MODEL TESTS ============

def test_create_acl_rule_any_mode(db):
    """Test creating an ACL rule with public access mode."""
    rule = ACLRule(
        resource_id="skill-public-123",
        resource_name="Public API Endpoint",
        access_mode=AccessMode.ANY,
        conditions={"rate_limit": 100}
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    assert rule.id is not None
    assert rule.access_mode == AccessMode.ANY
    assert rule.conditions["rate_limit"] == 100


def test_create_acl_rule_rbac_mode(db):
    """Test creating an ACL rule with RBAC mode."""
    # Create role
    role = Role(name="skill_admin", description="Skill administrator")
    db.add(role)
    db.commit()

    rule = ACLRule(
        resource_id="skill-private-456",
        resource_name="Private API Endpoint",
        access_mode=AccessMode.RBAC,
        conditions={"ip_whitelist": ["10.0.0.0/8"]}
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Add role binding
    rule_binding = ACLRuleRole(
        acl_rule_id=rule.id,
        role_id=role.id,
        permissions=["read", "write", "execute"]
    )
    db.add(rule_binding)
    db.commit()
    db.refresh(rule)

    assert len(rule.role_bindings) == 1
    assert rule.role_bindings[0].permissions == ["read", "write", "execute"]


def test_acl_rule_with_multiple_roles(db):
    """Test ACL rule with multiple role bindings."""
    # Create roles
    admin_role = Role(name="admin", description="Administrator")
    viewer_role = Role(name="viewer", description="Read-only access")
    db.add_all([admin_role, viewer_role])
    db.commit()

    rule = ACLRule(
        resource_id="skill-multi-789",
        resource_name="Multi-role Endpoint",
        access_mode=AccessMode.RBAC
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Add multiple role bindings
    binding1 = ACLRuleRole(
        acl_rule_id=rule.id,
        role_id=admin_role.id,
        permissions=["read", "write", "delete"]
    )
    binding2 = ACLRuleRole(
        acl_rule_id=rule.id,
        role_id=viewer_role.id,
        permissions=["read"]
    )
    db.add_all([binding1, binding2])
    db.commit()
    db.refresh(rule)

    assert len(rule.role_bindings) == 2
    admin_perms = [b.permissions for b in rule.role_bindings if b.role_id == admin_role.id][0]
    viewer_perms = [b.permissions for b in rule.role_bindings if b.role_id == viewer_role.id][0]
    assert "delete" in admin_perms
    assert "delete" not in viewer_perms


def test_audit_log_creation(db):
    """Test creating audit logs."""
    # Create user and ACL rule
    user = User(
        username="audituser",
        email="audit@example.com",
        hashed_password="hashed_password"
    )
    db.add(user)
    db.commit()

    rule = ACLRule(
        resource_id="skill-audit-001",
        resource_name="Audited Endpoint",
        access_mode=AccessMode.RBAC
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Create audit log
    audit_log = AuditLog(
        user_id=user.id,
        username=user.username,
        resource_id=rule.resource_id,
        acl_rule_id=rule.id,
        access_mode=AccessMode.RBAC,
        result=AuditResult.ALLOWED,
        ip_address="192.168.1.100",
        request_id="req-abc-123",
        details={"method": "GET", "path": "/api/v1/skills/1"}
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    assert audit_log.id is not None
    assert audit_log.result == AuditResult.ALLOWED
    assert audit_log.username == "audituser"
    assert audit_log.acl_rule_id == rule.id


def test_audit_log_for_anonymous_access(db):
    """Test audit log for anonymous (unauthenticated) access."""
    rule = ACLRule(
        resource_id="skill-public-002",
        resource_name="Public Endpoint",
        access_mode=AccessMode.ANY
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Create audit log without user info
    audit_log = AuditLog(
        resource_id=rule.resource_id,
        acl_rule_id=rule.id,
        access_mode=AccessMode.ANY,
        result=AuditResult.DENIED,
        ip_address="10.0.0.50",
        request_id="req-def-456",
        details={"reason": "rate_limit_exceeded"}
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    assert audit_log.user_id is None
    assert audit_log.username is None
    assert audit_log.result == AuditResult.DENIED


def test_acl_rule_with_audit_logs(db):
    """Test relationship between ACL rule and audit logs."""
    rule = ACLRule(
        resource_id="skill-audit-003",
        resource_name="Heavily Audited Endpoint",
        access_mode=AccessMode.RBAC
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Create multiple audit logs
    log1 = AuditLog(
        resource_id=rule.resource_id,
        acl_rule_id=rule.id,
        access_mode=AccessMode.RBAC,
        result=AuditResult.ALLOWED,
        ip_address="192.168.1.1"
    )
    log2 = AuditLog(
        resource_id=rule.resource_id,
        acl_rule_id=rule.id,
        access_mode=AccessMode.RBAC,
        result=AuditResult.DENIED,
        ip_address="192.168.1.2"
    )
    db.add_all([log1, log2])
    db.commit()
    db.refresh(rule)

    assert len(rule.audit_logs) == 2
    allowed_count = sum(1 for log in rule.audit_logs if log.result == AuditResult.ALLOWED)
    denied_count = sum(1 for log in rule.audit_logs if log.result == AuditResult.DENIED)
    assert allowed_count == 1
    assert denied_count == 1


def test_acl_rule_role_cascade_delete(db):
    """Test that deleting an ACL rule cascades to role bindings."""
    role = Role(name="test_role", description="Test role")
    db.add(role)
    db.commit()

    rule = ACLRule(
        resource_id="skill-cascade-001",
        resource_name="Cascade Test",
        access_mode=AccessMode.RBAC
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    binding = ACLRuleRole(
        acl_rule_id=rule.id,
        role_id=role.id,
        permissions=["read"]
    )
    db.add(binding)
    db.commit()

    # Count bindings before delete
    binding_count = db.query(ACLRuleRole).filter_by(acl_rule_id=rule.id).count()
    assert binding_count == 1

    # Delete rule
    db.delete(rule)
    db.commit()

    # Verify bindings are deleted
    binding_count_after = db.query(ACLRuleRole).filter_by(acl_rule_id=rule.id).count()
    assert binding_count_after == 0

