"""
ECharts解析工具
"""
import json
import re
from typing import List, Tuple
from loguru import logger


def parse_echarts_from_text(text: str) -> Tuple[str, List[dict]]:
    """
    从文本中提取echarts代码块并解析为图表配置
    
    Args:
        text: 包含```echarts代码块的文本
        
    Returns:
        Tuple[清理后的文本, charts配置列表]
    """
    if not text:
        return text, []
    
    charts = []
    # 匹配 ```echarts 代码块（支持多行JSON）
    # 模式：```echarts 开头（可选空格），然后是JSON内容，最后是 ```
    # 支持多种格式：```echarts\n...\n``` 或 ```echarts ... ```
    pattern = r'```echarts\s*\n?(.*?)\n?```'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    
    logger.info(f"[ECharts解析] 检测到 {len(matches)} 个echarts代码块")
    
    for idx, match in enumerate(matches):
        try:
            # 清理匹配到的内容（去除首尾空白）
            chart_json = match.strip()
            # 解析JSON
            chart_config = json.loads(chart_json)
            charts.append({
                "config": chart_config,
                "index": idx
            })
            logger.info(f"[ECharts解析] 成功解析第 {idx + 1} 个echarts配置")
        except json.JSONDecodeError as e:
            logger.warning(f"[ECharts解析] 第 {idx + 1} 个echarts代码块JSON解析失败: {e}")
            logger.debug(f"[ECharts解析] 失败的JSON内容: {chart_json[:200]}")
            continue
        except Exception as e:
            logger.error(f"[ECharts解析] 解析echarts代码块异常: {e}")
            continue
    
    # 移除代码块，保留纯文本（可选：也可以保留代码块作为说明）
    cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
    
    return cleaned_text, charts

