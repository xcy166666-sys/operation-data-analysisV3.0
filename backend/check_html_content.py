#!/usr/bin/env python3
"""检查数据库中的HTML图表内容"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/operation_analysis")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def check_html_content(session_id: int = 24):
    """检查指定会话的HTML内容"""
    db = SessionLocal()
    try:
        # 直接查询数据库
        result = db.execute(
            text(f"SELECT messages FROM analysis_sessions WHERE id = {session_id}")
        ).fetchone()
        
        if not result:
            print(f"未找到会话 ID: {session_id}")
            return
        
        messages = result[0]
        if not messages:
            print("会话没有消息")
            return
        
        print(f"=== 会话 {session_id} 的消息 ===")
        print(f"消息数量: {len(messages)}")
        
        for i, msg in enumerate(messages):
            print(f"\n--- 消息 {i+1} ---")
            print(f"角色: {msg.get('role')}")
            
            if msg.get('role') == 'assistant':
                # 检查html_charts
                html_charts = msg.get('html_charts')
                if html_charts:
                    print(f"\n✓ 找到 html_charts")
                    print(f"长度: {len(html_charts)} 字符")
                    print(f"\n=== 完整HTML内容 ===")
                    print(html_charts)
                    print(f"\n=== 内容分析 ===")
                    
                    # 检查是否包含实际的图表代码
                    if 'echarts' in html_charts.lower():
                        print("✓ 包含 ECharts 代码")
                    else:
                        print("✗ 不包含 ECharts 代码")
                    
                    if 'option' in html_charts.lower():
                        print("✓ 包含 option 配置")
                    else:
                        print("✗ 不包含 option 配置")
                    
                    if 'series' in html_charts.lower():
                        print("✓ 包含 series 数据")
                    else:
                        print("✗ 不包含 series 数据")
                    
                    if 'setoption' in html_charts.lower():
                        print("✓ 包含 setOption 调用")
                    else:
                        print("✗ 不包含 setOption 调用")
                else:
                    print("\n✗ 没有 html_charts")
                
                # 检查content
                content = msg.get('content')
                if content:
                    print(f"\n内容长度: {len(content)} 字符")
                    print(f"内容预览: {content[:200]}...")
    
    finally:
        db.close()

if __name__ == "__main__":
    session_id = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    check_html_content(session_id)
