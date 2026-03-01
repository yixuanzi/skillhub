"""测试 ext_config 中 token 占位符替换功能.

这个测试验证了在调用资源时，ext_config 中的 {key} 占位符
能够正确地从用户的 mtoken 中查找并替换为实际的 token 值。
"""
import sys
sys.path.insert(0, '.')

import pytest
from sqlalchemy.orm import Session
from services.gateway_service import GatewayService
from services.mtoken_service import MTokenService
from models.mtoken import MToken
from schemas.mtoken import MTokenCreate
from models.user import User
import uuid


def test_simple_string_replacement(db: Session):
    """测试简单的字符串替换."""
    # 创建测试用户
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"user_{unique_id}",
        email=f"user_{unique_id}@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(user)
    db.commit()

    # 创建 mtoken
    mtoken = MTokenCreate(
        app_name="github_token",
        key_name="Production Token",
        value="ghp_1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        desc="GitHub token for production"
    )
    MTokenService.create(db, mtoken, user.id)

    # 测试配置替换
    config = {
        "headers": {
            "Authorization": "Bearer {github_token}"
        },
        "timeout": 30
    }

    result = GatewayService._replace_token_placeholders(db, str(user.id), config)

    # 验证替换结果
    assert result["headers"]["Authorization"] == "Bearer ghp_1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert result["timeout"] == 30  # 非字符串值保持不变
    print("✅ 简单字符串替换测试通过")


def test_multiple_placeholders_in_one_string(db: Session):
    """测试一个字符串中的多个占位符."""
    # 创建测试用户
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"user_{unique_id}",
        email=f"user_{unique_id}@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(user)
    db.commit()

    # 创建多个 mtokens
    MTokenService.create(db, MTokenCreate(
        app_name="api_key",
        key_name="OpenAI Key",
        value="sk-1234567890",
        desc="OpenAI API key"
    ), user.id)
    MTokenService.create(db, MTokenCreate(
        app_name="secret_token",
        key_name="Slack Secret",
        value="xoxb-9876543210",
        desc="Slack bot token"
    ), user.id)

    # 测试多个占位符
    config = {
        "headers": {
            "X-API-Key": "{api_key}",
            "X-Secret": "{secret_token}"
        }
    }

    result = GatewayService._replace_token_placeholders(db, str(user.id), config)

    # 验证所有占位符都被替换
    assert result["headers"]["X-API-Key"] == "sk-1234567890"
    assert result["headers"]["X-Secret"] == "xoxb-9876543210"

    print("✅ 多占位符替换测试通过")


def test_nested_dict_replacement(db: Session):
    """测试嵌套字典的替换."""
    # 创建测试用户
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"user_{unique_id}",
        email=f"user_{unique_id}@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(user)
    db.commit()

    # 创建 mtoken
    MTokenService.create(db, MTokenCreate(
        app_name="auth_header",
        key_name="API Auth",
        value="Bearer xyz789",
        desc="Auth header value"
    ), user.id)

    # 测试嵌套配置
    config = {
        "auth": {
            "header": "{auth_header}",
            "type": "Bearer"
        },
        "timeout": 30
    }

    result = GatewayService._replace_token_placeholders(db, str(user.id), config)

    # 验证嵌套字典中的占位符被替换
    assert result["auth"]["header"] == "Bearer xyz789"
    assert result["auth"]["type"] == "Bearer"  # 非字符串值保持不变
    assert result["timeout"] == 30

    print("✅ 嵌套字典替换测试通过")


def test_placeholder_not_found(db: Session):
    """测试占位符找不到时的行为."""
    # 创建测试用户
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"user_{unique_id}",
        email=f"user_{unique_id}@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(user)
    db.commit()

    # 配置中包含不存在的占位符
    config = {
        "api_key": "{nonexistent_token}",
        "valid_key": "static_value"
    }

    result = GatewayService._replace_token_placeholders(db, str(user.id), config)

    # 不存在的占位符应该保持原样
    assert result["api_key"] == "{nonexistent_token}"
    # 没有占位符的值保持不变
    assert result["valid_key"] == "static_value"

    print("✅ 占位符未找到测试通过")


def test_complex_nested_structure(db: Session):
    """测试复杂的嵌套结构."""
    # 创建测试用户
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"user_{unique_id}",
        email=f"user_{unique_id}@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(user)
    db.commit()

    # 创建多个 mtokens
    MTokenService.create(db, MTokenCreate(
        app_name="main_token",
        key_name="Primary",
        value="token_abc",
        desc="Main token"
    ), user.id)
    MTokenService.create(db, MTokenCreate(
        app_name="backup_token",
        key_name="Backup",
        value="token_xyz",
        desc="Backup token"
    ), user.id)

    # 复杂嵌套配置
    config = {
        "options": {
            "primary": "{main_token}",
            "secondary": ["{backup_token}", "static_value"],
            "nested": {
                "deep": "{main_token}"
            }
        },
        "metadata": {
            "app": "myapp",
            "version": "1.0"
        }
    }

    result = GatewayService._replace_token_placeholders(db, str(user.id), config)

    # 验证所有层级的替换
    assert result["options"]["primary"] == "token_abc"
    assert result["options"]["secondary"][0] == "token_xyz"
    assert result["options"]["secondary"][1] == "static_value"
    assert result["options"]["nested"]["deep"] == "token_abc"
    assert result["metadata"]["app"] == "myapp"  # 非字符串值保持不变

    print("✅ 复杂嵌套结构测试通过")


def test_empty_and_none_values(db: Session):
    """测试空值和 None 的处理."""
    # 创建测试用户
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"user_{unique_id}",
        email=f"user_{unique_id}@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(user)
    db.commit()

    # 测试各种边界情况
    config = {
        "empty_string": "",
        "null_value": None,
        "normal_string": "no placeholder",
        "dict_empty": {},
        "list_empty": []
    }

    result = GatewayService._replace_token_placeholders(db, str(user.id), config)

    # 验证边界情况
    assert result["empty_string"] == ""
    assert result["null_value"] is None
    assert result["normal_string"] == "no placeholder"
    assert result["dict_empty"] == {}
    assert result["list_empty"] == []

    print("✅ 空值和 None 处理测试通过")


if __name__ == "__main__":
    """运行所有测试."""
    from database import init_db
    from core.deps import get_db

    print("\n" + "="*60)
    print("Token 占位符替换功能测试")
    print("="*60 + "\n")

    # 初始化数据库
    print("初始化数据库...")
    init_db()
    print("✅ 数据库初始化完成\n")

    # 获取数据库 session
    db = next(get_db())

    try:
        print("开始测试...\n")
        test_simple_string_replacement(db)
        test_multiple_placeholders_in_one_string(db)
        test_nested_dict_replacement(db)
        test_placeholder_not_found(db)
        test_complex_nested_structure(db)
        test_empty_and_none_values(db)

        print("\n" + "="*60)
        print("所有测试通过！✅")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
