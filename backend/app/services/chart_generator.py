"""
图表生成服务（协调阿里百炼和Pyecharts）
"""
from typing import Dict, Any, Optional
from loguru import logger
import pandas as pd
from app.services.bailian_service import BailianService
from app.services.pyecharts_generator import PyechartsGenerator
from app.services.code_executor import CodeExecutor


class ChartGenerator:
    """图表生成服务（协调阿里百炼和Pyecharts）"""
    
    def __init__(self):
        self.bailian_service = BailianService()
        self.pyecharts_generator = PyechartsGenerator()
        self.code_executor = CodeExecutor()
    
    async def generate_charts_from_excel(
        self,
        file_path: str,
        analysis_request: str,
        generate_type: str = "json",  # "html"（新）或 "json"（推荐）或 "code"
        chart_customization: Optional[str] = None  # 用户自定义prompt（用于HTML生成）
    ) -> Dict[str, Any]:
        """
        从Excel生成图表（完整流程）
        
        Args:
            file_path: Excel文件路径
            analysis_request: 分析需求
            generate_type: 生成类型 "html"（新）、"json"（推荐）或 "code"
            chart_customization: 图表定制化 prompt（用于HTML生成）
        
        Returns:
            {
                "success": bool,
                "html_content": str,  # HTML模式时返回HTML代码
                "charts": list,  # JSON/代码模式时返回图表配置列表
                "data_summary": dict,  # 数据摘要
                "error": str
            }
        """
        try:
            if generate_type == "html":
                # 新方式：生成HTML代码
                logger.info(f"[ChartGenerator] 调用阿里百炼API生成HTML代码 - has_customization={bool(chart_customization)}")
                html_result = await self.bailian_service.analyze_excel_and_generate_html(
                    file_path=file_path,
                    analysis_request=analysis_request,
                    chart_customization=chart_customization
                )
                
                if not html_result["success"]:
                    return {
                        "success": False,
                        "html_content": None,
                        "charts": [],
                        "data_summary": {},
                        "error": f"HTML生成失败: {html_result['error']}"
                    }
                
                html_content = html_result["html_content"]
                
                # 读取数据摘要
                df = pd.read_excel(file_path)
                data_summary = {
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                    "categorical_columns": df.select_dtypes(include=['object']).columns.tolist()
                }
                
                return {
                    "success": True,
                    "html_content": html_content,
                    "charts": [],  # HTML模式下，charts为空
                    "data_summary": data_summary,
                    "error": None
                }
            
            # 原有方式：生成JSON配置或代码
            # 1. 调用阿里百炼API生成配置
            logger.info(f"[ChartGenerator] 调用阿里百炼API生成配置 - type={generate_type}")
            config_result = await self.bailian_service.analyze_excel_and_generate_chart_config(
                file_path=file_path,
                analysis_request=analysis_request,
                generate_type=generate_type
            )
            
            if not config_result["success"]:
                return {
                    "success": False,
                    "charts": [],
                    "data_summary": {},
                    "error": f"配置生成失败: {config_result['error']}"
                }
            
            # 2. 读取真实数据
            df = pd.read_excel(file_path)
            
            # 3. 根据生成类型处理
            if generate_type == "json":
                # 方案A：JSON配置（推荐）
                chart_configs = config_result["config"]
                charts = self.pyecharts_generator.generate_charts_from_config(df, chart_configs)
                
                # 提取数据摘要
                data_summary = {
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                    "categorical_columns": df.select_dtypes(include=['object']).columns.tolist()
                }
            
            else:
                # 方案B：Python代码（备选）
                code = config_result["config"]
                logger.info(f"[ChartGenerator] 执行生成的代码")
                exec_result = self.code_executor.execute_chart_code(
                    code=code,
                    file_path=file_path
                )
                
                if not exec_result["success"]:
                    return {
                        "success": False,
                        "charts": [],
                        "data_summary": {},
                        "error": f"代码执行失败: {exec_result['error']}"
                    }
                
                result = exec_result["result"]
                charts = result.get("charts", [])
                data_summary = result.get("data_summary", {})
            
            # 4. 验证图表配置
            validated_charts = []
            for chart in charts:
                if self._validate_chart_config(chart):
                    validated_charts.append(chart)
                else:
                    logger.warning(f"[ChartGenerator] 跳过无效图表配置")
            
            return {
                "success": True,
                "html_content": None,  # JSON/代码模式下，html_content为空
                "charts": validated_charts,
                "data_summary": data_summary,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"[ChartGenerator] 生成图表失败: {str(e)}")
            return {
                "success": False,
                "html_content": None,
                "charts": [],
                "data_summary": {},
                "error": str(e)
            }
    
    def _validate_chart_config(self, chart: Dict[str, Any]) -> bool:
        """验证图表配置"""
        required_fields = ["type", "config"]
        
        for field in required_fields:
            if field not in chart:
                return False
        
        # 验证类型
        valid_types = ["line", "bar", "pie", "scatter", "area", "radar"]
        if chart["type"] not in valid_types:
            return False
        
        # 验证config是字典
        if not isinstance(chart["config"], dict):
            return False
        
        return True

