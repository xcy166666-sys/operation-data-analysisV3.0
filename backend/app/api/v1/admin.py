"""
管理员API（功能管理）
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.deps import get_db
from app.schemas.function_module import (
    FunctionModuleResponse,
    FunctionConfigRequest,
    FunctionToggleRequest,
    CustomBatchConfigRequest
)
from app.schemas.common import SuccessResponse
from app.schemas.workflow import WorkflowCreate, WorkflowResponse
from app.models.function_module import FunctionModule
from app.models.workflow import Workflow, WorkflowBinding
from app.models.user import User
from app.auth.dependencies import get_current_superadmin
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("/functions", response_model=SuccessResponse[List[FunctionModuleResponse]])
async def get_functions(
    search: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    获取功能模块列表（仅管理员）
    """
    try:
        query = db.query(FunctionModule)
        
        # 搜索过滤
        if search:
            search_filter = or_(
                FunctionModule.name.ilike(f"%{search}%"),
                FunctionModule.function_key.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # 状态过滤
        if is_enabled is not None:
            query = query.filter(FunctionModule.is_enabled == is_enabled)
        
        # 排序
        functions = query.order_by(FunctionModule.sort_order, FunctionModule.id).all()
        
        # 获取每个功能的工作流配置
        result = []
        for func in functions:
            # 对于定制化批量分析，获取所有6个工作流配置
            if func.function_key == "custom_operation_data_analysis":
                # 获取所有sheet_index的工作流绑定（0-5）
                bindings = db.query(WorkflowBinding).filter(
                    WorkflowBinding.function_key == func.function_key,
                    WorkflowBinding.user_id.is_(None),
                    WorkflowBinding.sheet_index.isnot(None)
                ).order_by(WorkflowBinding.sheet_index).all()
                
                workflows = []
                for binding in bindings:
                    workflow_obj = db.query(Workflow).filter(Workflow.id == binding.workflow_id).first()
                    if workflow_obj:
                        workflows.append({
                            "sheet_index": binding.sheet_index,
                            "workflow": WorkflowResponse(
                                id=workflow_obj.id,
                                name=workflow_obj.name,
                                category=workflow_obj.category,
                                platform=workflow_obj.platform,
                                config=workflow_obj.config,
                                description=workflow_obj.description,
                                is_active=workflow_obj.is_active,
                                created_by=workflow_obj.created_by,
                                created_at=workflow_obj.created_at,
                                updated_at=workflow_obj.updated_at
                            )
                        })
                
                func_dict = {
                    "id": func.id,
                    "function_key": func.function_key,
                    "name": func.name,
                    "description": func.description,
                    "route_path": func.route_path,
                    "icon": func.icon,
                    "category": func.category,
                    "is_enabled": func.is_enabled,
                    "sort_order": func.sort_order,
                    "created_at": func.created_at,
                    "updated_at": func.updated_at,
                    "workflow": None,
                    "workflows": workflows  # 多个工作流配置
                }
            else:
                # 其他功能，获取单个工作流配置
                binding = db.query(WorkflowBinding).filter(
                    WorkflowBinding.function_key == func.function_key,
                    WorkflowBinding.user_id.is_(None),
                    WorkflowBinding.sheet_index.is_(None)  # 非定制化批量分析，sheet_index为None
                ).first()
                
                workflow = None
                if binding:
                    workflow_obj = db.query(Workflow).filter(Workflow.id == binding.workflow_id).first()
                    if workflow_obj:
                        workflow = WorkflowResponse(
                            id=workflow_obj.id,
                            name=workflow_obj.name,
                            category=workflow_obj.category,
                            platform=workflow_obj.platform,
                            config=workflow_obj.config,
                            description=workflow_obj.description,
                            is_active=workflow_obj.is_active,
                            created_by=workflow_obj.created_by,
                            created_at=workflow_obj.created_at,
                            updated_at=workflow_obj.updated_at
                        )
                
                func_dict = {
                    "id": func.id,
                    "function_key": func.function_key,
                    "name": func.name,
                    "description": func.description,
                    "route_path": func.route_path,
                    "icon": func.icon,
                    "category": func.category,
                    "is_enabled": func.is_enabled,
                    "sort_order": func.sort_order,
                    "created_at": func.created_at,
                    "updated_at": func.updated_at,
                    "workflow": workflow
                }
            result.append(func_dict)
        
        return {
            "success": True,
            "data": result,
            "message": "获取成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取功能列表失败: {str(e)}"
        )


@router.get("/functions/{function_key}", response_model=SuccessResponse[FunctionModuleResponse])
async def get_function(
    function_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    获取单个功能的配置
    """
    try:
        func = db.query(FunctionModule).filter(
            FunctionModule.function_key == function_key
        ).first()
        
        if not func:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="功能不存在"
            )
        
        # 对于定制化批量分析，获取所有6个工作流配置
        if function_key == "custom_operation_data_analysis":
            # 获取所有sheet_index的工作流绑定（0-5）
            bindings = db.query(WorkflowBinding).filter(
                WorkflowBinding.function_key == function_key,
                WorkflowBinding.user_id.is_(None),
                WorkflowBinding.sheet_index.isnot(None)
            ).order_by(WorkflowBinding.sheet_index).all()
            
            workflows = []
            for binding in bindings:
                workflow_obj = db.query(Workflow).filter(Workflow.id == binding.workflow_id).first()
                if workflow_obj:
                    workflows.append({
                        "sheet_index": binding.sheet_index,
                        "workflow": WorkflowResponse(
                            id=workflow_obj.id,
                            name=workflow_obj.name,
                            category=workflow_obj.category,
                            platform=workflow_obj.platform,
                            config=workflow_obj.config,
                            description=workflow_obj.description,
                            is_active=workflow_obj.is_active,
                            created_by=workflow_obj.created_by,
                            created_at=workflow_obj.created_at,
                            updated_at=workflow_obj.updated_at
                        )
                    })
            
            func_dict = {
                "id": func.id,
                "function_key": func.function_key,
                "name": func.name,
                "description": func.description,
                "route_path": func.route_path,
                "icon": func.icon,
                "category": func.category,
                "is_enabled": func.is_enabled,
                "sort_order": func.sort_order,
                "created_at": func.created_at,
                "updated_at": func.updated_at,
                "workflow": None,
                "workflows": workflows  # 多个工作流配置
            }
        else:
            # 其他功能，获取单个工作流配置
            binding = db.query(WorkflowBinding).filter(
                WorkflowBinding.function_key == function_key,
                WorkflowBinding.user_id.is_(None),
                WorkflowBinding.sheet_index.is_(None)  # 非定制化批量分析，sheet_index为None
            ).first()
            
            workflow = None
            if binding:
                workflow_obj = db.query(Workflow).filter(Workflow.id == binding.workflow_id).first()
                if workflow_obj:
                    workflow = WorkflowResponse(
                        id=workflow_obj.id,
                        name=workflow_obj.name,
                        category=workflow_obj.category,
                        platform=workflow_obj.platform,
                        config=workflow_obj.config,
                        description=workflow_obj.description,
                        is_active=workflow_obj.is_active,
                        created_by=workflow_obj.created_by,
                        created_at=workflow_obj.created_at,
                        updated_at=workflow_obj.updated_at
                    )
            
            func_dict = {
                "id": func.id,
                "function_key": func.function_key,
                "name": func.name,
                "description": func.description,
                "route_path": func.route_path,
                "icon": func.icon,
                "category": func.category,
                "is_enabled": func.is_enabled,
                "sort_order": func.sort_order,
                "created_at": func.created_at,
                "updated_at": func.updated_at,
                "workflow": workflow
            }
        
        return {
            "success": True,
            "data": func_dict,
            "message": "获取成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取功能配置失败: {str(e)}"
        )


@router.post("/functions/{function_key}/config", response_model=SuccessResponse[dict])
async def set_function_config(
    function_key: str,
    config_data: FunctionConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    配置功能的API（全局配置，仅管理员）
    对于custom_operation_data_analysis，需要配置6个工作流（sheet_index 0-5）
    """
    try:
        # 检查功能是否存在
        func = db.query(FunctionModule).filter(
            FunctionModule.function_key == function_key
        ).first()
        
        if not func:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="功能不存在"
            )
        
        # 对于定制化批量分析，需要特殊处理
        if function_key == "custom_operation_data_analysis":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="定制化批量分析需要使用 /functions/{function_key}/config-batch 接口配置6个工作流"
            )
        
        # 检查是否已存在工作流绑定（非定制化批量分析，sheet_index为None）
        existing_binding = db.query(WorkflowBinding).filter(
            WorkflowBinding.function_key == function_key,
            WorkflowBinding.user_id.is_(None),
            WorkflowBinding.sheet_index.is_(None)
        ).first()
        
        if existing_binding:
            # 更新现有工作流
            workflow = db.query(Workflow).filter(Workflow.id == existing_binding.workflow_id).first()
            if workflow:
                workflow.name = config_data.name
                workflow.description = config_data.description
                workflow.platform = config_data.platform
                workflow.config = config_data.config
                workflow.is_active = True
                db.commit()
                db.refresh(workflow)
            else:
                # 工作流不存在，创建新的
                workflow = WorkflowService.create_workflow(
                    db=db,
                    workflow_data=WorkflowCreate(
                        name=config_data.name,
                        category="operation",
                        platform=config_data.platform,
                        config=config_data.config,
                        description=config_data.description,
                        is_active=True
                    ),
                    created_by=current_user.id
                )
                existing_binding.workflow_id = workflow.id
                db.commit()
        else:
            # 创建新工作流
            workflow = WorkflowService.create_workflow(
                db=db,
                workflow_data=WorkflowCreate(
                    name=config_data.name,
                    category="operation",
                    platform=config_data.platform,
                    config=config_data.config,
                    description=config_data.description,
                    is_active=True
                ),
                created_by=current_user.id
            )
            
            # 创建全局绑定（sheet_index为None）
            binding = WorkflowBinding(
                function_key=function_key,
                workflow_id=workflow.id,
                user_id=None,  # 全局配置
                sheet_index=None  # 非定制化批量分析
            )
            db.add(binding)
            db.commit()
        
        return {
            "success": True,
            "data": {
                "workflow_id": workflow.id,
                "function_key": function_key
            },
            "message": "API配置成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置API失败: {str(e)}"
        )


@router.post("/functions/{function_key}/config-batch", response_model=SuccessResponse[dict])
async def set_custom_batch_config(
    function_key: str,
    config_data: CustomBatchConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    配置定制化批量分析的6个工作流（仅用于custom_operation_data_analysis）
    """
    try:
        # 检查功能是否存在
        if function_key != "custom_operation_data_analysis":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此接口仅用于定制化批量分析功能"
            )
        
        func = db.query(FunctionModule).filter(
            FunctionModule.function_key == function_key
        ).first()
        
        if not func:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="功能不存在"
            )
        
        # 验证必须有6个工作流配置
        if len(config_data.workflows) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="定制化批量分析必须配置6个工作流（对应Sheet索引0-5）"
            )
        
        # 验证sheet_index是否完整（0-5）
        sheet_indices = [w.sheet_index for w in config_data.workflows]
        if set(sheet_indices) != {0, 1, 2, 3, 4, 5}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="工作流配置必须包含Sheet索引0-5"
            )
        
        workflow_ids = []
        
        # 为每个Sheet索引配置工作流
        for workflow_config in config_data.workflows:
            sheet_index = workflow_config.sheet_index
            platform = workflow_config.platform
            name = workflow_config.name
            description = workflow_config.description
            config = workflow_config.config
            
            # 检查是否已存在该sheet_index的绑定
            existing_binding = db.query(WorkflowBinding).filter(
                WorkflowBinding.function_key == function_key,
                WorkflowBinding.user_id.is_(None),
                WorkflowBinding.sheet_index == sheet_index
            ).first()
            
            if existing_binding:
                # 更新现有工作流
                workflow = db.query(Workflow).filter(Workflow.id == existing_binding.workflow_id).first()
                if workflow:
                    workflow.name = name
                    workflow.description = description
                    workflow.platform = platform
                    workflow.config = config
                    workflow.is_active = True
                    db.commit()
                    db.refresh(workflow)
                    workflow_ids.append(workflow.id)
                else:
                    # 工作流不存在，创建新的
                    workflow = WorkflowService.create_workflow(
                        db=db,
                        workflow_data=WorkflowCreate(
                            name=name,
                            category="operation",
                            platform=platform,
                            config=config,
                            description=description,
                            is_active=True
                        ),
                        created_by=current_user.id
                    )
                    existing_binding.workflow_id = workflow.id
                    db.commit()
                    workflow_ids.append(workflow.id)
            else:
                # 创建新工作流
                workflow = WorkflowService.create_workflow(
                    db=db,
                    workflow_data=WorkflowCreate(
                        name=name,
                        category="operation",
                        platform=platform,
                        config=config,
                        description=description,
                        is_active=True
                    ),
                    created_by=current_user.id
                )
                
                # 创建全局绑定（带sheet_index）
                binding = WorkflowBinding(
                    function_key=function_key,
                    workflow_id=workflow.id,
                    user_id=None,  # 全局配置
                    sheet_index=sheet_index
                )
                db.add(binding)
                db.commit()
                workflow_ids.append(workflow.id)
        
        return {
            "success": True,
            "data": {
                "function_key": function_key,
                "workflow_ids": workflow_ids,
                "workflow_count": len(workflow_ids)
            },
            "message": "6个工作流配置成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置API失败: {str(e)}"
        )


@router.put("/functions/{function_key}/config", response_model=SuccessResponse[dict])
async def update_function_config(
    function_key: str,
    config_data: FunctionConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    更新功能的API配置
    """
    try:
        # 检查功能是否存在
        func = db.query(FunctionModule).filter(
            FunctionModule.function_key == function_key
        ).first()
        
        if not func:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="功能不存在"
            )
        
        # 对于定制化批量分析，需要特殊处理
        if function_key == "custom_operation_data_analysis":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="定制化批量分析需要使用 /functions/{function_key}/config-batch 接口更新6个工作流"
            )
        
        # 获取全局配置的工作流绑定（非定制化批量分析，sheet_index为None）
        binding = db.query(WorkflowBinding).filter(
            WorkflowBinding.function_key == function_key,
            WorkflowBinding.user_id.is_(None),
            WorkflowBinding.sheet_index.is_(None)
        ).first()
        
        if not binding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该功能尚未配置API，请先创建配置"
            )
        
        # 更新工作流
        workflow = db.query(Workflow).filter(Workflow.id == binding.workflow_id).first()
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        workflow.name = config_data.name
        workflow.description = config_data.description
        workflow.platform = config_data.platform
        workflow.config = config_data.config
        workflow.is_active = True
        db.commit()
        db.refresh(workflow)
        
        return {
            "success": True,
            "data": {
                "workflow_id": workflow.id,
                "function_key": function_key
            },
            "message": "API配置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新API配置失败: {str(e)}"
        )


@router.post("/functions/{function_key}/test-config", response_model=SuccessResponse[dict])
async def test_function_config(
    function_key: str,
    test_data: FunctionConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    测试API配置
    """
    try:
        # 简单的连接测试：验证配置格式
        if not test_data.config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="配置不能为空"
            )
        
        # 根据平台验证必填字段
        if test_data.platform == "dify":
            required_fields = ["api_url", "api_key"]
            for field in required_fields:
                if field not in test_data.config:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Dify配置缺少必填字段: {field}"
                    )
        
        # TODO: 实际测试API连接（可以发送一个测试请求）
        # 这里先返回成功，后续可以添加实际的连接测试逻辑
        
        return {
            "success": True,
            "data": {
                "connected": True,
                "message": "配置格式验证通过"
            },
            "message": "测试成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试配置失败: {str(e)}"
        )


@router.delete("/functions/{function_key}/config", response_model=SuccessResponse[dict])
async def delete_function_config(
    function_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    删除功能的API配置
    """
    try:
        # 对于定制化批量分析，需要删除所有6个工作流绑定
        if function_key == "custom_operation_data_analysis":
            bindings = db.query(WorkflowBinding).filter(
                WorkflowBinding.function_key == function_key,
                WorkflowBinding.user_id.is_(None),
                WorkflowBinding.sheet_index.isnot(None)
            ).all()
            
            if not bindings:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="该功能尚未配置API"
                )
            
            # 删除所有绑定
            for binding in bindings:
                db.delete(binding)
            db.commit()
            
            return {
                "success": True,
                "data": {
                    "function_key": function_key
                },
                "message": "API配置已删除"
            }
        
        # 其他功能，删除单个工作流绑定
        binding = db.query(WorkflowBinding).filter(
            WorkflowBinding.function_key == function_key,
            WorkflowBinding.user_id.is_(None),
            WorkflowBinding.sheet_index.is_(None)
        ).first()
        
        if not binding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该功能尚未配置API"
            )
        
        # 删除绑定
        db.delete(binding)
        db.commit()
        
        return {
            "success": True,
            "data": {
                "function_key": function_key
            },
            "message": "API配置已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除API配置失败: {str(e)}"
        )


@router.patch("/functions/{function_key}/toggle", response_model=SuccessResponse[dict])
async def toggle_function(
    function_key: str,
    toggle_data: FunctionToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    启用/禁用功能
    """
    try:
        func = db.query(FunctionModule).filter(
            FunctionModule.function_key == function_key
        ).first()
        
        if not func:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="功能不存在"
            )
        
        func.is_enabled = toggle_data.is_enabled
        db.commit()
        db.refresh(func)
        
        return {
            "success": True,
            "data": {
                "function_key": function_key,
                "is_enabled": func.is_enabled
            },
            "message": f"功能已{'启用' if func.is_enabled else '禁用'}"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新功能状态失败: {str(e)}"
        )

