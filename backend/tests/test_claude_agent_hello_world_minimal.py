"""
Claude Agent SDK - 最简单的 Hello World 示例

这是最基本的示例，展示如何使用 claude_agent_sdk 进行查询。

使用方法：
python test_claude_agent_hello_world_minimal.py <your_api_key>
"""

import asyncio
import sys
import os

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
except ImportError:
    print("错误: 未找到 claude_agent_sdk 模块")
    print("\n请确保:")
    print("1. claude_agent_sdk 已安装")
    print("2. 或者设置了正确的 PYTHONPATH")
    sys.exit(1)


async def hello_world():
    """
    最简单的 Hello World 查询

    Args:
        api_key: Anthropic API Key
    """
    print("Claude Agent SDK - Hello World")
    print("=" * 40)

    # 配置选项（最小化配置）
    options = ClaudeAgentOptions(
        cwd=os.getcwd(),           # 当前工作目录
        allowed_tools=[],          # 不使用任何工具
    )

    # 用户查询
    prompt = "请说 'Hello, World!' 然后用一句话介绍你自己。"

    print(f"\n查询: {prompt}\n")
    print("-" * 40)
    print("响应:")

    # 发送查询并处理响应
    async for message in query(
        prompt=prompt,
        options=options
    ):
        # 处理消息内容
        if hasattr(message, 'content'):
            for block in message.content:
                # 只处理文本块
                if hasattr(block, 'text'):
                    print(block.text, end='', flush=True)

        # 显示成本（如果有）
        if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
            print(f"\n\n成本: ${message.total_cost_usd:.6f}")

    print("\n" + "=" * 40)


if __name__ == "__main__":
    # 运行异步函数
    asyncio.run(hello_world())
