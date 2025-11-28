"""
运营数据分析API（简化版，移除项目依赖）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Path as PathParam
from fastapi.responses import FileResponse, StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import Optional, List
import asyncio
from loguru import logger
from pathlib import Path
import uuid
import base64
import json
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import Body

from app.api.deps import get_db
from app.schemas.common import SuccessResponse
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.batch_analysis import BatchAnalysisSession, SheetReport
from app.models.custom_batch_analysis import CustomBatchAnalysisSession, CustomSheetReport
from app.models.session import AnalysisSession
from app.models.workflow import Workflow, WorkflowBinding
from app.services.workflow_service import WorkflowService
from app.services.dify_service import DifyService
from app.services.excel_service import ExcelService
from app.api.v1.operation_batch import process_all_sheets_concurrently
from app.api.v1.operation_custom_batch import process_all_custom_sheets_concurrently
from app.utils.echarts_parser import parse_echarts_from_text

router = APIRouter()

# 固定项目ID（单项目系统）
DEFAULT_PROJECT_ID = 1


# ==================== 数据模型 ====================

class ChartImage(BaseModel):
    """图表图片数据"""
    index: int
    title: str
    image: str  # Base64编码的图片数据

class DownloadReportRequest(BaseModel):
    """下载报告请求（简化版，移除project_id）"""
    session_id: int
    chart_images: Optional[List[ChartImage]] = []

class DownloadBatchReportRequest(BaseModel):
    """下载批量分析报告请求（简化版，移除project_id）"""
    chart_images: Optional[List[ChartImage]] = []


# ==================== 单文件分析API ====================

@router.post("/sessions", response_model=SuccessResponse)
async def create_session(
    request_data: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新的分析会话（简化版，移除project_id参数）
    """
    title = request_data.get("title") if request_data else None
    logger.info(f"[运营数据分析] 创建会话 - user_id={current_user.id}, title={title}")
    
    try:
        # 1. 获取工作流配置（使用固定项目ID）
        function_key = "operation_data_analysis"
        binding = WorkflowService.get_function_workflow(db, function_key)
        workflow_id = binding.workflow_id if binding else None
        
        # 2. 生成标题
        if not title:
            title = f"数据分析会话_{datetime.now().strftime('%Y%m%d')}"
        
        # 3. 创建会话（单项目系统，不需要project_id）
        conversation = AnalysisSession(
            user_id=current_user.id,
            function_key=function_key,
            workflow_id=workflow_id,
            title=title,
            messages=[]
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        logger.info(f"[运营数据分析] 会话创建成功 - conversation_id={conversation.id}, title={conversation.title}")
        
        # 4. 返回响应
        return SuccessResponse(
            data={
                "id": conversation.id,
                "title": conversation.title,
                "status": "draft",
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat()
            },
            message="会话创建成功"
        )
    except Exception as e:
        logger.error(f"[运营数据分析] 创建会话失败 - error={str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建会话失败: {str(e)}"
        )


@router.get("/sessions", response_model=SuccessResponse)
async def get_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取会话列表（简化版，移除project_id参数）
    """
    logger.info(f"[运营数据分析] 获取会话列表 - user_id={current_user.id}, page={page}, search={search}")
    
    try:
        # 1. 构建查询（单项目系统，不需要project_id过滤）
        function_key = "operation_data_analysis"
        query = db.query(AnalysisSession).filter(
            AnalysisSession.function_key == function_key,
            AnalysisSession.user_id == current_user.id
        )
        
        # 2. 搜索过滤
        if search:
            query = query.filter(AnalysisSession.title.ilike(f"%{search}%"))
        
        # 3. 获取总数
        total = query.count()
        
        # 4. 分页查询
        conversations = query.order_by(AnalysisSession.updated_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # 5. 构建响应数据
        items = []
        for conv in conversations:
            # 计算状态
            status_val = "draft"
            if conv.messages:
                last_msg = conv.messages[-1]
                if last_msg.get("role") == "assistant":
                    try:
                        last_time_str = last_msg.get("timestamp", "")
                        if last_time_str:
                            last_time = datetime.fromisoformat(last_time_str.replace('Z', '+00:00'))
                            if last_time.tzinfo is None:
                                last_time = last_time.replace(tzinfo=None)
                                now = datetime.utcnow()
                            else:
                                now = datetime.utcnow().replace(tzinfo=None)
                                last_time = last_time.replace(tzinfo=None)
                            
                            if (now - last_time) < timedelta(hours=1):
                                status_val = "in_progress"
                            else:
                                status_val = "completed"
                        else:
                            status_val = "completed"
                    except Exception as e:
                        logger.warning(f"[运营数据分析] 解析消息时间戳失败 - conversation_id={conv.id}, error={str(e)}")
                        status_val = "completed"
                else:
                    status_val = "in_progress"
            
            items.append({
                "id": conv.id,
                "title": conv.title,
                "status": status_val,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "message_count": len(conv.messages) if conv.messages else 0
            })
        
        logger.info(f"[运营数据分析] 获取会话列表成功 - total={total}, items_count={len(items)}")
        
        return SuccessResponse(
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )
    except Exception as e:
        logger.error(f"[运营数据分析] 获取会话列表失败 - error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}"
        )


@router.get("/sessions/{id}", response_model=SuccessResponse)
async def get_session_detail(
    id: int = PathParam(..., description="会话ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取会话详情（简化版，移除project_id参数）
    """
    logger.info(f"[运营数据分析] 获取会话详情 - session_id={id}, user_id={current_user.id}")
    
    try:
        # 1. 查询会话
        function_key = "operation_data_analysis"
        conversation = db.query(AnalysisSession).filter(
            AnalysisSession.id == id,
            AnalysisSession.function_key == function_key,
            AnalysisSession.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 2. 计算状态
        status_val = "draft"
        if conversation.messages:
            last_msg = conversation.messages[-1]
            if last_msg.get("role") == "assistant":
                try:
                    last_time_str = last_msg.get("timestamp", "")
                    if last_time_str:
                        last_time = datetime.fromisoformat(last_time_str.replace('Z', '+00:00'))
                        if last_time.tzinfo is None:
                            last_time = last_time.replace(tzinfo=None)
                            now = datetime.utcnow()
                        else:
                            now = datetime.utcnow().replace(tzinfo=None)
                            last_time = last_time.replace(tzinfo=None)
                        
                        if (now - last_time) < timedelta(hours=1):
                            status_val = "in_progress"
                        else:
                            status_val = "completed"
                    else:
                        status_val = "completed"
                except Exception as e:
                    logger.warning(f"[运营数据分析] 解析消息时间戳失败 - conversation_id={conversation.id}, error={str(e)}")
                    status_val = "completed"
            else:
                status_val = "in_progress"
        
        logger.info(f"[运营数据分析] 获取会话详情成功 - conversation_id={id}, messages_count={len(conversation.messages) if conversation.messages else 0}")
        
        return SuccessResponse(
            data={
                "id": conversation.id,
                "title": conversation.title,
                "status": status_val,
                "messages": conversation.messages if conversation.messages else [],
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[运营数据分析] 获取会话详情失败 - error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话详情失败: {str(e)}"
        )


@router.delete("/sessions/{id}", response_model=SuccessResponse)
async def delete_session(
    id: int = PathParam(..., description="会话ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    删除会话（简化版，移除project_id参数）
    """
    logger.info(f"[运营数据分析] 删除会话 - session_id={id}, user_id={current_user.id}")
    
    try:
        # 1. 查询会话
        function_key = "operation_data_analysis"
        conversation = db.query(AnalysisSession).filter(
            AnalysisSession.id == id,
            AnalysisSession.function_key == function_key,
            AnalysisSession.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 2. 删除会话
        db.delete(conversation)
        db.commit()
        
        logger.info(f"[运营数据分析] 会话删除成功 - session_id={id}")
        
        return SuccessResponse(
            data={"deleted_id": id},
            message="会话删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[运营数据分析] 删除会话失败 - session_id={id}, error={str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )


@router.post("/upload", response_model=SuccessResponse)
async def upload_excel(
    file: UploadFile = File(...),
    session_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传Excel文件（简化版，移除project_id参数）
    """
    logger.info(f"[运营数据分析] 上传文件 - session_id={session_id}, filename={file.filename}, user_id={current_user.id}")
    
    # 验证文件类型
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.xlsx', '.csv']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 .xlsx 和 .csv 格式的文件"
        )
    
    # 验证文件大小（10MB）
    file_content = await file.read()
    file_size = len(file_content)
    max_size = 10 * 1024 * 1024  # 10MB
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过10MB"
        )
    
    # 创建上传目录（使用固定项目ID）
    upload_dir = Path(f"uploads/operation/project_{DEFAULT_PROJECT_ID}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名（使用session_id和uuid）
    file_id_str = f"{session_id}_{uuid.uuid4().hex[:8]}"
    file_name = f"{file_id_str}{file_ext}"
    file_path = upload_dir / file_name
    
    # 保存文件
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    logger.info(f"[运营数据分析] 文件保存成功 - file_path={file_path}, size={file_size}")
    
    # 更新会话标题为文件名（去掉扩展名）
    try:
        conversation = db.query(AnalysisSession).filter(
            AnalysisSession.id == session_id,
            AnalysisSession.function_key == "operation_data_analysis"
        ).first()
        
        if conversation:
            file_name_without_ext = Path(file.filename).stem
            conversation.title = file_name_without_ext
            db.commit()
            logger.info(f"[运营数据分析] 会话标题已更新为文件名 - session_id={session_id}, title={file_name_without_ext}")
    except Exception as e:
        logger.warning(f"[运营数据分析] 更新会话标题失败 - session_id={session_id}, error={str(e)}")
    
    # 使用文件路径的hash作为file_id
    import hashlib
    file_id_hash = int(hashlib.md5(str(file_path).encode()).hexdigest()[:8], 16) % 1000000
    
    return SuccessResponse(
        data={
            "file_id": file_id_hash,
            "file_name": file.filename,
            "file_path": str(file_path),
            "row_count": 0,
            "column_info": {}
        },
        message="文件上传成功"
    )


@router.post("/generate", response_model=SuccessResponse)
async def generate_report(
    session_id: int = Form(...),
    file_id: int = Form(...),
    analysis_request: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    生成分析报告（简化版，移除project_id参数）
    调用Dify工作流处理Excel文件并生成报告
    """
    logger.info(f"[运营数据分析] 生成报告 - session_id={session_id}, file_id={file_id}, user_id={current_user.id}")
    logger.info(f"[运营数据分析] 分析需求: {analysis_request[:100]}...")
    
    try:
        # 1. 获取绑定的Dify工作流（优先使用用户配置，如果没有则使用全局配置）
        function_key = "operation_data_analysis"
        binding = WorkflowService.get_function_workflow(db, function_key, current_user.id)
        
        if not binding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="尚未配置运营数据分析工作流，请在系统设置中配置"
            )
        
        workflow = WorkflowService.get_workflow_by_id(db, binding.workflow_id)
        if not workflow or not workflow.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在或已禁用"
            )
        
        if workflow.platform != "dify":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"当前工作流平台为 {workflow.platform}，仅支持 Dify 平台"
            )
        
        logger.info(f"[运营数据分析] 找到工作流 - workflow_id={workflow.id}, name={workflow.name}")
        
        # 2. 读取上传的文件
        upload_dir = Path(f"uploads/operation/project_{DEFAULT_PROJECT_ID}")
        file_path = None
        
        if upload_dir.exists():
            for f in upload_dir.iterdir():
                if f.is_file() and str(session_id) in f.stem:
                    file_path = f
                    break
        
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在，请重新上传"
            )
        
        logger.info(f"[运营数据分析] 找到文件 - file_path={file_path}")
        
        # 3. 准备Dify工作流输入
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="工作流配置不完整，请检查API Key、文件上传URL和工作流URL"
            )
        
        # 生成Dify用户标识（移除project_id参数）
        dify_user = DifyService.generate_user_id(
            user_id=current_user.id,
            function_key=function_key,
            conversation_id=session_id
        )
        
        # 根据工作流类型处理文件
        if workflow_type == "chatflow":
            # Chatflow: 先上传文件到Dify
            logger.info(f"[运营数据分析] 上传文件到Dify - file_path={file_path}, url={url_file}")
            upload_result = await DifyService.upload_file(
                api_url=url_file,  # 直接使用用户配置的文件上传URL
                api_key=api_key,
                file_path=str(file_path),
                file_name=file_path.name,
                user_id=dify_user
            )
            
            if not upload_result.get("success"):
                error_msg = upload_result.get("error", "文件上传失败")
                logger.error(f"[运营数据分析] 文件上传到Dify失败 - {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"文件上传到Dify失败: {error_msg}"
                )
            
            dify_file_id = upload_result.get("data", {}).get("id")
            if not dify_file_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Dify文件上传成功但未返回文件ID"
                )
            
            logger.info(f"[运营数据分析] 文件上传成功 - Dify文件ID: {dify_file_id}")
            
            # Chatflow输入参数：使用用户配置的参数名
            inputs = {
                file_param: dify_file_id,  # 文件参数名（用户配置）
                query_param: analysis_request,  # 对话参数名（用户配置）
            }
        else:
            # Workflow: 读取文件内容并转换为base64
            with open(file_path, "rb") as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            inputs = {
                "excell": file_base64,
                "sys.query": analysis_request,
            }
        
        logger.info(f"[运营数据分析] 调用Dify {workflow_type} - url={url_work}, inputs_keys={list(inputs.keys())}")
        
        # 4. 调用Dify工作流（使用用户配置的URL）
        result = await DifyService.run_workflow(
            api_url=url_work,  # 直接使用用户配置的工作流URL
            api_key=api_key,
            workflow_id="1",  # 固定为1，实际使用url_work
            user_id=current_user.id,
            function_key=function_key,
            inputs=inputs,
            conversation_id=session_id,
            response_mode="blocking",
            workflow_type=workflow_type
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "Dify工作流执行失败")
            logger.error(f"[运营数据分析] Dify工作流执行失败 - {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"工作流执行失败: {error_msg}"
            )
        
        # 5. 解析Dify返回的结果
        dify_data = result.get("data", {})
        
        if workflow_type == "chatflow":
            report_text = dify_data.get("answer", "")
            if not report_text:
                report_text = dify_data.get("text", "")
        else:
            workflow_output = dify_data.get("data", {}).get("outputs", {})
            report_text = workflow_output.get("text", "")
            if not report_text:
                report_text = dify_data.get("text", "")
        
        # 6. 解析echarts代码块
        cleaned_text, charts = parse_echarts_from_text(report_text)
        
        # 7. 构建报告内容
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
        
        logger.info(f"[运营数据分析] 报告生成成功 - text_length={len(cleaned_text)}, charts_count={len(charts)}")
        
        # 8. 保存对话消息到会话记录
        try:
            conversation = db.query(AnalysisSession).filter(
                AnalysisSession.id == session_id,
                AnalysisSession.function_key == function_key
            ).first()
            
            if conversation:
                user_message = {
                    "role": "user",
                    "content": analysis_request,
                    "timestamp": datetime.utcnow().isoformat(),
                    "file_name": file_path.name if file_path else None
                }
                
                assistant_message = {
                    "role": "assistant",
                    "content": cleaned_text,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if charts:
                    assistant_message["charts"] = charts
                
                if report_content.get("tables"):
                    assistant_message["tables"] = report_content["tables"]
                
                if not conversation.messages:
                    conversation.messages = []
                conversation.messages.append(user_message)
                conversation.messages.append(assistant_message)
                
                if conversation.title.startswith("数据分析会话_"):
                    if user_message.get("file_name"):
                        file_name_without_ext = Path(user_message["file_name"]).stem
                        conversation.title = file_name_without_ext
                
                db.commit()
                logger.info(f"[运营数据分析] 对话消息已保存到会话 - session_id={session_id}, messages_count={len(conversation.messages)}")
        except Exception as e:
            logger.error(f"[运营数据分析] 保存对话消息失败 - session_id={session_id}, error={str(e)}")
        
        # 9. 返回报告
        report_id = uuid.uuid4().hex
        
        return SuccessResponse(
            data={
                "report_id": report_id,
                "content": report_content
            },
            message="报告生成成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e)
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"[运营数据分析] 生成报告异常 - {error_detail}")
        logger.error(f"[运营数据分析] 异常堆栈:\n{error_traceback}")
        
        error_msg = f"生成报告失败: {error_detail}"
        if "workflow" in error_detail.lower() or "dify" in error_detail.lower():
            error_msg = f"工作流执行错误: {error_detail}"
        elif "file" in error_detail.lower():
            error_msg = f"文件处理错误: {error_detail}"
        elif "upload" in error_detail.lower():
            error_msg = f"文件上传错误: {error_detail}"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.post("/reports/{report_id}/download")
async def download_report_pdf(
    report_id: str = PathParam(..., description="报告ID（实际使用session_id获取报告）"),
    request_data: DownloadReportRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    下载报告PDF（支持图表图片）（简化版，移除project_id参数）
    """
    import traceback
    logger.info(f"[运营数据分析] ====== 开始下载报告PDF ======")
    logger.info(f"[运营数据分析] report_id={report_id}, session_id={request_data.session_id}, user_id={current_user.id}")
    logger.info(f"[运营数据分析] 收到 {len(request_data.chart_images)} 个图表图片")
    
    try:
        # 1. 从会话记录中获取报告内容（使用固定项目ID）
        function_key = "operation_data_analysis"
        conversation = db.query(AnalysisSession).filter(
            AnalysisSession.id == request_data.session_id,
            AnalysisSession.function_key == function_key,
            AnalysisSession.user_id == current_user.id
        ).first()
        
        if not conversation:
            logger.error(f"[运营数据分析] 会话不存在 - session_id={request_data.session_id}, user_id={current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或无权限访问"
            )
        
        logger.info(f"[运营数据分析] 找到会话 - conversation_id={conversation.id}, title={conversation.title}, messages_count={len(conversation.messages) if conversation.messages else 0}")
        
        # 2. 从最后一条assistant消息中获取报告内容
        report_content = None
        try:
            if conversation.messages:
                assistant_messages = [msg for msg in conversation.messages if msg.get("role") == "assistant"]
                if assistant_messages:
                    last_assistant_msg = assistant_messages[-1]
                    report_content = {
                        "text": str(last_assistant_msg.get("content", "")),
                        "charts": last_assistant_msg.get("charts", []) or [],
                        "tables": last_assistant_msg.get("tables", []) or [],
                        "metrics": last_assistant_msg.get("metrics", {}) or {}
                    }
        except Exception as e:
            logger.error(f"[运营数据分析] 获取报告内容时出错: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取报告内容失败: {str(e)}"
            )
        
        if not report_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告内容不存在，请先生成报告"
            )
        
        if not report_content.get("text"):
            report_content["text"] = "报告内容为空"
        
        # 3. 处理图表图片
        chart_images_data = []
        if request_data.chart_images:
            for chart_img in request_data.chart_images:
                try:
                    image_data = chart_img.image.split(',')[1] if ',' in chart_img.image else chart_img.image
                    chart_images_data.append({
                        'index': chart_img.index,
                        'title': chart_img.title,
                        'image_data': image_data
                    })
                except Exception as e:
                    logger.error(f"[运营数据分析] ✗ 解析图表图片失败: {str(e)}")
        
        # 4. 生成PDF
        try:
            from app.utils.pdf_generator import generate_report_pdf
            
            pdf_bytes = generate_report_pdf(
                title=str(conversation.title or "数据分析报告"),
                report_content=report_content,
                session_id=request_data.session_id,
                chart_images=chart_images_data
            )
            logger.info(f"[运营数据分析] PDF生成成功 - 大小: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"[运营数据分析] PDF生成失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF生成失败: {str(e)}"
            )
        
        # 5. 返回PDF文件
        filename = f"{conversation.title or '数据分析报告'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"[运营数据分析] ====== PDF下载失败 ======")
        logger.error(f"[运营数据分析] 错误类型: {type(e).__name__}")
        logger.error(f"[运营数据分析] 错误消息: {str(e)}")
        logger.error(f"[运营数据分析] 完整堆栈:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成PDF失败: {str(e)}"
        )


@router.get("/reports/{report_id}/download-image")
async def download_report_image(
    report_id: str = PathParam(..., description="报告ID（实际使用session_id获取报告）"),
    session_id: int = Query(..., description="会话ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    下载报告图片（PNG格式，避免PDF中文乱码问题）（简化版，移除project_id参数）
    """
    import traceback
    logger.info(f"[运营数据分析] ====== 开始下载报告图片 ======")
    logger.info(f"[运营数据分析] report_id={report_id}, session_id={session_id}, user_id={current_user.id}")
    
    try:
        # 1. 从会话记录中获取报告内容（使用固定项目ID）
        function_key = "operation_data_analysis"
        conversation = db.query(AnalysisSession).filter(
            AnalysisSession.id == session_id,
            AnalysisSession.function_key == function_key,
            AnalysisSession.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或无权限访问"
            )
        
        # 2. 从最后一条assistant消息中获取报告内容
        report_content = None
        try:
            if conversation.messages:
                assistant_messages = [msg for msg in conversation.messages if msg.get("role") == "assistant"]
                if assistant_messages:
                    last_assistant_msg = assistant_messages[-1]
                    report_content = {
                        "text": str(last_assistant_msg.get("content", "")),
                        "charts": last_assistant_msg.get("charts", []) or [],
                        "tables": last_assistant_msg.get("tables", []) or [],
                        "metrics": last_assistant_msg.get("metrics", {}) or {}
                    }
        except Exception as e:
            logger.error(f"[运营数据分析] 获取报告内容时出错: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取报告内容失败: {str(e)}"
            )
        
        if not report_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告内容不存在，请先生成报告"
            )
        
        if not report_content.get("text"):
            report_content["text"] = "报告内容为空"
        
        # 3. 生成图片
        try:
            from app.utils.image_generator import generate_report_image
            
            image_bytes = generate_report_image(
                title=str(conversation.title or "数据分析报告"),
                report_content=report_content,
                session_id=session_id
            )
            logger.info(f"[运营数据分析] 图片生成成功 - 大小: {len(image_bytes)} bytes")
        except Exception as e:
            logger.error(f"[运营数据分析] 图片生成失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"图片生成失败: {str(e)}"
            )
        
        # 4. 返回图片文件
        filename = f"{conversation.title or '数据分析报告'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"[运营数据分析] ====== 图片下载失败 ======")
        logger.error(f"[运营数据分析] 错误类型: {type(e).__name__}")
        logger.error(f"[运营数据分析] 错误消息: {str(e)}")
        logger.error(f"[运营数据分析] 完整堆栈:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成图片失败: {str(e)}"
        )


@router.get("/template")
async def download_template(
    current_user: User = Depends(get_current_active_user)
):
    """
    下载Excel模板
    """
    logger.info(f"[运营数据分析] 下载模板 - user_id={current_user.id}")
    
    # TODO: 生成Excel模板文件并返回
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="模板下载功能待实现"
    )


# ==================== 批量分析相关API ====================

@router.post("/batch/upload", response_model=SuccessResponse)
async def upload_batch_excel(
    file: UploadFile = File(...),
    analysis_request: str = Form("生成数据分析报告"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传多Sheet Excel文件并拆分（简化版，移除project_id参数）
    拆分完成后自动开始批量分析
    """
    logger.info(f"[批量分析] 上传文件 - filename={file.filename}, user_id={current_user.id}")
    
    # 1. 验证文件
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.xlsx']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="批量分析只支持 .xlsx 格式的文件"
        )
    
    # 验证文件大小（20MB）
    file_content = await file.read()
    file_size = len(file_content)
    max_size = 20 * 1024 * 1024  # 20MB
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过20MB"
        )
    
    try:
        # 2. 创建批量会话记录（使用固定项目ID）
        batch_session = BatchAnalysisSession(
            user_id=current_user.id,
            original_file_name=file.filename,
            original_file_path="",
            split_files_dir="",
            sheet_count=0,
            status="processing"
        )
        db.add(batch_session)
        db.flush()
        
        batch_session_id = batch_session.id
        logger.info(f"[批量分析] 创建批量会话 - batch_session_id={batch_session_id}")
        
        # 3. 保存原始文件
        batch_dir = Path(f"uploads/operation/project_{DEFAULT_PROJECT_ID}/batch/batch_{batch_session_id}")
        original_dir = batch_dir / "original"
        sheets_dir = batch_dir / "sheets"
        
        original_dir.mkdir(parents=True, exist_ok=True)
        sheets_dir.mkdir(parents=True, exist_ok=True)
        
        original_file_path = original_dir / file.filename
        with open(original_file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"[批量分析] 原始文件已保存 - path={original_file_path}")
        
        # 4. 拆分Excel文件
        logger.info(f"[批量分析] 开始拆分Excel文件...")
        split_files = ExcelService.split_excel_file(
            source_file_path=str(original_file_path),
            output_dir=sheets_dir,
            batch_session_id=batch_session_id
        )
        
        sheet_count = len(split_files)
        logger.info(f"[批量分析] 拆分完成 - sheet_count={sheet_count}")
        
        # 验证所有拆分文件都存在
        for sheet_info in split_files:
            split_path = Path(sheet_info["split_file_path"])
            if not split_path.exists():
                logger.error(f"[批量分析] 拆分文件不存在: {split_path}")
                raise Exception(f"拆分文件不存在: {split_path}")
        
        # 5. 更新批量会话记录
        batch_session.original_file_path = str(original_file_path)
        batch_session.split_files_dir = str(sheets_dir)
        batch_session.sheet_count = sheet_count
        
        # 6. 为每个Sheet创建报告记录
        sheet_reports = []
        for sheet_info in split_files:
            sheet_report = SheetReport(
                batch_session_id=batch_session_id,
                sheet_name=sheet_info["sheet_name"],
                sheet_index=sheet_info["sheet_index"],
                split_file_path=sheet_info["split_file_path"],
                report_status="pending"
            )
            db.add(sheet_report)
            sheet_reports.append(sheet_report)
        
        db.commit()
        logger.info(f"[批量分析] 批量会话和Sheet报告记录已创建")
        
        # 7. 返回结果
        return SuccessResponse(
            data={
                "batch_session_id": batch_session_id,
                "sheet_count": sheet_count,
                "sheets": [
                    {
                        "id": sr.id,
                        "sheet_name": sr.sheet_name,
                        "sheet_index": sr.sheet_index,
                        "split_file_path": sr.split_file_path,
                        "report_status": sr.report_status
                    }
                    for sr in sheet_reports
                ],
                "status": batch_session.status
            },
            message="文件上传成功，已拆分完成"
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"[批量分析] 上传和拆分失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传和拆分失败: {str(e)}"
        )


@router.post("/batch/analyze", response_model=SuccessResponse)
async def start_batch_analysis(
    batch_session_id: int = Form(...),
    analysis_request: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    开始批量分析（异步处理）（简化版，移除project_id参数）
    复用现有的 generate_report 逻辑，对每个Sheet重复调用
    """
    logger.info(f"[批量分析] 开始批量分析 - batch_session_id={batch_session_id}, user_id={current_user.id}")
    
    try:
        # 1. 获取批量会话（使用固定项目ID）
        batch_session = db.query(BatchAnalysisSession).filter(
            BatchAnalysisSession.id == batch_session_id,
            BatchAnalysisSession.user_id == current_user.id
        ).first()
        
        if not batch_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="批量会话不存在或无权限访问"
            )
        
        # 2. 获取所有待处理的Sheet报告
        sheet_reports = db.query(SheetReport).filter(
            SheetReport.batch_session_id == batch_session_id,
            SheetReport.report_status == "pending"
        ).order_by(SheetReport.sheet_index).all()
        
        if not sheet_reports:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有待处理的Sheet报告"
            )
        
        logger.info(f"[批量分析] 找到 {len(sheet_reports)} 个待处理的Sheet")
        
        # 3. 更新批量会话状态
        batch_session.status = "processing"
        db.commit()
        
        # 4. 启动异步任务处理每个Sheet
        async def run_batch_analysis():
            """后台异步任务"""
            try:
                from app.core.database import SessionLocal
                background_db = SessionLocal()
                
                try:
                    background_sheet_reports = background_db.query(SheetReport).filter(
                        SheetReport.batch_session_id == batch_session_id
                    ).order_by(SheetReport.sheet_index).all()
                    
                    # 并发处理所有Sheet（移除project_id参数）
                    results = await process_all_sheets_concurrently(
                        sheet_reports=background_sheet_reports,
                        analysis_request=analysis_request,
                        user_id=current_user.id,
                        batch_session_id=batch_session_id,
                        db=background_db
                    )
                    
                    # 更新批量会话状态
                    background_batch_session = background_db.query(BatchAnalysisSession).filter(
                        BatchAnalysisSession.id == batch_session_id
                    ).first()
                    
                    if background_batch_session:
                        completed_count = background_db.query(SheetReport).filter(
                            SheetReport.batch_session_id == batch_session_id,
                            SheetReport.report_status == "completed"
                        ).count()
                        
                        failed_count = background_db.query(SheetReport).filter(
                            SheetReport.batch_session_id == batch_session_id,
                            SheetReport.report_status == "failed"
                        ).count()
                        
                        total_count = background_batch_session.sheet_count
                        
                        if completed_count == total_count:
                            background_batch_session.status = "completed"
                        elif failed_count == total_count:
                            background_batch_session.status = "failed"
                        elif failed_count > 0:
                            background_batch_session.status = "partial_failed"
                        else:
                            background_batch_session.status = "processing"
                        
                        background_db.commit()
                        logger.info(f"[批量分析] 批量分析完成 - batch_session_id={batch_session_id}, completed={completed_count}, failed={failed_count}")
                
                finally:
                    background_db.close()
            
            except Exception as e:
                logger.error(f"[批量分析] 后台任务执行失败: {str(e)}", exc_info=True)
                from app.core.database import SessionLocal
                error_db = SessionLocal()
                try:
                    error_batch_session = error_db.query(BatchAnalysisSession).filter(
                        BatchAnalysisSession.id == batch_session_id
                    ).first()
                    if error_batch_session:
                        error_batch_session.status = "failed"
                        error_db.commit()
                finally:
                    error_db.close()
        
        # 启动后台任务
        asyncio.create_task(run_batch_analysis())
        
        # 5. 返回处理状态
        return SuccessResponse(
            data={
                "batch_session_id": batch_session_id,
                "status": "processing",
                "total_sheets": len(sheet_reports),
                "completed_sheets": 0
            },
            message="批量分析已开始，正在后台处理"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[批量分析] 启动批量分析失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动批量分析失败: {str(e)}"
        )


@router.get("/batch/{batch_session_id}/status", response_model=SuccessResponse)
async def get_batch_analysis_status(
    batch_session_id: int = PathParam(..., description="批量会话ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取批量分析状态（简化版，移除project_id参数）
    """
    logger.info(f"[批量分析] 查询状态 - batch_session_id={batch_session_id}, user_id={current_user.id}")
    
    # 1. 获取批量会话（使用固定项目ID）
    batch_session = db.query(BatchAnalysisSession).filter(
        BatchAnalysisSession.id == batch_session_id,
        BatchAnalysisSession.user_id == current_user.id
    ).first()
    
    if not batch_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批量会话不存在或无权限访问"
        )
    
    # 2. 获取所有Sheet报告
    sheet_reports = db.query(SheetReport).filter(
        SheetReport.batch_session_id == batch_session_id
    ).order_by(SheetReport.sheet_index).all()
    
    # 3. 统计状态
    total_sheets = len(sheet_reports)
    completed_sheets = sum(1 for sr in sheet_reports if sr.report_status == "completed")
    failed_sheets = sum(1 for sr in sheet_reports if sr.report_status == "failed")
    generating_sheets = sum(1 for sr in sheet_reports if sr.report_status == "generating")
    
    # 4. 构建报告列表
    reports_data = []
    for sr in sheet_reports:
        report_data = {
            "id": sr.id,
            "sheet_name": sr.sheet_name,
            "sheet_index": sr.sheet_index,
            "report_status": sr.report_status,
        }
        
        if sr.report_status == "completed" and sr.report_content:
            report_data["report_content"] = sr.report_content
        elif sr.report_status == "failed" and sr.error_message:
            report_data["error_message"] = sr.error_message
        
        reports_data.append(report_data)
    
    return SuccessResponse(
        data={
            "batch_session_id": batch_session_id,
            "status": batch_session.status,
            "total_sheets": total_sheets,
            "completed_sheets": completed_sheets,
            "failed_sheets": failed_sheets,
            "generating_sheets": generating_sheets,
            "pending_sheets": total_sheets - completed_sheets - failed_sheets - generating_sheets,
            "reports": reports_data
        },
        message="状态查询成功"
    )


@router.get("/batch/reports/{report_id}", response_model=SuccessResponse)
async def get_sheet_report(
    report_id: int = PathParam(..., description="报告ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个报告详情（简化版，移除project_id参数）
    """
    logger.info(f"[批量分析] 查询报告详情 - report_id={report_id}, user_id={current_user.id}")
    
    # 1. 获取报告
    sheet_report = db.query(SheetReport).filter(
        SheetReport.id == report_id
    ).first()
    
    if not sheet_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )
    
    # 2. 验证权限（通过批量会话验证，使用固定项目ID）
    batch_session = db.query(BatchAnalysisSession).filter(
        BatchAnalysisSession.id == sheet_report.batch_session_id,
        BatchAnalysisSession.user_id == current_user.id
    ).first()
    
    if not batch_session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此报告"
        )
    
    # 3. 构建响应数据
    report_data = {
        "id": sheet_report.id,
        "sheet_name": sheet_report.sheet_name,
        "sheet_index": sheet_report.sheet_index,
        "report_status": sheet_report.report_status,
        "report_content": sheet_report.report_content or {},
        "error_message": sheet_report.error_message,
        "created_at": sheet_report.created_at.isoformat() if sheet_report.created_at else None,
        "updated_at": sheet_report.updated_at.isoformat() if sheet_report.updated_at else None
    }
    
    return SuccessResponse(
        data=report_data,
        message="报告查询成功"
    )


@router.post("/batch/reports/{report_id}/download")
async def download_batch_report_pdf(
    report_id: int = PathParam(..., description="报告ID"),
    request_data: DownloadBatchReportRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    下载批量分析报告PDF（支持图表图片）（简化版，移除project_id参数）
    """
    import traceback
    logger.info(f"[批量分析] ====== 开始下载报告PDF ======")
    logger.info(f"[批量分析] report_id={report_id}, user_id={current_user.id}")
    logger.info(f"[批量分析] 收到 {len(request_data.chart_images) if request_data.chart_images else 0} 个图表图片")
    
    try:
        # 1. 获取Sheet报告
        sheet_report = db.query(SheetReport).filter(
            SheetReport.id == report_id
        ).first()
        
        if not sheet_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )
        
        # 2. 验证权限（使用固定项目ID）
        batch_session = db.query(BatchAnalysisSession).filter(
            BatchAnalysisSession.id == sheet_report.batch_session_id,
            BatchAnalysisSession.user_id == current_user.id
        ).first()
        
        if not batch_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此报告"
            )
        
        # 3. 检查报告状态和内容
        if sheet_report.report_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"报告尚未完成，当前状态: {sheet_report.report_status}"
            )
        
        if not sheet_report.report_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告内容不存在"
            )
        
        # 4. 获取报告内容
        report_content = {
            "text": str(sheet_report.report_content.get("text", "")),
            "charts": sheet_report.report_content.get("charts", []) or [],
            "tables": sheet_report.report_content.get("tables", []) or [],
            "metrics": sheet_report.report_content.get("metrics", {}) or {}
        }
        
        if not report_content.get("text"):
            report_content["text"] = "报告内容为空"
        
        # 5. 处理图表图片
        chart_images_data = []
        if request_data.chart_images:
            for chart_img in request_data.chart_images:
                try:
                    image_data = chart_img.image.split(',')[1] if ',' in chart_img.image else chart_img.image
                    chart_images_data.append({
                        'index': chart_img.index,
                        'title': chart_img.title,
                        'image_data': image_data
                    })
                except Exception as e:
                    logger.error(f"[批量分析] ✗ 解析图表图片失败: {str(e)}")
        
        # 6. 生成PDF
        try:
            from app.utils.pdf_generator import generate_report_pdf
            
            report_title = f"{sheet_report.sheet_name} - 数据分析报告"
            pdf_bytes = generate_report_pdf(
                title=report_title,
                report_content=report_content,
                session_id=sheet_report.batch_session_id,
                chart_images=chart_images_data
            )
            logger.info(f"[批量分析] PDF生成成功 - 大小: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"[批量分析] PDF生成失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF生成失败: {str(e)}"
            )
        
        # 7. 返回PDF文件
        filename = f"{sheet_report.sheet_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"[批量分析] ====== PDF下载失败 ======")
        logger.error(f"[批量分析] 错误类型: {type(e).__name__}")
        logger.error(f"[批量分析] 错误消息: {str(e)}")
        logger.error(f"[批量分析] 完整堆栈:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成PDF失败: {str(e)}"
        )


@router.post("/batch/sessions", response_model=SuccessResponse)
async def create_batch_session(
    request_data: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新的批量分析会话（简化版，移除project_id参数）
    """
    title = request_data.get("title") if request_data else None
    logger.info(f"[批量分析] 创建会话 - user_id={current_user.id}, title={title}")
    
    try:
        # 生成标题
        if not title:
            title = f"批量分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建批量会话（初始状态为draft，等待上传文件）
        batch_session = BatchAnalysisSession(
            user_id=current_user.id,
            original_file_name=title,
            original_file_path="",
            split_files_dir="",
            sheet_count=0,
            status="draft"  # 草稿状态，等待上传文件
        )
        db.add(batch_session)
        db.commit()
        db.refresh(batch_session)
        
        logger.info(f"[批量分析] 会话创建成功 - batch_session_id={batch_session.id}, title={batch_session.original_file_name}")
        
        # 返回响应
        return SuccessResponse(
            data={
                "id": batch_session.id,
                "original_file_name": batch_session.original_file_name,
                "sheet_count": batch_session.sheet_count,
                "status": batch_session.status,
                "created_at": batch_session.created_at.isoformat() if batch_session.created_at else None,
                "updated_at": batch_session.updated_at.isoformat() if batch_session.updated_at else None
            },
            message="批量分析会话创建成功"
        )
    except Exception as e:
        logger.error(f"[批量分析] 创建会话失败 - error={str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建批量分析会话失败: {str(e)}"
        )


@router.get("/batch/sessions", response_model=SuccessResponse)
async def get_batch_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取批量分析会话列表（简化版，移除project_id参数）
    """
    logger.info(f"[批量分析] 查询会话列表 - user_id={current_user.id}")
    
    # 1. 查询批量会话（使用固定项目ID）
    query = db.query(BatchAnalysisSession).filter(
        BatchAnalysisSession.user_id == current_user.id
    ).order_by(BatchAnalysisSession.created_at.desc())
    
    # 2. 分页
    total = query.count()
    sessions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 3. 构建响应数据
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            "id": session.id,
            "original_file_name": session.original_file_name,
            "sheet_count": session.sheet_count,
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None
        })
    
    return SuccessResponse(
        data={
            "sessions": sessions_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        },
        message="会话列表查询成功"
    )


@router.delete("/batch/sessions/{batch_session_id}", response_model=SuccessResponse)
async def delete_batch_session(
    batch_session_id: int = PathParam(..., description="批量会话ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除批量分析会话（简化版，移除project_id参数）
    """
    logger.info(f"[批量分析] 删除会话 - batch_session_id={batch_session_id}, user_id={current_user.id}")
    
    try:
        # 1. 查询批量会话（使用固定项目ID）
        batch_session = db.query(BatchAnalysisSession).filter(
            BatchAnalysisSession.id == batch_session_id,
            BatchAnalysisSession.user_id == current_user.id
        ).first()
        
        if not batch_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="批量会话不存在或无权限访问"
            )
        
        # 2. 删除会话（级联删除会同时删除相关的SheetReport记录）
        db.delete(batch_session)
        db.commit()
        
        logger.info(f"[批量分析] 会话删除成功 - batch_session_id={batch_session_id}")
        
        return SuccessResponse(
            data={"deleted_id": batch_session_id},
            message="会话删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[批量分析] 删除会话失败 - batch_session_id={batch_session_id}, error={str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )


# ==================== 定制化批量分析相关API ====================

@router.post("/custom-batch/upload", response_model=SuccessResponse)
async def upload_custom_batch_excel(
    file: UploadFile = File(...),
    analysis_request: str = Form("生成数据分析报告"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传多Sheet Excel文件并拆分（定制化批量分析）
    拆分完成后自动开始批量分析
    """
    logger.info(f"[定制化批量分析] 上传文件 - filename={file.filename}, user_id={current_user.id}")
    
    # 1. 验证文件
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.xlsx']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="批量分析只支持 .xlsx 格式的文件"
        )
    
    # 验证文件大小（20MB）
    file_content = await file.read()
    file_size = len(file_content)
    max_size = 20 * 1024 * 1024  # 20MB
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过20MB"
        )
    
    try:
        # 2. 创建批量会话记录（使用固定项目ID）
        batch_session = CustomBatchAnalysisSession(
            user_id=current_user.id,
            original_file_name=file.filename,
            original_file_path="",
            split_files_dir="",
            sheet_count=0,
            status="processing"
        )
        db.add(batch_session)
        db.flush()
        
        batch_session_id = batch_session.id
        logger.info(f"[定制化批量分析] 创建批量会话 - batch_session_id={batch_session_id}")
        
        # 3. 保存原始文件（使用custom_batch目录）
        batch_dir = Path(f"uploads/operation/project_{DEFAULT_PROJECT_ID}/custom_batch/batch_{batch_session_id}")
        original_dir = batch_dir / "original"
        sheets_dir = batch_dir / "sheets"
        
        original_dir.mkdir(parents=True, exist_ok=True)
        sheets_dir.mkdir(parents=True, exist_ok=True)
        
        original_file_path = original_dir / file.filename
        with open(original_file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"[定制化批量分析] 原始文件已保存 - path={original_file_path}")
        
        # 4. 拆分Excel文件
        logger.info(f"[定制化批量分析] 开始拆分Excel文件...")
        split_files = ExcelService.split_excel_file(
            source_file_path=str(original_file_path),
            output_dir=sheets_dir,
            batch_session_id=batch_session_id
        )
        
        sheet_count = len(split_files)
        logger.info(f"[定制化批量分析] 拆分完成 - sheet_count={sheet_count}")
        
        # 验证所有拆分文件都存在
        for sheet_info in split_files:
            split_path = Path(sheet_info["split_file_path"])
            if not split_path.exists():
                logger.error(f"[定制化批量分析] 拆分文件不存在: {split_path}")
                raise Exception(f"拆分文件不存在: {split_path}")
        
        # 5. 更新批量会话记录
        batch_session.original_file_path = str(original_file_path)
        batch_session.split_files_dir = str(sheets_dir)
        batch_session.sheet_count = sheet_count
        
        # 6. 为每个Sheet创建报告记录
        sheet_reports = []
        for sheet_info in split_files:
            sheet_report = CustomSheetReport(
                custom_batch_session_id=batch_session_id,
                sheet_name=sheet_info["sheet_name"],
                sheet_index=sheet_info["sheet_index"],
                split_file_path=sheet_info["split_file_path"],
                report_status="pending"
            )
            db.add(sheet_report)
            sheet_reports.append(sheet_report)
        
        db.commit()
        logger.info(f"[定制化批量分析] 批量会话和Sheet报告记录已创建")
        
        # 7. 返回结果
        return SuccessResponse(
            data={
                "batch_session_id": batch_session_id,
                "sheet_count": sheet_count,
                "sheets": [
                    {
                        "id": sr.id,
                        "sheet_name": sr.sheet_name,
                        "sheet_index": sr.sheet_index,
                        "split_file_path": sr.split_file_path,
                        "report_status": sr.report_status
                    }
                    for sr in sheet_reports
                ],
                "status": batch_session.status
            },
            message="文件上传成功，已拆分完成"
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"[定制化批量分析] 上传和拆分失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传和拆分失败: {str(e)}"
        )


@router.post("/custom-batch/analyze", response_model=SuccessResponse)
async def start_custom_batch_analysis(
    batch_session_id: int = Form(...),
    analysis_request: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    开始定制化批量分析（异步处理）
    复用现有的 generate_report 逻辑，对每个Sheet重复调用
    """
    logger.info(f"[定制化批量分析] 开始批量分析 - batch_session_id={batch_session_id}, user_id={current_user.id}")
    
    try:
        # 1. 获取批量会话（使用固定项目ID）
        batch_session = db.query(CustomBatchAnalysisSession).filter(
            CustomBatchAnalysisSession.id == batch_session_id,
            CustomBatchAnalysisSession.user_id == current_user.id
        ).first()
        
        if not batch_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="批量会话不存在或无权限访问"
            )
        
        # 2. 获取所有待处理的Sheet报告
        sheet_reports = db.query(CustomSheetReport).filter(
            CustomSheetReport.custom_batch_session_id == batch_session_id,
            CustomSheetReport.report_status == "pending"
        ).order_by(CustomSheetReport.sheet_index).all()
        
        if not sheet_reports:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有待处理的Sheet报告"
            )
        
        logger.info(f"[定制化批量分析] 找到 {len(sheet_reports)} 个待处理的Sheet")
        
        # 3. 更新批量会话状态
        batch_session.status = "processing"
        db.commit()
        
        # 4. 启动异步任务处理每个Sheet
        async def run_batch_analysis():
            """后台异步任务"""
            try:
                from app.core.database import SessionLocal
                background_db = SessionLocal()
                
                try:
                    background_sheet_reports = background_db.query(CustomSheetReport).filter(
                        CustomSheetReport.custom_batch_session_id == batch_session_id
                    ).order_by(CustomSheetReport.sheet_index).all()
                    
                    # 并发处理所有Sheet（使用定制化批量分析函数）
                    results = await process_all_custom_sheets_concurrently(
                        sheet_reports=background_sheet_reports,
                        analysis_request=analysis_request,
                        user_id=current_user.id,
                        batch_session_id=batch_session_id,
                        db=background_db
                    )
                    
                    # 更新批量会话状态
                    background_batch_session = background_db.query(CustomBatchAnalysisSession).filter(
                        CustomBatchAnalysisSession.id == batch_session_id
                    ).first()
                    
                    if background_batch_session:
                        completed_count = background_db.query(CustomSheetReport).filter(
                            CustomSheetReport.custom_batch_session_id == batch_session_id,
                            CustomSheetReport.report_status == "completed"
                        ).count()
                        
                        failed_count = background_db.query(CustomSheetReport).filter(
                            CustomSheetReport.custom_batch_session_id == batch_session_id,
                            CustomSheetReport.report_status == "failed"
                        ).count()
                        
                        total_count = background_batch_session.sheet_count
                        
                        if completed_count == total_count:
                            background_batch_session.status = "completed"
                        elif failed_count == total_count:
                            background_batch_session.status = "failed"
                        elif failed_count > 0:
                            background_batch_session.status = "partial_failed"
                        else:
                            background_batch_session.status = "processing"
                        
                        background_db.commit()
                        logger.info(f"[定制化批量分析] 批量分析完成 - batch_session_id={batch_session_id}, completed={completed_count}, failed={failed_count}")
                
                finally:
                    background_db.close()
            
            except Exception as e:
                logger.error(f"[定制化批量分析] 后台任务执行失败: {str(e)}", exc_info=True)
                from app.core.database import SessionLocal
                error_db = SessionLocal()
                try:
                    error_batch_session = error_db.query(CustomBatchAnalysisSession).filter(
                        CustomBatchAnalysisSession.id == batch_session_id
                    ).first()
                    if error_batch_session:
                        error_batch_session.status = "failed"
                        error_db.commit()
                finally:
                    error_db.close()
        
        # 启动后台任务
        asyncio.create_task(run_batch_analysis())
        
        # 5. 返回处理状态
        return SuccessResponse(
            data={
                "batch_session_id": batch_session_id,
                "status": "processing",
                "total_sheets": len(sheet_reports),
                "completed_sheets": 0
            },
            message="批量分析已开始，正在后台处理"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[定制化批量分析] 启动批量分析失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动批量分析失败: {str(e)}"
        )


@router.get("/custom-batch/{batch_session_id}/status", response_model=SuccessResponse)
async def get_custom_batch_analysis_status(
    batch_session_id: int = PathParam(..., description="批量会话ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取定制化批量分析状态
    """
    logger.info(f"[定制化批量分析] 查询状态 - batch_session_id={batch_session_id}, user_id={current_user.id}")
    
    # 1. 获取批量会话（使用固定项目ID）
    batch_session = db.query(CustomBatchAnalysisSession).filter(
        CustomBatchAnalysisSession.id == batch_session_id,
        CustomBatchAnalysisSession.user_id == current_user.id
    ).first()
    
    if not batch_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批量会话不存在或无权限访问"
        )
    
    # 2. 获取所有Sheet报告
    sheet_reports = db.query(CustomSheetReport).filter(
        CustomSheetReport.custom_batch_session_id == batch_session_id
    ).order_by(CustomSheetReport.sheet_index).all()
    
    # 3. 统计状态
    total_sheets = len(sheet_reports)
    completed_sheets = sum(1 for sr in sheet_reports if sr.report_status == "completed")
    failed_sheets = sum(1 for sr in sheet_reports if sr.report_status == "failed")
    generating_sheets = sum(1 for sr in sheet_reports if sr.report_status == "generating")
    
    # 4. 构建报告列表
    reports_data = []
    for sr in sheet_reports:
        report_data = {
            "id": sr.id,
            "sheet_name": sr.sheet_name,
            "sheet_index": sr.sheet_index,
            "report_status": sr.report_status,
        }
        
        if sr.report_status == "completed" and sr.report_content:
            report_data["report_content"] = sr.report_content
        elif sr.report_status == "failed" and sr.error_message:
            report_data["error_message"] = sr.error_message
        
        reports_data.append(report_data)
    
    return SuccessResponse(
        data={
            "batch_session_id": batch_session_id,
            "status": batch_session.status,
            "total_sheets": total_sheets,
            "completed_sheets": completed_sheets,
            "failed_sheets": failed_sheets,
            "generating_sheets": generating_sheets,
            "pending_sheets": total_sheets - completed_sheets - failed_sheets - generating_sheets,
            "reports": reports_data
        },
        message="状态查询成功"
    )


@router.get("/custom-batch/reports/{report_id}", response_model=SuccessResponse)
async def get_custom_sheet_report(
    report_id: int = PathParam(..., description="报告ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个报告详情（定制化批量分析）
    """
    logger.info(f"[定制化批量分析] 查询报告详情 - report_id={report_id}, user_id={current_user.id}")
    
    # 1. 获取报告
    sheet_report = db.query(CustomSheetReport).filter(
        CustomSheetReport.id == report_id
    ).first()
    
    if not sheet_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )
    
    # 2. 验证权限（通过批量会话验证，使用固定项目ID）
    batch_session = db.query(CustomBatchAnalysisSession).filter(
        CustomBatchAnalysisSession.id == sheet_report.custom_batch_session_id,
        CustomBatchAnalysisSession.user_id == current_user.id
    ).first()
    
    if not batch_session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此报告"
        )
    
    # 3. 构建响应数据
    report_data = {
        "id": sheet_report.id,
        "sheet_name": sheet_report.sheet_name,
        "sheet_index": sheet_report.sheet_index,
        "report_status": sheet_report.report_status,
        "report_content": sheet_report.report_content or {},
        "error_message": sheet_report.error_message,
        "created_at": sheet_report.created_at.isoformat() if sheet_report.created_at else None,
        "updated_at": sheet_report.updated_at.isoformat() if sheet_report.updated_at else None
    }
    
    return SuccessResponse(
        data=report_data,
        message="报告查询成功"
    )


@router.post("/custom-batch/reports/{report_id}/download")
async def download_custom_batch_report_pdf(
    report_id: int = PathParam(..., description="报告ID"),
    request_data: DownloadBatchReportRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    下载定制化批量分析报告PDF（支持图表图片）
    """
    import traceback
    logger.info(f"[定制化批量分析] ====== 开始下载报告PDF ======")
    logger.info(f"[定制化批量分析] report_id={report_id}, user_id={current_user.id}")
    logger.info(f"[定制化批量分析] 收到 {len(request_data.chart_images) if request_data.chart_images else 0} 个图表图片")
    
    try:
        # 1. 获取Sheet报告
        sheet_report = db.query(CustomSheetReport).filter(
            CustomSheetReport.id == report_id
        ).first()
        
        if not sheet_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )
        
        # 2. 验证权限（使用固定项目ID）
        batch_session = db.query(CustomBatchAnalysisSession).filter(
            CustomBatchAnalysisSession.id == sheet_report.custom_batch_session_id,
            CustomBatchAnalysisSession.user_id == current_user.id
        ).first()
        
        if not batch_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此报告"
            )
        
        # 3. 检查报告状态和内容
        if sheet_report.report_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"报告尚未完成，当前状态: {sheet_report.report_status}"
            )
        
        if not sheet_report.report_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告内容不存在"
            )
        
        # 4. 获取报告内容
        report_content = {
            "text": str(sheet_report.report_content.get("text", "")),
            "charts": sheet_report.report_content.get("charts", []) or [],
            "tables": sheet_report.report_content.get("tables", []) or [],
            "metrics": sheet_report.report_content.get("metrics", {}) or {}
        }
        
        if not report_content.get("text"):
            report_content["text"] = "报告内容为空"
        
        # 5. 处理图表图片
        chart_images_data = []
        if request_data.chart_images:
            for chart_img in request_data.chart_images:
                try:
                    image_data = chart_img.image.split(',')[1] if ',' in chart_img.image else chart_img.image
                    chart_images_data.append({
                        'index': chart_img.index,
                        'title': chart_img.title,
                        'image_data': image_data
                    })
                except Exception as e:
                    logger.error(f"[定制化批量分析] ✗ 解析图表图片失败: {str(e)}")
        
        # 6. 生成PDF
        try:
            from app.utils.pdf_generator import generate_report_pdf
            
            report_title = f"{sheet_report.sheet_name} - 数据分析报告"
            pdf_bytes = generate_report_pdf(
                title=report_title,
                report_content=report_content,
                session_id=sheet_report.custom_batch_session_id,
                chart_images=chart_images_data
            )
            logger.info(f"[定制化批量分析] PDF生成成功 - 大小: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"[定制化批量分析] PDF生成失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF生成失败: {str(e)}"
            )
        
        # 7. 返回PDF文件
        filename = f"{sheet_report.sheet_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"[定制化批量分析] ====== PDF下载失败 ======")
        logger.error(f"[定制化批量分析] 错误类型: {type(e).__name__}")
        logger.error(f"[定制化批量分析] 错误消息: {str(e)}")
        logger.error(f"[定制化批量分析] 完整堆栈:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成PDF失败: {str(e)}"
        )


@router.post("/custom-batch/sessions", response_model=SuccessResponse)
async def create_custom_batch_session(
    request_data: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新的定制化批量分析会话
    """
    title = request_data.get("title") if request_data else None
    logger.info(f"[定制化批量分析] 创建会话 - user_id={current_user.id}, title={title}")
    
    try:
        # 生成标题
        if not title:
            title = f"定制化批量分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建批量会话（初始状态为draft，等待上传文件）
        batch_session = CustomBatchAnalysisSession(
            user_id=current_user.id,
            original_file_name=title,
            original_file_path="",
            split_files_dir="",
            sheet_count=0,
            status="draft"  # 草稿状态，等待上传文件
        )
        db.add(batch_session)
        db.commit()
        db.refresh(batch_session)
        
        logger.info(f"[定制化批量分析] 会话创建成功 - batch_session_id={batch_session.id}, title={batch_session.original_file_name}")
        
        # 返回响应
        return SuccessResponse(
            data={
                "id": batch_session.id,
                "original_file_name": batch_session.original_file_name,
                "sheet_count": batch_session.sheet_count,
                "status": batch_session.status,
                "created_at": batch_session.created_at.isoformat() if batch_session.created_at else None,
                "updated_at": batch_session.updated_at.isoformat() if batch_session.updated_at else None
            },
            message="定制化批量分析会话创建成功"
        )
    except Exception as e:
        logger.error(f"[定制化批量分析] 创建会话失败 - error={str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建定制化批量分析会话失败: {str(e)}"
        )


@router.get("/custom-batch/sessions", response_model=SuccessResponse)
async def get_custom_batch_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取定制化批量分析会话列表
    """
    logger.info(f"[定制化批量分析] 查询会话列表 - user_id={current_user.id}")
    
    # 1. 查询批量会话（使用固定项目ID）
    query = db.query(CustomBatchAnalysisSession).filter(
        CustomBatchAnalysisSession.user_id == current_user.id
    ).order_by(CustomBatchAnalysisSession.created_at.desc())
    
    # 2. 分页
    total = query.count()
    sessions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 3. 构建响应数据
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            "id": session.id,
            "original_file_name": session.original_file_name,
            "sheet_count": session.sheet_count,
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None
        })
    
    return SuccessResponse(
        data={
            "sessions": sessions_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        },
        message="会话列表查询成功"
    )


@router.delete("/custom-batch/sessions/{batch_session_id}", response_model=SuccessResponse)
async def delete_custom_batch_session(
    batch_session_id: int = PathParam(..., description="批量会话ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除定制化批量分析会话
    """
    logger.info(f"[定制化批量分析] 删除会话 - batch_session_id={batch_session_id}, user_id={current_user.id}")
    
    try:
        # 1. 查询批量会话（使用固定项目ID）
        batch_session = db.query(CustomBatchAnalysisSession).filter(
            CustomBatchAnalysisSession.id == batch_session_id,
            CustomBatchAnalysisSession.user_id == current_user.id
        ).first()
        
        if not batch_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="批量会话不存在或无权限访问"
            )
        
        # 2. 删除会话（级联删除会同时删除相关的CustomSheetReport记录）
        db.delete(batch_session)
        db.commit()
        
        logger.info(f"[定制化批量分析] 会话删除成功 - batch_session_id={batch_session_id}")
        
        return SuccessResponse(
            data={"deleted_id": batch_session_id},
            message="会话删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[定制化批量分析] 删除会话失败 - batch_session_id={batch_session_id}, error={str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )
