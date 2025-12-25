"""
工作流服务（简化版，移除项目依赖）
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowBinding
from app.models.session import AnalysisSession
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


# 固定项目ID（单项目系统）
DEFAULT_PROJECT_ID = 1


class WorkflowService:
    """工作流服务类"""
    
    @staticmethod
    def create_workflow(
        db: Session,
        workflow_data: WorkflowCreate,
        created_by: int
    ) -> Workflow:
        """创建工作流（单项目系统，不需要project_id）"""
        workflow = Workflow(
            name=workflow_data.name,
            category=workflow_data.category,
            platform=workflow_data.platform,
            config=workflow_data.config,
            description=workflow_data.description,
            is_active=workflow_data.is_active,
            created_by=created_by
        )
        
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        
        return workflow
    
    @staticmethod
    def get_workflow_by_id(db: Session, workflow_id: int) -> Optional[Workflow]:
        """通过ID获取工作流"""
        return db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    @staticmethod
    def get_workflows(
        db: Session,
        category: Optional[str] = None,
        platform: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Workflow]:
        """获取工作流列表（单项目系统，不需要project_id过滤）"""
        query = db.query(Workflow)
        
        if category:
            query = query.filter(Workflow.category == category)
        if platform:
            query = query.filter(Workflow.platform == platform)
        if is_active is not None:
            query = query.filter(Workflow.is_active == is_active)
        
        return query.order_by(Workflow.created_at.desc()).all()
    
    @staticmethod
    def update_workflow(
        db: Session,
        workflow_id: int,
        workflow_data: WorkflowUpdate
    ) -> Optional[Workflow]:
        """更新工作流"""
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return None
        
        if workflow_data.name is not None:
            workflow.name = workflow_data.name
        if workflow_data.category is not None:
            workflow.category = workflow_data.category
        if workflow_data.platform is not None:
            workflow.platform = workflow_data.platform
        if workflow_data.config is not None:
            workflow.config = workflow_data.config
        if workflow_data.description is not None:
            workflow.description = workflow_data.description
        if workflow_data.is_active is not None:
            workflow.is_active = workflow_data.is_active
        
        db.commit()
        db.refresh(workflow)
        
        return workflow
    
    @staticmethod
    def delete_workflow(db: Session, workflow_id: int) -> bool:
        """删除工作流"""
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return False
        
        db.delete(workflow)
        db.commit()
        
        return True
    
    # ===== 功能工作流绑定 =====
    
    @staticmethod
    def bind_function_workflow(
        db: Session,
        function_key: str,
        workflow_id: int,
        user_id: Optional[int] = None,
        sheet_index: Optional[int] = None
    ) -> WorkflowBinding:
        """绑定功能到工作流（支持用户级配置，user_id为None表示全局配置，sheet_index用于定制化批量分析）"""
        # 检查是否已存在绑定
        query = db.query(WorkflowBinding).filter(
            WorkflowBinding.function_key == function_key
        )
        if user_id is not None:
            query = query.filter(WorkflowBinding.user_id == user_id)
        else:
            query = query.filter(WorkflowBinding.user_id.is_(None))
        
        # 对于定制化批量分析，需要匹配sheet_index
        if sheet_index is not None:
            query = query.filter(WorkflowBinding.sheet_index == sheet_index)
        else:
            query = query.filter(WorkflowBinding.sheet_index.is_(None))
        
        existing = query.first()
        
        if existing:
            # 更新绑定
            existing.workflow_id = workflow_id
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # 创建新绑定
            binding = WorkflowBinding(
                function_key=function_key,
                workflow_id=workflow_id,
                user_id=user_id,
                sheet_index=sheet_index
            )
            db.add(binding)
            db.commit()
            db.refresh(binding)
            return binding
    
    @staticmethod
    def get_function_workflow(
        db: Session,
        function_key: str,
        user_id: Optional[int] = None
    ) -> Optional[WorkflowBinding]:
        """获取功能绑定的工作流（优先返回用户配置，如果没有则返回全局配置）"""
        # 先查找用户配置
        if user_id is not None:
            user_binding = db.query(WorkflowBinding).filter(
                WorkflowBinding.function_key == function_key,
                WorkflowBinding.user_id == user_id
            ).first()
            if user_binding:
                return user_binding
        
        # 如果没有用户配置，返回全局配置
        return db.query(WorkflowBinding).filter(
            WorkflowBinding.function_key == function_key,
            WorkflowBinding.user_id.is_(None)
        ).first()
    
    @staticmethod
    def get_function_workflows(
        db: Session
    ) -> List[WorkflowBinding]:
        """获取所有功能工作流绑定（单项目系统，不需要project_id过滤）"""
        return db.query(WorkflowBinding).all()
    
    # ===== 对话记录 =====
    
    @staticmethod
    def create_conversation(
        db: Session,
        user_id: int,
        function_key: str,
        workflow_id: Optional[int] = None,
        title: Optional[str] = None,
        messages: List[dict] = None
    ) -> AnalysisSession:
        """创建对话（单项目系统，不需要project_id）"""
        conversation = AnalysisSession(
            user_id=user_id,
            function_key=function_key,
            workflow_id=workflow_id,
            title=title or f"新对话 {function_key}",
            messages=messages or []
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    def get_conversation_by_id(db: Session, conversation_id: int) -> Optional[AnalysisSession]:
        """获取对话详情"""
        return db.query(AnalysisSession).filter(AnalysisSession.id == conversation_id).first()
    
    @staticmethod
    def get_user_conversations(
        db: Session,
        user_id: int,
        function_key: Optional[str] = None
    ) -> List[AnalysisSession]:
        """获取用户对话列表（单项目系统，不需要project_id过滤）"""
        query = db.query(AnalysisSession).filter(
            AnalysisSession.user_id == user_id
        )
        
        if function_key:
            query = query.filter(AnalysisSession.function_key == function_key)
        
        return query.order_by(AnalysisSession.updated_at.desc()).all()
    
    @staticmethod
    def update_conversation(
        db: Session,
        conversation_id: int,
        title: Optional[str] = None,
        messages: Optional[List[dict]] = None
    ) -> Optional[AnalysisSession]:
        """更新对话"""
        conversation = db.query(AnalysisSession).filter(AnalysisSession.id == conversation_id).first()
        if not conversation:
            return None
        
        if title is not None:
            conversation.title = title
        if messages is not None:
            conversation.messages = messages
        
        db.commit()
        db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    def append_message(
        db: Session,
        conversation_id: int,
        role: str,
        content: str
    ) -> Optional[AnalysisSession]:
        """追加消息到对话"""
        conversation = db.query(AnalysisSession).filter(AnalysisSession.id == conversation_id).first()
        if not conversation:
            return None
        
        messages = conversation.messages or []
        messages.append({"role": role, "content": content})
        conversation.messages = messages
        
        db.commit()
        db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    def delete_conversation(db: Session, conversation_id: int) -> bool:
        """删除对话"""
        conversation = db.query(AnalysisSession).filter(AnalysisSession.id == conversation_id).first()
        if not conversation:
            return False
        
        db.delete(conversation)
        db.commit()
        
        return True

