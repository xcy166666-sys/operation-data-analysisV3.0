# AI编辑功能集成说明

## 概述

本文档说明AI编辑功能的集成情况和使用方式。

## 功能说明

### 已集成功能 ✅

#### 1. 文本AI编辑（通过AI对话面板）
- **位置**：左侧AI对话助手面板
- **触发方式**：选中报告中的文字
- **功能**：
  - 自动引用选中的文字到对话框
  - 提供快捷指令（润色、简化、扩写、改写）
  - 支持自定义修改指令
  - AI理解上下文进行修改
  - 自动更新报告内容

#### 2. 后端API
- **端点**：`POST /api/v1/operation/ai/text-edit`
- **功能**：接收文本编辑请求，调用AI服务
- **状态**：已实现并测试

### 未集成功能 ⏳

#### 1. 独立的文本编辑工具栏
- **原因**：与AI对话面板的选中文字功能冲突
- **决策**：保留AI对话面板的方式，移除独立工具栏
- **优势**：
  - 避免功能重复
  - 统一的交互体验
  - 更强大的对话式修改

#### 2. 图表AI编辑
- **状态**：组件已开发，但未集成到页面
- **原因**：需要先完善图表编辑的后端逻辑
- **计划**：后续版本集成

## 技术实现

### 前端实现

#### DataAnalysis.vue
```vue
<!-- 导入DialogPanel组件 -->
import DialogPanel from './components/DialogPanel.vue'

<!-- 使用DialogPanel -->
<DialogPanel
  v-if="showDialogPanel"
  :session-id="currentSessionId"
  :charts="reportContent?.charts || []"
  :conversation-id="currentConversationId"
  :report-text="reportContent?.text || ''"
  :html-charts="reportContent?.html_charts || ''"
  @dialog-response="handleDialogResponse"
  @panel-toggle="handleDialogPanelToggle"
  @history-cleared="handleDialogHistoryCleared"
  @exit-edit="handleExitEdit"
  ref="dialogPanelRef"
/>
```

#### DialogPanel.vue
```typescript
// 选中文字引用功能
const setSelectedText = (text: string, context?: { 
  beforeContext: string
  afterContext: string
  fullText: string 
}) => {
  selectedTextRef.value = text
  selectedTextContext.value = context || null
}

// 发送消息时包含选中的文字
const sendMessage = async () => {
  const requestParams: any = {
    session_id: props.sessionId,
    message: userMessage,
    selected_text: quotedText,
    selected_text_context: quotedContext
  }
  
  await sendDialogMessageStream(requestParams, ...)
}
```

### 后端实现

#### operation.py
```python
class TextEditRequest(BaseModel):
    """文本编辑请求"""
    selectedText: str
    beforeContext: str
    afterContext: str
    instruction: str

@router.post("/ai/text-edit", response_model=SuccessResponse)
async def ai_text_edit(
    request: TextEditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI文本编辑：根据用户指令修改选中的文本"""
    # 构建prompt
    prompt = f"""你是一个文本编辑助手...
    上文：{request.beforeContext}
    【需要修改的文本】：{request.selectedText}
    下文：{request.afterContext}
    用户指令：{request.instruction}
    """
    
    # 调用AI服务
    bailian_service = BailianService()
    response = await bailian_service._call_dashscope_api(prompt)
    new_text = bailian_service._extract_text_from_response(response)
    
    return SuccessResponse(data={"newText": new_text})
```

## 使用流程

### 用户操作流程
```
1. 用户选中报告中的文字
   ↓
2. 左侧AI对话面板显示"已选中文字"
   ↓
3. 用户点击快捷指令或输入自定义指令
   ↓
4. 点击"发送"按钮
   ↓
5. AI处理并返回修改后的文字
   ↓
6. 报告自动更新
```

### 数据流
```
前端选中文字
   ↓
DialogPanel.setSelectedText()
   ↓
用户输入指令
   ↓
sendDialogMessageStream()
   ↓
后端 /api/v1/dialog/send-stream
   ↓
AI服务处理
   ↓
返回修改后的文字
   ↓
前端更新报告内容
```

## 文件清单

### 前端文件
- `frontend/src/views/Operation/DataAnalysis.vue` - 主页面
- `frontend/src/views/Operation/components/DialogPanel.vue` - AI对话面板
- `frontend/src/components/TextEditToolbar.vue` - 独立工具栏（未使用）
- `frontend/src/components/ChartQuickEditPanel.vue` - 图表编辑面板（未集成）
- `frontend/src/api/textEdit.ts` - 文本编辑API
- `frontend/src/api/dialog.ts` - 对话API

### 后端文件
- `backend/app/api/v1/operation.py` - 运营数据分析API（包含text-edit端点）
- `backend/app/api/v1/dialog.py` - 对话API
- `backend/app/services/bailian_service.py` - AI服务
- `backend/app/services/bailian_dialog_service_stream.py` - 流式对话服务

### 文档文件
- `docs/AI文本编辑功能-使用指南.md` - 用户使用指南
- `docs/AI编辑功能-集成说明.md` - 本文档
- `docs/AI文本选中修改功能设计文档.md` - 原始设计文档
- `docs/AI对话功能设计文档.md` - 对话功能设计文档

## 配置说明

### 环境变量
```bash
# 阿里百炼API配置
DASHSCOPE_API_KEY=your_api_key
DASHSCOPE_MODEL=qwen-plus
```

### 依赖项
- 前端：Vue 3, Element Plus, Axios
- 后端：FastAPI, SQLAlchemy, httpx

## 测试说明

### 功能测试
1. 启动前后端服务
2. 登录系统
3. 生成一份报告
4. 选中报告中的文字
5. 查看左侧AI对话面板是否显示"已选中文字"
6. 点击快捷指令或输入自定义指令
7. 点击发送
8. 等待AI处理
9. 查看报告是否更新

### API测试
```bash
# 测试text-edit端点
curl -X POST http://localhost:8000/api/v1/operation/ai/text-edit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "selectedText": "VIP用户的rmb_ltv比较高",
    "beforeContext": "...",
    "afterContext": "...",
    "instruction": "润色这段话"
  }'
```

## 已知问题

### 1. 文本替换位置
- **问题**：AI返回的文字需要准确替换到原位置
- **状态**：通过对话API实现，由后端处理替换逻辑
- **解决方案**：使用`action_type: 'modify_text'`标识文本修改操作

### 2. 上下文提取
- **问题**：需要提取选中文字的上下文
- **状态**：已在DialogPanel中实现
- **实现**：提取前后各500字符作为上下文

## 后续计划

### 短期（本周）
- [ ] 完善文本替换逻辑
- [ ] 优化AI Prompt
- [ ] 添加错误处理
- [ ] 用户测试反馈

### 中期（下周）
- [ ] 集成图表AI编辑功能
- [ ] 添加修改历史记录
- [ ] 实现撤销功能
- [ ] 性能优化

### 长期（下月）
- [ ] 批量修改功能
- [ ] 自定义快捷指令
- [ ] 修改模板库
- [ ] 协作编辑

## 参考文档

- [AI文本编辑功能-使用指南](./AI文本编辑功能-使用指南.md)
- [AI对话功能设计文档](./AI对话功能设计文档.md)
- [AI文本选中修改功能设计文档](./AI文本选中修改功能设计文档.md)

---

**文档版本：** 1.0  
**创建时间：** 2024-12-26  
**最后更新：** 2024-12-26  
**维护者：** 开发团队
