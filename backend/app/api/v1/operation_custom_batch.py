"""
定制化批量分析核心逻辑（复制自批量分析）
"""
import asyncio
import base64
import json
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session
from loguru import logger

from app.models.custom_batch_analysis import CustomBatchAnalysisSession, CustomSheetReport
from app.services.workflow_service import WorkflowService
from app.services.dify_service import DifyService
from app.utils.echarts_parser import parse_echarts_from_text

# 固定项目ID（单项目系统）
DEFAULT_PROJECT_ID = 1


async def process_custom_sheet_analysis(
    sheet_report_id: int,
    split_file_path: str,
    sheet_name: str,
    analysis_request: str,
    batch_session_id: int,
    user_id: int,
    db: Session
) -> dict:
    """
    处理单个Sheet的分析任务（定制化批量分析）
    复用现有的 generate_report 逻辑，直接调用Dify工作流
    """
    try:
        # 1. 更新报告状态为 generating
        sheet_report = db.query(CustomSheetReport).filter(CustomSheetReport.id == sheet_report_id).first()
        if not sheet_report:
            raise Exception(f"Sheet报告不存在: {sheet_report_id}")
        
        sheet_report.report_status = "generating"
        db.commit()
        logger.info(f"[定制化批量分析] Sheet {sheet_name} 开始分析 - report_id={sheet_report_id}, sheet_index={sheet_report.sheet_index}")
        
        # 2. 根据Sheet索引选择固定的工作流配置（定制化批量分析）
        sheet_index = sheet_report.sheet_index
        
        # 定义固定的工作流配置（前6个Sheet）
        if sheet_index == 0:
            # 第一个Sheet：最后操作分布
            api_key = "app-bPuA3gTwoFUefEd9BYJexJ3l"
            url_file = "http://118.89.16.95/v1/files/upload"
            url_work = "http://118.89.16.95/v1/chat-messages"
            function_key = "last_action_distribution"  # 最后操作分布
            logger.info(f"[定制化批量分析] 使用最后操作分布工作流 - sheet_index={sheet_index}")
        elif sheet_index == 1:
            # 第二个Sheet：新手漏斗
            api_key = "app-sAIJG3ZFzdgIS82JbmRne4sX"
            url_file = "http://118.89.16.95/v1/files/upload"
            url_work = "http://118.89.16.95/v1/chat-messages"
            function_key = "newbie_funnel"  # 新手漏斗
            logger.info(f"[定制化批量分析] 使用新手漏斗工作流 - sheet_index={sheet_index}")
        elif sheet_index == 2:
            # 第三个Sheet：回流用户
            api_key = "app-1kzCXNaI1995gPPE3b9VATYr"
            url_file = "http://118.89.16.95/v1/files/upload"
            url_work = "http://118.89.16.95/v1/chat-messages"
            function_key = "returning_users"  # 回流用户
            logger.info(f"[定制化批量分析] 使用回流用户工作流 - sheet_index={sheet_index}")
        elif sheet_index == 3:
            # 第四个Sheet：流失用户属性
            api_key = "app-F9cfBnTx0A6cvUzwCEps9KFN"
            url_file = "http://118.89.16.95/v1/files/upload"
            url_work = "http://118.89.16.95/v1/chat-messages"
            function_key = "churned_user_attributes"  # 流失用户属性
            logger.info(f"[定制化批量分析] 使用流失用户属性工作流 - sheet_index={sheet_index}")
        elif sheet_index == 4:
            # 第五个Sheet：留存率
            api_key = "app-DDrJ34dOessai3io1zcvtq7n"
            url_file = "http://118.89.16.95/v1/files/upload"
            url_work = "http://118.89.16.95/v1/chat-messages"
            function_key = "retention_rate_analysis"  # 留存率分析
            logger.info(f"[定制化批量分析] 使用留存率分析工作流 - sheet_index={sheet_index}")
        elif sheet_index == 5:
            # 第六个Sheet：LTV分析
            api_key = "app-EUzFTWScRAOV2a0AlT2AvRLm"
            url_file = "http://118.89.16.95/v1/files/upload"
            url_work = "http://118.89.16.95/v1/chat-messages"
            function_key = "ltv_analysis"  # LTV分析
            logger.info(f"[定制化批量分析] 使用LTV分析工作流 - sheet_index={sheet_index}")
        else:
            # 其他Sheet（索引>=6）：使用默认配置（回退到第一个工作流）
            api_key = "app-bPuA3gTwoFUefEd9BYJexJ3l"
            url_file = "http://118.89.16.95/v1/files/upload"
            url_work = "http://118.89.16.95/v1/chat-messages"
            function_key = "custom_operation_data_analysis"
            logger.warning(f"[定制化批量分析] Sheet索引 {sheet_index} 超出预期（>=6），使用默认工作流（最后操作分布）")
        
        # 固定参数
        file_param = "excell"  # 文件参数名
        query_param = "query"  # 对话参数名
        workflow_type = "chatflow"  # 工作流类型
        
        # 验证配置完整性
        if not all([api_key, url_file, url_work]):
            raise Exception("工作流配置不完整，请检查API Key、文件上传URL和工作流URL")
        
        # 3. 生成Dify用户标识
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
                    logger.info(f"[定制化批量分析] 使用替代路径格式: {alt_path}")
        
        # 检查文件是否存在
        if not file_path_obj.exists():
            error_msg = f"拆分后的文件不存在: {split_file_path}"
            logger.error(f"[定制化批量分析] {error_msg}")
            raise FileNotFoundError(error_msg)
        
        # 验证文件可读
        try:
            file_size = file_path_obj.stat().st_size
            if file_size == 0:
                raise Exception(f"文件大小为0: {split_file_path}")
            logger.info(f"[定制化批量分析] 文件验证通过 - 路径: {file_path_obj}, 大小: {file_size} bytes")
        except Exception as e:
            logger.error(f"[定制化批量分析] 文件验证失败: {str(e)}")
            raise
        
        if workflow_type == "chatflow":
            # Chatflow: 先上传文件到Dify
            logger.info(f"[定制化批量分析] 准备上传文件到Dify - file_path={file_path_obj}, file_size={file_size} bytes, url={url_file}, user_id={dify_user}")
            
            upload_result = await DifyService.upload_file(
                api_url=url_file,
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
            
            inputs = {
                file_param: dify_file_id,
                query_param: analysis_request,
            }
        else:
            # Workflow: 读取文件内容并转换为base64
            logger.info(f"[定制化批量分析] 读取文件内容转换为base64 - file_path={file_path_obj}")
            
            with open(file_path_obj, "rb") as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                logger.info(f"[定制化批量分析] 文件内容读取成功 - 大小: {len(file_content)} bytes")
            
            inputs = {
                file_param: file_base64,
                f"sys.{query_param}": analysis_request,
            }
        
        # 5. 调用Dify工作流
        result = await DifyService.run_workflow(
            api_url=url_work,
            api_key=api_key,
            workflow_id="1",
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
        
        logger.info(f"[定制化批量分析] Sheet {sheet_name} 分析完成 - text_length={len(cleaned_text)}, charts_count={len(charts)}")
        return report_content
        
    except Exception as e:
        logger.error(f"[定制化批量分析] Sheet {sheet_name} 分析失败: {str(e)}", exc_info=True)
        # 更新报告状态为 failed，记录错误信息
        sheet_report = db.query(CustomSheetReport).filter(CustomSheetReport.id == sheet_report_id).first()
        if sheet_report:
            sheet_report.report_status = "failed"
            sheet_report.error_message = str(e)
            db.commit()
        raise


async def process_all_custom_sheets_concurrently(
    sheet_reports: List[CustomSheetReport],
    analysis_request: str,
    user_id: int,
    batch_session_id: int,
    db: Session
) -> List[dict]:
    """
    并发处理所有Sheet的分析任务（定制化批量分析）
    """
    tasks = []
    for sheet_report in sheet_reports:
        # 为每个Sheet创建分析任务
        task = process_custom_sheet_analysis(
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
                logger.error(f"[定制化批量分析] Sheet分析任务失败: {str(e)}")
                return None
    
    # 使用 gather 并发执行，即使某个失败也不影响其他
    results = await asyncio.gather(*[bounded_task(task) for task in tasks], return_exceptions=True)
    
    # 统计成功和失败数量
    success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
    failed_count = len(results) - success_count
    
    logger.info(f"[定制化批量分析] 完成 - 成功: {success_count}, 失败: {failed_count}")
    return results

