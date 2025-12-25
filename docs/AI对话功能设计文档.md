# AI对话功能设计文档

## 1. 功能概述

基于test.html的对话功能，整合到运营数据分析系统中，实现用户与AI的多轮对话，动态调整图表和报告内容。

### 1.1 核心特性
- **多轮对话**：支持conversation_id维持对话上下文
- **实时调整**：通过对话持续修改图表和报告
- **流式输出**：使用SSE实时显示AI生成内容
- **状态管理**：保存对话历史和会话状态

### 1.2 参考实现
- **test.html**：Dify工作流对话实现
- **现有代码**：bailian_dialog_service.py、dialog_manager.py

## 2. 系统架构

### 2.1 技术栈
- **前端**：Vue 3 + Element Plus
- **后端**：FastAPI + 阿里百炼API
- **存储**：PostgreSQL (会话) + 内存 (对话历史)

### 2.2 核心组件

#### 前端组件
\\\
DialogPanel.vue (对话面板)
 对话历史显示
 消息输入框
 发送按钮
 图表预览区
\\\

#### 后端服务
\\\
BailianDialogService (对话服务)
 process_dialog_message() - 处理对话消息
 _build_dialog_context() - 构建对话上下文
 _call_bailian_dialog_api() - 调用阿里百炼API
 _parse_dialog_response() - 解析AI回复

DialogManager (对话管理器)
 save_message() - 保存消息
 get_conversation_history() - 获取历史
 save_session_state() - 保存会话状态
 clear_session_history() - 清除历史
\\\

## 3. 数据流设计

### 3.1 对话流程
\\\
用户输入消息
    
前端发送请求 (POST /api/v1/operation/dialog)
    
后端接收请求
    
构建对话上下文 (当前图表 + 用户消息)
    
调用阿里百炼API (带conversation_id)
    
解析AI回复 (文字 + 图表修改指令)
    
应用图表修改
    
保存对话历史
    
返回响应 (AI回复 + 修改后的图表)
    
前端更新UI
\\\

### 3.2 conversation_id管理
- **首次对话**：conversation_id = null，后端生成新ID
- **后续对话**：使用已有conversation_id维持上下文
- **存储位置**：session_states (DialogManager)

## 4. API设计

### 4.1 发送对话消息
\\\http
POST /api/v1/operation/dialog
Content-Type: application/json

{
  "session_id": 123,
  "message": "请将第一个图表改为柱状图",
  "conversation_id": "uuid-xxx" // 可选，首次为null
}
\\\

**响应**：
\\\json
{
  "success": true,
  "data": {
    "response": "已将第一个图表改为柱状图",
    "modified_charts": [...],
    "conversation_id": "uuid-xxx",
    "action_type": "modify_chart"
  }
}
\\\

### 4.2 获取对话历史
\\\http
GET /api/v1/operation/dialog/history?session_id=123&limit=20
\\\

**响应**：
\\\json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "生成报告",
        "timestamp": "2025-12-19T10:00:00Z"
      },
      {
        "id": "msg-2",
        "role": "assistant",
        "content": "报告已生成",
        "timestamp": "2025-12-19T10:00:05Z",
        "modified_charts": [...]
      }
    ]
  }
}
\\\

### 4.3 清除对话历史
\\\http
DELETE /api/v1/operation/dialog/history?session_id=123
\\\

## 5. 前端实现

### 5.1 DialogPanel组件结构
\\\ue
<template>
  <div class="dialog-panel">
    <!-- 对话历史 -->
    <div class="dialog-history">
      <div v-for="msg in messages" :key="msg.id" :class="msg.role">
        {{ msg.content }}
      </div>
    </div>
    
    <!-- 输入区 -->
    <div class="dialog-input">
      <el-input v-model="userMessage" @keyup.enter="sendMessage" />
      <el-button @click="sendMessage">发送</el-button>
    </div>
  </div>
</template>
\\\

### 5.2 核心方法
\\\	ypescript
// 发送消息
async sendMessage() {
  const response = await dialogApi.sendMessage({
    session_id: this.sessionId,
    message: this.userMessage,
    conversation_id: this.conversationId
  })
  
  // 更新对话历史
  this.messages.push({
    role: 'user',
    content: this.userMessage
  })
  
  this.messages.push({
    role: 'assistant',
    content: response.data.response
  })
  
  // 更新conversation_id
  this.conversationId = response.data.conversation_id
  
  // 更新图表
  if (response.data.modified_charts) {
    this.('charts-updated', response.data.modified_charts)
  }
}

// 加载历史
async loadHistory() {
  const response = await dialogApi.getHistory(this.sessionId)
  this.messages = response.data.messages
}
\\\

## 6. 后端实现

### 6.1 API路由
\\\python
# backend/app/api/v1/operation_dialog.py

@router.post("/dialog")
async def send_dialog_message(
    request: DialogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 1. 获取会话
    session = get_session(db, request.session_id, current_user.id)
    
    # 2. 获取当前图表
    current_charts = get_current_charts(session)
    
    # 3. 调用对话服务
    dialog_service = BailianDialogService()
    result = await dialog_service.process_dialog_message(
        session_id=str(request.session_id),
        user_message=request.message,
        current_charts=current_charts,
        conversation_id=request.conversation_id
    )
    
    # 4. 保存对话历史
    dialog_manager = DialogManager()
    await dialog_manager.save_message(
        session_id=str(request.session_id),
        role="user",
        content=request.message
    )
    await dialog_manager.save_message(
        session_id=str(request.session_id),
        role="assistant",
        content=result["response"],
        modified_charts=result["modified_charts"]
    )
    
    # 5. 保存会话状态
    await dialog_manager.save_session_state(
        session_id=str(request.session_id),
        conversation_id=result["conversation_id"]
    )
    
    return SuccessResponse(data=result)
\\\

### 6.2 对话服务实现
\\\python
# backend/app/services/bailian_dialog_service.py

async def process_dialog_message(
    self,
    session_id: str,
    user_message: str,
    current_charts: List[Dict],
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    # 1. 构建上下文
    context = await self._build_dialog_context(
        user_message=user_message,
        current_charts=current_charts,
        session_id=session_id
    )
    
    # 2. 调用API
    api_response = await self._call_bailian_dialog_api(
        context=context,
        conversation_id=conversation_id
    )
    
    # 3. 解析回复
    parsed = await self._parse_dialog_response(api_response)
    
    # 4. 应用修改
    if parsed["action_type"] == "modify_chart":
        modified_charts = await self._apply_chart_modifications(
            current_charts,
            parsed["modifications"]
        )
    else:
        modified_charts = current_charts
    
    return {
        "response": parsed["response"],
        "modified_charts": modified_charts,
        "conversation_id": api_response["conversation_id"],
        "action_type": parsed["action_type"]
    }
\\\

## 7. 图表修改机制

### 7.1 修改指令格式
\\\json
{
  "action_type": "modify_chart",
  "modifications": [
    {
      "chart_index": 0,
      "modification_type": "change_type",
      "config": {
        "type": "bar"
      }
    }
  ]
}
\\\

### 7.2 支持的修改类型
- **change_type**：修改图表类型 (line/bar/pie/scatter)
- **change_color**：修改颜色
- **add_filter**：添加数据筛选
- **modify_style**：修改样式
- **update_data_range**：更新数据范围

## 8. 实施计划

### 阶段1：后端API开发 (2天)
- [ ] 创建operation_dialog.py路由
- [ ] 实现send_dialog_message接口
- [ ] 实现get_dialog_history接口
- [ ] 实现clear_dialog_history接口
- [ ] 完善BailianDialogService
- [ ] 测试API功能

### 阶段2：前端组件开发 (2天)
- [ ] 完善DialogPanel.vue组件
- [ ] 实现消息发送功能
- [ ] 实现历史加载功能
- [ ] 实现图表更新联动
- [ ] 优化UI交互

### 阶段3：集成测试 (1天)
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 错误处理完善
- [ ] 文档更新

## 9. 技术难点

### 9.1 conversation_id管理
- **问题**：阿里百炼API可能不直接支持conversation_id
- **解决**：使用UUID生成，在DialogManager中维护映射关系

### 9.2 图表修改解析
- **问题**：AI回复格式不稳定
- **解决**：使用正则表达式 + JSON解析，支持多种格式

### 9.3 对话历史存储
- **问题**：内存存储不持久
- **解决**：后续迁移到Redis或数据库

## 10. 测试用例

### 10.1 基础对话
- 用户："你好"
- AI："您好！我是数据分析助手..."

### 10.2 图表修改
- 用户："将第一个图表改为柱状图"
- AI："已将第一个图表改为柱状图" + 修改后的图表

### 10.3 数据分析
- 用户："分析一下用户留存趋势"
- AI："根据数据分析..." + 分析结果

## 11. 后续优化

- [ ] 支持流式输出 (SSE)
- [ ] 支持语音输入
- [ ] 支持图表导出
- [ ] 支持对话分享
- [ ] 支持多语言
