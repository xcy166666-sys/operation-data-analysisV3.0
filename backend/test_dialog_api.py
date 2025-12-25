#!/usr/bin/env python3
"""
AI对话API测试脚本
"""
import asyncio
import json
from app.services.bailian_dialog_service import BailianDialogService
from app.services.dialog_manager import DialogManager


async def test_dialog_service():
    """测试对话服务"""
    print("🧪 测试AI对话服务...")

    # 初始化服务
    dialog_service = BailianDialogService()
    dialog_manager = DialogManager()

    try:
        # 测试对话处理
        print("\n1️⃣ 测试对话处理...")

        result = await dialog_service.process_dialog_message(
            session_id="test_session_001",
            user_message="把图表颜色改成红色",
            current_charts=[{
                "type": "bar",
                "title": "测试图表",
                "config": {
                    "color": ["#5470C6"],
                    "series": [{"type": "bar", "data": [1, 2, 3]}]
                }
            }],
            conversation_id=None
        )

        print("✅ 对话处理成功:")
        print(f"   回复: {result['response'][:100]}...")
        print(f"   动作类型: {result['action_type']}")
        print(f"   修改图表数量: {len(result['modified_charts'])}")

        # 测试对话历史管理
        print("\n2️⃣ 测试对话历史管理...")

        # 保存消息
        await dialog_manager.save_message("test_session_001", "user", "把图表颜色改成红色")
        await dialog_manager.save_message("test_session_001", "assistant", result["response"])

        # 获取历史
        history = await dialog_manager.get_conversation_history("test_session_001")
        print(f"✅ 历史记录数量: {len(history)}")

        # 获取会话状态
        state = await dialog_manager.get_session_state("test_session_001")
        print(f"✅ 会话状态: {state}")

        print("\n🎉 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_dialog_service())










