"""
报告合并服务
"""
from typing import Dict, Any, List, Optional
from loguru import logger


class ReportMerger:
    """报告合并服务"""
    
    @staticmethod
    def merge_report(
        text_content: str,
        charts: List[Dict[str, Any]],
        data_summary: Dict[str, Any] = None,
        html_charts: Optional[str] = None  # 新增：HTML图表内容
    ) -> Dict[str, Any]:
        """
        合并文字和图表生成最终报告
        
        Args:
            text_content: Dify生成的文字内容
            charts: 图表配置列表（JSON方式，可选）
            data_summary: 数据摘要
            html_charts: HTML图表内容（新方式，可选）
        
        Returns:
            完整的报告内容
        """
        # 确保 text_content 是字符串
        if not isinstance(text_content, str):
            logger.error(f"[ReportMerger] text_content 不是字符串，类型: {type(text_content)}, 值: {text_content}")
            text_content = str(text_content) if text_content else "报告生成失败"
        
        # 检查是否包含无效的 Promise 字符串表示
        if "[object Promise]" in text_content or text_content == "[object Object]":
            logger.error(f"[ReportMerger] text_content 包含无效值: {text_content[:100]}")
            text_content = "报告内容加载异常，请重新生成"
        
        report_content = {
            "text": text_content,
            "charts": charts,  # JSON方式的图表（向后兼容）
            "html_charts": html_charts,  # HTML方式的图表（新）
            "tables": [],
            "metrics": {}
        }
        
        # 如果有数据摘要，添加到metrics中
        if data_summary:
            report_content["metrics"] = {
                "row_count": data_summary.get("row_count", 0),
                "column_count": data_summary.get("column_count", 0),
                "columns": data_summary.get("columns", []),
                "numeric_columns": data_summary.get("numeric_columns", []),
                "categorical_columns": data_summary.get("categorical_columns", [])
            }
        
        logger.info(f"[ReportMerger] 报告合并完成 - 文字长度: {len(text_content)}, 图表数: {len(charts)}")
        
        return report_content

