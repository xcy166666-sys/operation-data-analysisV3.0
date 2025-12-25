"""
测试阿里百炼API服务
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.bailian_service import BailianService
from loguru import logger


async def test_bailian_service():
    """测试阿里百炼服务"""
    logger.info("开始测试阿里百炼API服务...")
    
    service = BailianService()
    
    # 检查配置
    if not service.api_key:
        logger.error("DASHSCOPE_API_KEY未配置，请在.env文件中配置")
        return
    
    logger.info(f"API密钥已配置: {service.api_key[:10]}...")
    logger.info(f"使用模型: {service.model}")
    
    # 这里需要一个测试Excel文件
    # 如果没有，可以创建一个简单的测试
    test_file_path = "test.xlsx"
    
    if not Path(test_file_path).exists():
        logger.warning(f"测试文件不存在: {test_file_path}")
        logger.info("请创建一个测试Excel文件，或修改test_file_path变量")
        return
    
    try:
        # 测试JSON配置生成
        logger.info("测试JSON配置生成...")
        result = await service.analyze_excel_and_generate_chart_config(
            file_path=test_file_path,
            analysis_request="分析数据趋势，生成折线图",
            generate_type="json"
        )
        
        if result["success"]:
            logger.success(f"测试成功！生成配置数量: {len(result['config'])}")
            logger.info(f"配置内容: {result['config']}")
        else:
            logger.error(f"测试失败: {result['error']}")
    
    except Exception as e:
        logger.error(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bailian_service())

