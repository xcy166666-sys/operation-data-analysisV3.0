"""测试图表生成功能"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.chart_generator import ChartGenerator
from app.core.config import settings
from loguru import logger

async def test_chart_generation():
    """测试图表生成"""
    print("=" * 60)
    print("图表生成功能测试")
    print("=" * 60)
    
    print(f"\n1. API配置:")
    print(f"   API Key: {settings.DASHSCOPE_API_KEY[:25] if settings.DASHSCOPE_API_KEY else '未配置'}...")
    print(f"   Model: {settings.DASHSCOPE_MODEL}")
    print(f"   API Base: {settings.DASHSCOPE_API_BASE or '使用DashScope默认'}")
    
    # 查找测试文件
    upload_dir = Path("uploads/operation/project_1")
    test_file = None
    
    if upload_dir.exists():
        for f in upload_dir.iterdir():
            if f.is_file() and f.suffix in ['.xlsx', '.xls']:
                test_file = f
                break
    
    if not test_file:
        print("\n❌ 未找到测试Excel文件")
        print("   请先上传一个Excel文件")
        return
    
    print(f"\n2. 测试文件: {test_file}")
    
    print("\n3. 开始测试图表生成...")
    
    try:
        chart_generator = ChartGenerator()
        
        result = await chart_generator.generate_charts_from_excel(
            file_path=str(test_file),
            analysis_request="分析数据趋势，生成折线图",
            generate_type="json"
        )
        
        print(f"\n4. 测试结果:")
        print(f"   成功: {result.get('success')}")
        print(f"   图表数量: {len(result.get('charts', []))}")
        print(f"   错误: {result.get('error') or '无'}")
        
        if result.get('success'):
            print("\n✅ 图表生成成功！")
            for i, chart in enumerate(result.get('charts', []), 1):
                print(f"   图表 {i}: {chart.get('type')} - {chart.get('title')}")
        else:
            print("\n❌ 图表生成失败")
            print(f"   错误信息: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chart_generation())

