"""
批量分析核心逻辑（简化版，移除项目依赖）
"""
import asyncio
import base64
import json
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models.batch_analysis import BatchAnalysisSession, SheetReport
from app.services.chart_generator import ChartGenerator
from app.services.report_merger import ReportMerger
from app.services.bailian_service import BailianService, FIXED_TEXT_REPORT_PROMPT

# 固定项目ID（单项目系统）
DEFAULT_PROJECT_ID = 1


async def process_sheet_analysis(
    sheet_report_id: int,
    split_file_path: str,
    sheet_name: str,
    analysis_request: str,
    batch_session_id: int,
    user_id: int,
    db: Session,
    chart_customization_prompt: Optional[str] = None,
    chart_generation_mode: str = "html"
) -> dict:
    """
    处理单个Sheet的分析任务（简化版，移除project_id参数）
    使用阿里百炼生成文字报告和HTML图表
    """
    try:
        # 1. 更新报告状态为 generating
        sheet_report = db.query(SheetReport).filter(SheetReport.id == sheet_report_id).first()
        if not sheet_report:
            raise Exception(f"Sheet报告不存在: {sheet_report_id}")
        
        sheet_report.report_status = "generating"
        db.commit()
        logger.info(f"[批量分析] Sheet {sheet_name} 开始分析 - report_id={sheet_report_id}")
        
        # 2. 验证文件路径
        file_path_obj = Path(split_file_path)
        
        # 如果路径是相对路径，尝试多种格式
        if not file_path_obj.exists():
            if '\\' in str(split_file_path):
                alt_path = Path(split_file_path.replace('\\', '/'))
                if alt_path.exists():
                    file_path_obj = alt_path
                    logger.info(f"[批量分析] 使用替代路径格式: {alt_path}")
        
        # 检查文件是否存在
        if not file_path_obj.exists():
            error_msg = f"拆分后的文件不存在: {split_file_path}"
            logger.error(f"[批量分析] {error_msg}")
            raise FileNotFoundError(error_msg)
        
        # 验证文件可读
        try:
            file_size = file_path_obj.stat().st_size
            if file_size == 0:
                raise Exception(f"文件大小为0: {split_file_path}")
            logger.info(f"[批量分析] 文件验证通过 - 路径: {file_path_obj}, 大小: {file_size} bytes")
        except Exception as e:
            logger.error(f"[批量分析] 文件验证失败: {str(e)}")
            raise
        
        # 3. 并行处理：图表生成（阿里百炼API）和文字生成（阿里百炼API）
        chart_generator = ChartGenerator()
        bailian_service = BailianService()
        report_merger = ReportMerger()
        
        # 任务1：生成图表（阿里百炼API + HTML）
        async def generate_charts():
            # 合并分析需求和图表定制 prompt（用于HTML生成）
            chart_prompt = analysis_request
            if chart_customization_prompt:
                chart_prompt = f"{analysis_request}\n\n图表定制要求：\n{chart_customization_prompt}"
            
            return await chart_generator.generate_charts_from_excel(
                file_path=str(file_path_obj),
                analysis_request=chart_prompt,
                generate_type=chart_generation_mode,  # "html" 或 "json"
                chart_customization=chart_customization_prompt if chart_customization_prompt else None
            )
        
        # 任务2：生成文字（阿里百炼API - 改用阿里大模型）
        async def generate_text():
            logger.info(f"[批量分析] 调用阿里百炼API生成文字报告 - file_path={file_path_obj}")
            
            text_result = await bailian_service.analyze_excel_and_generate_text_report(
                file_path=str(file_path_obj),
                user_prompt=analysis_request,  # 用户输入的分析需求
                fixed_prompt_template=FIXED_TEXT_REPORT_PROMPT  # 固定prompt模板
            )
            
            if not text_result.get("success"):
                error_msg = text_result.get("error", "文字报告生成失败")
                logger.error(f"[批量分析] 文字报告生成失败 - {error_msg}")
                return f"文字生成失败：{error_msg}"
            
            text_content = text_result.get("text_content", "")
            
            if not isinstance(text_content, str):
                logger.error(f"[批量分析] text_content 不是字符串，类型: {type(text_content)}")
                return str(text_content) if text_content else "报告生成失败"
            
            logger.info(f"[批量分析] 文字报告生成成功 - 长度: {len(text_content)}")
            return text_content
        
        # 并行执行
        charts_task = generate_charts()
        text_task = generate_text()
        
        charts_result, report_text = await asyncio.gather(
            charts_task,
            text_task,
            return_exceptions=True
        )
        
        # 处理异常
        if isinstance(charts_result, Exception):
            logger.error(f"[批量分析] 图表生成异常: {charts_result}")
            charts_result = {"success": False, "charts": [], "data_summary": {}, "error": str(charts_result)}
        
        if isinstance(report_text, Exception):
            logger.error(f"[批量分析] 文字生成异常: {report_text}")
            report_text = "报告生成失败，请重试。"
        
        # 确保 report_text 是字符串
        if not isinstance(report_text, str):
            logger.error(f"[批量分析] report_text 不是字符串，类型: {type(report_text)}, 值: {report_text}")
            report_text = str(report_text) if report_text else "报告生成失败，请重试。"
        
        # 5. 合并报告
        if isinstance(charts_result, dict) and charts_result.get("success"):
            charts = charts_result.get("charts", []) if chart_generation_mode == "json" else []
            html_charts = charts_result.get("html_content") if chart_generation_mode == "html" else None
            data_summary = charts_result.get("data_summary", {})
        else:
            charts = []
            html_charts = None
            data_summary = {}
            logger.warning(f"[批量分析] 图表生成失败: {charts_result.get('error') if isinstance(charts_result, dict) else str(charts_result)}")
        
        # 再次确保 report_text 是字符串
        final_text = report_text if isinstance(report_text, str) else str(report_text) if report_text else "报告生成失败"
        logger.info(f"[批量分析] 最终文字内容类型: {type(final_text)}, 长度: {len(final_text)}")
        
        # 合并报告内容
        report_content = report_merger.merge_report(
            text_content=final_text,
            charts=charts,
            data_summary=data_summary,
            html_charts=html_charts
        )
        
        # 6. 更新报告内容和状态为 completed
        sheet_report.report_content = report_content
        sheet_report.report_status = "completed"
        db.commit()
        
        logger.info(f"[批量分析] Sheet {sheet_name} 分析完成 - text_length={len(final_text)}, html_charts_length={len(html_charts) if html_charts else 0}, charts_count={len(charts)}")
        return report_content
        
    except Exception as e:
        logger.error(f"[批量分析] Sheet {sheet_name} 分析失败: {str(e)}", exc_info=True)
        # 更新报告状态为 failed，记录错误信息
        sheet_report = db.query(SheetReport).filter(SheetReport.id == sheet_report_id).first()
        if sheet_report:
            sheet_report.report_status = "failed"
            sheet_report.error_message = str(e)
            db.commit()
        raise


async def process_all_sheets_concurrently(
    sheet_reports: List[SheetReport],
    analysis_request: str,
    user_id: int,
    batch_session_id: int,
    db: Session,
    chart_customization_prompt: Optional[str] = None,
    chart_generation_mode: str = "html"
) -> List[dict]:
    """
    并发处理所有Sheet的分析任务（简化版，移除project_id参数）
    """
    tasks = []
    for sheet_report in sheet_reports:
        # 为每个Sheet创建分析任务
        task = process_sheet_analysis(
            sheet_report_id=sheet_report.id,
            split_file_path=sheet_report.split_file_path,
            sheet_name=sheet_report.sheet_name,
            analysis_request=analysis_request,
            batch_session_id=batch_session_id,
            user_id=user_id,
            db=db,
            chart_customization_prompt=chart_customization_prompt,
            chart_generation_mode=chart_generation_mode
        )
        tasks.append(task)
    
    # 并发执行，但限制并发数（避免对阿里百炼API造成压力）
    semaphore = asyncio.Semaphore(3)  # 最多3个并发
    
    async def bounded_task(task):
        async with semaphore:
            try:
                return await task
            except Exception as e:
                logger.error(f"[批量分析] Sheet分析任务失败: {str(e)}")
                return None
    
    # 使用 gather 并发执行，即使某个失败也不影响其他
    results = await asyncio.gather(*[bounded_task(task) for task in tasks], return_exceptions=True)
    
    # 统计成功和失败数量
    success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
    failed_count = len(results) - success_count
    
    logger.info(f"[批量分析] 完成 - 成功: {success_count}, 失败: {failed_count}")
    return results

