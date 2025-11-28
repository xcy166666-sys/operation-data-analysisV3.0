"""
工作流管理API（简化版，移除项目依赖）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from loguru import logger

from app.api.deps import get_db
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    FunctionWorkflowBind, FunctionWorkflowResponse,
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ExecuteWorkflowRequest, ExecuteWorkflowResponse
)
from app.schemas.common import SuccessResponse
from app.services.workflow_service import WorkflowService
from app.auth.dependencies import get_current_active_user, get_current_superadmin
from app.models.user import User

router = APIRouter()

# 固定项目ID（单项目系统）
DEFAULT_PROJECT_ID = 1


# ===== 辅助函数 =====

def format_conversation_history(
    messages: List[Dict], 
    max_messages: int = 10,
    max_chars: int = 2000
) -> str:
    """
    格式化对话历史为文本，用于上下文管理
    """
    if not messages:
        return ""
    
    recent_messages = messages[-(max_messages * 2):]
    
    history_lines = []
    total_chars = 0
    
    for msg in recent_messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        line = f"{role}: {content}"
        
        if total_chars + len(line) > max_chars:
            if not history_lines:
                remaining = max_chars - total_chars
                line = line[:remaining] + "..."
                history_lines.append(line)
            break
        
        history_lines.append(line)
        total_chars += len(line)
    
    return "\n".join(history_lines)


# ===== 工作流管理 =====

@router.get("", response_model=SuccessResponse[List[WorkflowResponse]])
async def get_workflows(
    category: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取工作流列表（简化版，移除project_id参数）
    """
    workflows = WorkflowService.get_workflows(
        db, category, platform, is_active
    )
    
    return SuccessResponse(
        data=[WorkflowResponse.model_validate(w) for w in workflows]
    )


@router.post("", response_model=SuccessResponse[WorkflowResponse])
async def create_workflow(
    workflow_data: WorkflowCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建工作流（用户级配置，每个用户可以创建自己的工作流）
    """
    workflow = WorkflowService.create_workflow(
        db, workflow_data, current_user.id
    )
    
    return SuccessResponse(
        data=WorkflowResponse.model_validate(workflow),
        message="工作流创建成功"
    )


# ===== 功能工作流绑定 =====

@router.get("/functions")
async def get_all_function_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有功能工作流绑定（简化版，移除project_id参数）"""
    try:
        bindings = WorkflowService.get_function_workflows(db)
        
        result = []
        for b in bindings:
            result.append({
                "id": b.id,
                "project_id": b.project_id,  # 固定为1
                "function_key": b.function_key,
                "workflow_id": b.workflow_id,
                "workflow": {
                    "id": b.workflow.id,
                    "name": b.workflow.name,
                    "description": b.workflow.description,
                    "platform": b.workflow.platform,
                    "config": b.workflow.config
                } if b.workflow else None,
                "created_at": b.created_at.isoformat(),
                "updated_at": b.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "data": result,
            "message": "获取成功"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取功能工作流列表失败: {str(e)}"
        )


@router.post("/functions/bind")
async def bind_function_workflow(
    binding_data: FunctionWorkflowBind = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    绑定功能到工作流（用户级配置，每个用户可以配置自己的工作流）
    """
    binding = WorkflowService.bind_function_workflow(
        db,
        binding_data.function_key,
        binding_data.workflow_id,
        current_user.id  # 用户级绑定
    )
    
    return SuccessResponse(
        data=FunctionWorkflowResponse.model_validate(binding),
        message="工作流配置成功"
    )


@router.get("/functions/{function_key}")
async def get_function_workflow(
    function_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取功能绑定的工作流（优先返回用户配置，如果没有则返回全局配置）"""
    binding = WorkflowService.get_function_workflow(db, function_key, current_user.id)
    
    if not binding:
        return {
            "success": True,
            "data": None,
            "message": "该功能尚未配置工作流"
        }
    
    return SuccessResponse(data=FunctionWorkflowResponse.model_validate(binding))


# ===== 对话记录 =====

@router.get("/conversations")
async def get_conversations(
    function_key: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户对话列表（简化版，移除project_id参数）"""
    try:
        conversations = WorkflowService.get_user_conversations(
            db, current_user.id, function_key
        )
        
        result = []
        for c in conversations:
            result.append({
                "id": c.id,
                "user_id": c.user_id,
                "project_id": c.project_id,  # 固定为1
                "function_key": c.function_key,
                "workflow_id": c.workflow_id,
                "title": c.title,
                "messages": c.messages,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "data": result,
            "message": "获取成功"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话列表失败: {str(e)}"
        )


@router.post("/conversations")
async def create_conversation(
    conversation_data: ConversationCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建对话（简化版，移除project_id参数）"""
    conversation = WorkflowService.create_conversation(
        db,
        current_user.id,
        conversation_data.function_key,
        conversation_data.workflow_id,
        conversation_data.title,
        [msg.dict() for msg in conversation_data.messages]
    )
    
    return SuccessResponse(
        data=ConversationResponse.model_validate(conversation),
        message="对话创建成功"
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
):
    """获取对话详情"""
    conversation = WorkflowService.get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    return SuccessResponse(data=ConversationResponse.model_validate(conversation))


@router.put("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    conversation_data: ConversationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
):
    """更新对话"""
    conversation = WorkflowService.update_conversation(
        db,
        conversation_id,
        conversation_data.title,
        [msg.dict() for msg in conversation_data.messages] if conversation_data.messages else None
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    return SuccessResponse(
        data=ConversationResponse.model_validate(conversation),
        message="对话更新成功"
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
):
    """删除对话"""
    success = WorkflowService.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    return SuccessResponse(message="对话删除成功")


# ===== 工作流执行 =====

@router.post("/execute")
async def execute_workflow(
    request_data: ExecuteWorkflowRequest = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    执行工作流（简化版，移除project_id参数）
    
    根据工作流平台调用相应的API：
    - Dify: 调用Dify API
    - Langchain: 执行本地Langchain（待实现）
    - Ragflow: 调用Ragflow API（待实现）
    """
    from app.services.dify_service import DifyService
    
    logger.info(f"[工作流执行] 收到请求 - workflow_id={request_data.workflow_id}, function_key={request_data.function_key}, user_id={current_user.id}")
    
    # 获取工作流信息
    workflow = WorkflowService.get_workflow_by_id(db, request_data.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    logger.info(f"[工作流执行] 找到工作流 - name={workflow.name}, platform={workflow.platform}")
    
    # 根据平台执行不同的逻辑
    if workflow.platform == "dify":
        config = workflow.config or {}
        api_url = config.get("api_url")
        api_key = config.get("api_key")
        workflow_id = config.get("workflow_id")
        
        if not all([api_url, api_key, workflow_id]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dify工作流配置不完整"
            )
        
        # 获取对话历史（如果有conversation_id）
        history_text = ""
        if request_data.conversation_id:
            try:
                conversation = WorkflowService.get_conversation_by_id(
                    db, 
                    request_data.conversation_id
                )
                
                if conversation and conversation.messages:
                    max_messages_map = {
                        "operation_data_analysis": 10,
                        "default": 10
                    }
                    max_messages = max_messages_map.get(
                        request_data.function_key, 
                        max_messages_map["default"]
                    )
                    
                    history_text = format_conversation_history(
                        conversation.messages,
                        max_messages=max_messages,
                        max_chars=2000
                    )
            except Exception as e:
                logger.warning(f"获取对话历史失败: {str(e)}")
        
        # 准备输入参数
        input_field = config.get("input_field", "input")
        history_field = config.get("history_field", "history")
        
        inputs = {
            input_field: request_data.input,
        }
        
        extra_inputs = config.get("extra_inputs", {})
        if extra_inputs:
            inputs.update(extra_inputs)
        if request_data.extra_inputs:
            inputs.update(request_data.extra_inputs)
        
        if history_text:
            inputs[history_field] = history_text
            inputs["has_context"] = True
        else:
            inputs["has_context"] = False
        
        logger.info(f"[工作流执行] 准备调用Dify API - 完整inputs: {inputs}")

        # 使用blocking模式调用Dify（移除project_id参数）
        result = await DifyService.run_workflow(
            api_url=api_url,
            api_key=api_key,
            workflow_id=workflow_id,
            user_id=current_user.id,
            function_key=request_data.function_key,
            inputs=inputs,
            conversation_id=request_data.conversation_id,
            response_mode="blocking",
            workflow_type="workflow"
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Dify执行失败")
            )
        
        dify_data = result.get("data", {})
        workflow_data = dify_data.get("data", {})
        outputs = workflow_data.get("outputs", {})
        workflow_status = workflow_data.get("status", "completed")

        if workflow_status == "failed":
            error_msg = workflow_data.get("error", "工作流执行失败")
            return SuccessResponse(
                data=ExecuteWorkflowResponse(
                    execution_id=dify_data.get("workflow_run_id", f"exec_{workflow.id}"),
                    status="failed",
                    output=f"工作流执行失败：{error_msg}"
                ),
                message="工作流执行失败"
            )
        
        output = (
            outputs.get("text") or
            outputs.get("result") or
            outputs.get("output") or
            str(outputs) if outputs else
            "无响应内容"
        )
        
        return SuccessResponse(
            data=ExecuteWorkflowResponse(
                execution_id=dify_data.get("workflow_run_id", f"exec_{workflow.id}"),
                status=workflow_status,
                output=output
            ),
            message="工作流执行成功"
        )
    
    elif workflow.platform == "langchain":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Langchain平台暂未实现"
        )
    
    elif workflow.platform == "ragflow":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Ragflow平台暂未实现"
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的平台: {workflow.platform}"
        )


@router.post("/execute-stream")
async def execute_workflow_stream(
    request_data: ExecuteWorkflowRequest = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    流式执行工作流（SSE）（简化版，移除project_id参数）
    
    返回Server-Sent Events流，实时推送工作流执行结果
    """
    from app.services.dify_service import DifyService
    
    # 获取工作流信息
    workflow = WorkflowService.get_workflow_by_id(db, request_data.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    # 只支持Dify平台的流式执行
    if workflow.platform != "dify":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有Dify平台支持流式执行"
        )
    
    config = workflow.config or {}
    api_url = config.get("api_url")
    api_key = config.get("api_key")
    workflow_id = config.get("workflow_id")
    
    if not all([api_url, api_key, workflow_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工作流配置不完整"
        )
    
    # 准备输入参数
    input_field = config.get("input_field", "input")
    history_field = config.get("history_field", "history")
    
    inputs = {
        input_field: request_data.input,
    }
    
    extra_inputs = config.get("extra_inputs", {})
    if extra_inputs:
        inputs.update(extra_inputs)

    if request_data.extra_inputs:
        inputs.update(request_data.extra_inputs)
    
    # 如果有对话历史，添加到inputs
    history_text = ""
    if request_data.conversation_id:
        try:
            conversation = WorkflowService.get_conversation_by_id(
                db,
                request_data.conversation_id
            )
            if conversation and conversation.messages:
                max_messages_map = {
                    "operation_data_analysis": 10,
                    "default": 10
                }
                max_messages = max_messages_map.get(
                    request_data.function_key,
                    max_messages_map["default"]
                )
                history_text = format_conversation_history(
                    conversation.messages,
                    max_messages=max_messages,
                    max_chars=2000
                )
        except Exception as e:
            logger.warning(f"获取对话历史失败: {str(e)}")
    
    if history_text:
        inputs[history_field] = history_text
        inputs["has_context"] = True
    else:
        inputs["has_context"] = False
    
    # 创建流式响应（移除project_id参数）
    async def event_generator():
        try:
            async for chunk in DifyService.run_workflow_streaming(
                api_url=api_url,
                api_key=api_key,
                workflow_id=workflow_id,
                user_id=current_user.id,
                function_key=request_data.function_key,
                inputs=inputs,
                conversation_id=request_data.conversation_id
            ):
                yield chunk
        except Exception as e:
            logger.error(f"流式执行异常: {str(e)}")
            yield f"data: {{\"event\": \"error\", \"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ===== 工作流CRUD =====

@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
):
    """获取工作流详情"""
    workflow = WorkflowService.get_workflow_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    return SuccessResponse(data=WorkflowResponse.model_validate(workflow))


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin)
):
    """更新工作流（需要超级管理员权限）"""
    workflow = WorkflowService.update_workflow(db, workflow_id, workflow_data)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    return SuccessResponse(
        data=WorkflowResponse.model_validate(workflow),
        message="工作流更新成功"
    )


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin)
):
    """删除工作流（需要超级管理员权限）"""
    success = WorkflowService.delete_workflow(db, workflow_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    return SuccessResponse(message="工作流删除成功")

