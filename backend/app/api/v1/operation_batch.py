"""
批量分析核心逻辑（简化版，移除项目依赖）
"""
import asyncio
import base64
import json
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session
from loguru import logger

from app.models.batch_analysis import BatchAnalysisSession, SheetReport
from app.services.workflow_service import WorkflowService
from app.services.dify_service import DifyService
from app.utils.echarts_parser import parse_echarts_from_text

# 固定项目ID（单项目系统）
DEFAULT_PROJECT_ID = 1


async def process_sheet_analysis(
    sheet_report_id: int,
    split_file_path: str,
    sheet_name: str,
    analysis_request: str,
    batch_session_id: int,
    user_id: int,
    db: Session
) -> dict:
    """
    处理单个Sheet的分析任务（简化版，移除project_id参数）
    复用现有的 generate_report 逻辑，直接调用Dify工作流
    """
    try:
        # 1. 更新报告状态为 generating
        sheet_report = db.query(SheetReport).filter(SheetReport.id == sheet_report_id).first()
        if not sheet_report:
            raise Exception(f"Sheet报告不存在: {sheet_report_id}")
        
        sheet_report.report_status = "generating"
        db.commit()
        logger.info(f"[批量分析] Sheet {sheet_name} 开始分析 - report_id={sheet_report_id}")
        
        # 2. 获取绑定的Dify工作流（优先使用用户配置）
        function_key = "operation_data_analysis"
        binding = WorkflowService.get_function_workflow(db, function_key, user_id)
        
        if not binding:
            raise Exception(f"尚未配置运营数据分析工作流")
        
        workflow = WorkflowService.get_workflow_by_id(db, binding.workflow_id)
        if not workflow or not workflow.is_active:
            raise Exception("工作流不存在或已禁用")
        
        if workflow.platform != "dify":
            raise Exception(f"当前工作流平台为 {workflow.platform}，仅支持 Dify 平台")
        
        workflow_config = workflow.config
        api_key = workflow_config.get("api_key")
        url_file = workflow_config.get("url_file")  # 文件上传URL
        url_work = workflow_config.get("url_work")  # 工作流URL
        file_param = workflow_config.get("file_param", "excell")  # 文件参数名
        query_param = workflow_config.get("query_param", "query")  # 对话参数名
        workflow_type = workflow_config.get("workflow_type", "chatflow")
        
        # 兼容旧配置格式
        if not url_file:
            api_url = workflow_config.get("api_url")
            if api_url:
                url_file = f"{api_url.rstrip('/')}/files/upload"
        if not url_work:
            api_url = workflow_config.get("api_url")
            if api_url:
                url_work = f"{api_url.rstrip('/')}/chat-messages"
        
        if not all([api_key, url_file, url_work]):
            raise Exception("工作流配置不完整，请检查API Key、文件上传URL和工作流URL")
        
        # 3. 生成Dify用户标识（移除project_id参数）
        dify_user = DifyService.generate_user_id(
            user_id=user_id,
            function_key=function_key,
            conversation_id=batch_session_id
        )
        
        # 4. 根据工作流类型处理文件
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
        
        if workflow_type == "chatflow":
            # Chatflow: 先上传文件到Dify
            logger.info(f"[批量分析] 准备上传文件到Dify - file_path={file_path_obj}, file_size={file_size} bytes, url={url_file}, user_id={dify_user}")
            
            upload_result = await DifyService.upload_file(
                api_url=url_file,  # 使用用户配置的文件上传URL
                api_key=api_key,
                file_path=str(file_path_obj),
                file_name=file_path_obj.name,
                user_id=dify_user
            )
            
            if not upload_result.get("success"):
                error_msg = upload_result.get('error', '未知错误')
                raise Exception(f"文件上传到Dify失败: {error_msg}")
            
            dify_file_id = upload_result.get("data", {}).get("id")
            if not dify_file_id:
                raise Exception("Dify文件上传成功但未返回文件ID")
            
            # 使用用户配置的参数名
            inputs = {
                file_param: dify_file_id,  # 文件参数名（用户配置）
                query_param: analysis_request,  # 对话参数名（用户配置）
            }
        else:
            # Workflow: 读取文件内容并转换为base64
            logger.info(f"[批量分析] 读取文件内容转换为base64 - file_path={file_path_obj}")
            
            with open(file_path_obj, "rb") as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                logger.info(f"[批量分析] 文件内容读取成功 - 大小: {len(file_content)} bytes")
            
            inputs = {
                file_param: file_base64,  # 文件参数名（用户配置）
                f"sys.{query_param}": analysis_request,  # 对话参数名（用户配置）
            }
        
        # 5. 调用Dify工作流（使用用户配置的URL）
        result = await DifyService.run_workflow(
            api_url=url_work,  # 使用用户配置的工作流URL
            api_key=api_key,
            workflow_id="1",  # 固定为1，实际使用url_work
            user_id=user_id,
            function_key=function_key,
            inputs=inputs,
            conversation_id=batch_session_id,
            response_mode="blocking",
            workflow_type=workflow_type
        )
        
        if not result.get("success"):
            raise Exception(f"Dify工作流执行失败: {result.get('error')}")
        
        # 6. 解析Dify返回的结果
        dify_data = result.get("data", {})
        
        if workflow_type == "chatflow":
            report_text = dify_data.get("answer", "") or dify_data.get("text", "")
            conversation_id = dify_data.get("conversation_id")
            if conversation_id:
                sheet_report.dify_conversation_id = str(conversation_id)
        else:
            workflow_output = dify_data.get("data", {}).get("outputs", {})
            report_text = workflow_output.get("text", "") or dify_data.get("text", "")
        
        # 7. 解析echarts代码块
        cleaned_text, charts = parse_echarts_from_text(report_text)
        
        # 8. 构建报告内容
        report_content = {
            "text": cleaned_text,
            "charts": charts,
            "tables": [],
            "metrics": {}
        }
        
        # 如果清理后的文本是JSON格式，尝试解析
        if cleaned_text and (cleaned_text.startswith("{") or cleaned_text.startswith("[")):
            try:
                parsed = json.loads(cleaned_text)
                if isinstance(parsed, dict):
                    parsed_charts = parsed.get("charts", [])
                    if parsed_charts and not charts:
                        report_content["charts"] = parsed_charts
                    for key in ["tables", "metrics"]:
                        if key in parsed:
                            report_content[key] = parsed[key]
            except:
                pass
        
        # 9. 更新报告内容和状态为 completed
        sheet_report.report_content = report_content
        sheet_report.report_status = "completed"
        db.commit()
        
        logger.info(f"[批量分析] Sheet {sheet_name} 分析完成 - text_length={len(cleaned_text)}, charts_count={len(charts)}")
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
    db: Session
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
            db=db
        )
        tasks.append(task)
    
    # 并发执行，但限制并发数（避免对Dify API造成压力）
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

