"""测试 tmpkey 认证功能.

这个测试脚本演示了如何使用 tmpkey 进行 API 认证。
"""
import sys
sys.path.insert(0, '~/Documents/workspace/skillhub/backend')

from core.tmpkey_manager import (
    generate_tmpkey,
    store_tmpkey,
    get_user_id_by_tmpkey,
    remove_tmpkey,
    cleanup_expired_tmpkeys,
    get_tmpkey_count
)


def test_tmpkey_basic():
    """测试 tmpkey 基本功能."""
    print("=== TmpKey 基本功能测试 ===\n")

    # 1. 生成 tmpkey
    print("1. 生成 tmpkey:")
    tmpkey = generate_tmpkey()
    print(f"   生成的 tmpkey: {tmpkey}")
    print(f"   长度: {len(tmpkey)} 字符")
    assert len(tmpkey) == 32, "Tmpkey 长度应该是 32"
    print("   ✓ 长度正确\n")

    # 2. 存储 tmpkey
    print("2. 存储 tmpkey:")
    user_id = "test-user-123"
    store_tmpkey(tmpkey, user_id)
    print(f"   存储: tmpkey='{tmpkey}' -> user_id='{user_id}'")
    print(f"   当前存储数量: {get_tmpkey_count()}")
    print("   ✓ 存储成功\n")

    # 3. 查询 tmpkey
    print("3. 通过 tmpkey 查询 user_id:")
    retrieved_user_id = get_user_id_by_tmpkey(tmpkey)
    print(f"   查询结果: {retrieved_user_id}")
    assert retrieved_user_id == user_id, "User ID 应该匹配"
    print("   ✓ 查询成功\n")

    # 4. 删除 tmpkey
    print("4. 删除 tmpkey:")
    result = remove_tmpkey(tmpkey)
    print(f"   删除结果: {result}")
    assert result == True, "删除应该成功"
    print("   ✓ 删除成功\n")

    # 5. 验证删除后查询失败
    print("5. 验证删除后查询:")
    retrieved_user_id = get_user_id_by_tmpkey(tmpkey)
    print(f"   查询结果: {retrieved_user_id}")
    assert retrieved_user_id is None, "删除后应该查询不到"
    print("   ✓ 查询返回 None（正确）\n")


def test_tmpkey_expiration():
    """测试 tmpkey 过期功能."""
    print("=== TmpKey 过期功能测试 ===\n")

    # 1. 创建一个即将过期的 tmpkey（1秒后过期）
    print("1. 创建即将过期的 tmpkey:")
    tmpkey = generate_tmpkey()
    user_id = "test-user-456"
    store_tmpkey(tmpkey, user_id, expire_seconds=1)
    print(f"   存储: tmpkey='{tmpkey}' (1秒后过期)")
    print("   ✓ 存储成功\n")

    # 2. 立即查询（应该成功）
    print("2. 立即查询:")
    retrieved_user_id = get_user_id_by_tmpkey(tmpkey)
    print(f"   查询结果: {retrieved_user_id}")
    assert retrieved_user_id == user_id, "应该能查询到"
    print("   ✓ 查询成功\n")

    # 3. 等待2秒后查询（应该失败）
    print("3. 等待2秒后查询:")
    import time
    time.sleep(2)
    retrieved_user_id = get_user_id_by_tmpkey(tmpkey)
    print(f"   查询结果: {retrieved_user_id}")
    assert retrieved_user_id is None, "过期后应该查询不到"
    print("   ✓ 查询返回 None（已过期，正确）\n")


def test_multiple_tmpkeys():
    """测试多个 tmpkey."""
    print("=== 多个 TmpKey 测试 ===\n")

    # 创建多个 tmpkey
    print("1. 创建多个 tmpkey:")
    tmpkeys = []
    for i in range(5):
        tmpkey = generate_tmpkey()
        user_id = f"user-{i}"
        store_tmpkey(tmpkey, user_id)
        tmpkeys.append((tmpkey, user_id))
        print(f"   {i+1}. tmpkey={tmpkey[:8]}... -> user_id={user_id}")

    print(f"   当前存储数量: {get_tmpkey_count()}")
    print("   ✓ 存储成功\n")

    # 查询所有 tmpkey
    print("2. 查询所有 tmpkey:")
    for tmpkey, expected_user_id in tmpkeys:
        retrieved_user_id = get_user_id_by_tmpkey(tmpkey)
        assert retrieved_user_id == expected_user_id, f"User ID 不匹配: {retrieved_user_id} != {expected_user_id}"
        print(f"   ✓ tmpkey={tmpkey[:8]}... -> {retrieved_user_id}")

    print()


def test_cleanup_expired():
    """测试清理过期 tmpkey."""
    print("=== 清理过期 TmpKey 测试 ===\n")

    # 1. 创建一些 tmpkey（部分过期）
    print("1. 创建 tmpkey（部分将过期）:")
    import time

    # 创建3个正常的 tmpkey
    for i in range(3):
        tmpkey = generate_tmpkey()
        store_tmpkey(tmpkey, f"user-normal-{i}", expire_seconds=60)
        print(f"   正常: {tmpkey[:8]}...")

    # 创建2个即将过期的 tmpkey
    expired_tmpkeys = []
    for i in range(2):
        tmpkey = generate_tmpkey()
        store_tmpkey(tmpkey, f"user-expired-{i}", expire_seconds=1)
        expired_tmpkeys.append(tmpkey)
        print(f"   即将过期: {tmpkey[:8]}...")

    print(f"\n   存储数量: {get_tmpkey_count()}")
    print("   ✓ 存储成功\n")

    # 2. 等待过期
    print("2. 等待2秒让部分 tmpkey 过期:")
    time.sleep(2)
    print("   ✓ 等待完成\n")

    # 3. 清理过期 tmpkey
    print("3. 清理过期的 tmpkey:")
    cleaned_count = cleanup_expired_tmpkeys()
    print(f"   清理数量: {cleaned_count}")
    print(f"   剩余数量: {get_tmpkey_count()}")
    assert cleaned_count == 2, "应该清理2个过期的 tmpkey"
    print("   ✓ 清理成功\n")

    # 4. 验证过期的 tmpkey 已删除
    print("4. 验证过期的 tmpkey 已删除:")
    for tmpkey in expired_tmpkeys:
        user_id = get_user_id_by_tmpkey(tmpkey)
        assert user_id is None, "过期的 tmpkey 应该已被删除"
        print(f"   ✓ {tmpkey[:8]}... 已删除")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TmpKey 认证功能测试")
    print("="*60 + "\n")

    try:
        test_tmpkey_basic()
        test_tmpkey_expiration()
        test_multiple_tmpkeys()
        test_cleanup_expired()

        print("="*60)
        print("所有测试通过! ✓")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
