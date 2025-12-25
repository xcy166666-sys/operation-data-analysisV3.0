# AI对话功能 - 报告重新生成方案

## 方案说明

用户提出的新需求：**当用户提出修改要求时，AI应该重新生成整个报告（包括文字和图表），而不是只修改图表配置。**

这是一个更符合实际使用场景的方案！

## 实现原理

### 数据流程

```
1. 用户查看报告
   ↓
2. 点击"AI对话"按钮
   ↓
3. 前端传递完整报告内容：
   - current_report_text: 报告文字
   - current_html_charts: HTML图表
   - current_charts: 图表配置（如果有）
   ↓
4. 用户发送修改需求："把图表改成红色"
   ↓
5. 后端将报告内容 + 用户需求发给AI
   ↓
6. AI理解需求，重新生成报告：
   - new_report_text: 改进后的文字
   - new_html_charts: 改进后的HTML图表
   ↓
7. 前端接收新报告，更新右侧显示
   ↓
8. 用户看到更新后的报告
```

## 代码修改

### 1. 前端 API 接口

**文件**：`frontend/src/api/dialog.ts`

**修改**：添加报告内容参数

```typescript
export interface DialogRequest {
  session_id: number
  message: string
  conversation_id?: string
  current_charts?: any[]
  current_report_text?: string  // 新增
  current_html_charts?: string  // 新增
}

export function sendDialogMessage(data: DialogRequest) {
  const formData = new FormData()
  formData.append('session_id', data.session_id.toString())
  formData.append('user_message', data.message)
  formData.append('current_charts', JSON.stringify(data.current_charts || []))
  formData.append('current_report_text', data.current_report_text || '')  // 新增
  formData.append('current_html_charts', data.current_html_charts || '')  // 新增
  // ...
}
```

### 2. 对话面板组件

**文件**：`frontend/src/views/Operation/components/DialogPanel.vue`

**修改**：接收并传递报告内容

```typescript
interface Props {
  sessionId: number
  charts: any[]
  conversationId?: string
  reportText?: string  // 新增
  htmlCharts?: string  // 新增
}

// 发送消息时传递完整报告
const res: any = await sendDialogMessage({
  session_id: props.sessionId,
  message: userMessage,
  conversation_id: currentConversationId.value || undefined,
  current_charts: props.charts,
  current_report_text: props.reportText,  // 新增
  current_html_charts: props.htmlCharts  // 新增
})

// 处理AI返回的新报告
if (res.data.action_type === 'regenerate_report') {
  emit('dialog-response', {
    action_type: 'regenerate_report',
    new_report_text: res.data.new_report_text,
    new_html_charts: res.data.new_html_charts
  })
}
```

### 3. 数据分析页面

**文件**：`frontend/src/views/Operation/DataAnalysis.vue`

**修改**：传递报告内容给对话面板

```vue
<DialogPanel
  v-if="currentSessionId"
  :session-id="currentSessionId"
  :charts="currentCharts"
  :conversation-id="conversationId"
  :report-text="reportContent?.text || ''"  <!-- 新增 -->
  :html-charts="reportContent?.html_charts || ''"  <!-- 新增 -->
  @dialog-response="handleDialogResponse"
/>
```

**处理AI响应**：

```typescript
const handleDialogResponse = (response: any) => {
  if (response.action_type === 'regenerate_report') {
    // AI重新生成了完整报告
    const newContent = {
      ...reportContent.value,
      text: response.new_report_text,
      html_charts: response.new_html_charts
    }
    operationStore.setReportContent(newContent)
    ElMessage.success('报告已更新')
  }
}
```

### 4. 后端 API

**文件**：`backend/app/api/v1/operation.py`

**修改**：接收报告内容参数

```python
@router.post("/dialog", response_model=SuccessResponse)
async def process_dialog_message(
    session_id: int = Form(...),
    user_message: str = Form(...),
    current_charts: str = Form(""),
    current_report_text: str = Form(""),  # 新增
    current_html_charts: str = Form(""),  # 新增
    conversation_id: Optional[str] = Form(None),
    # ...
):
    # 传递给对话服务
    result = await dialog_service.process_dialog_message(
        session_id=str(session_id),
        user_message=user_message,
        current_charts=charts_data,
        current_report_text=current_report_text,  # 新增
        current_html_charts=current_html_charts,  # 新增
        conversation_id=conversation_id,
        file_path=str(file_path) if file_path else None
    )
```

### 5. 对话服务

**文件**：`backend/app/services/bailian_dialog_service.py`

**修改**：重新生成报告模式

**系统提示词**：

```python
system_prompt = """你是一个专业的数据分析师助手，可以帮助用户优化和调整数据分析报告。

你的任务：
1. 理解用户的修改需求
2. 基于当前报告内容，生成改进后的新版本报告
3. 保持报告的专业性和完整性
4. 根据需求调整图表样式、颜色、类型等

回复格式：
```json
{
  "action_type": "regenerate_report",
  "new_report_text": "改进后的报告文字内容...",
  "new_html_charts": "<div>改进后的HTML图表代码...</div>",
  "response": "已根据您的要求重新生成报告"
}
```
"""
```

**上下文构建**：

```python
context_message = f"""
当前报告内容：
---
文字部分（前500字）：
{current_report_text[:500]}
...

HTML图表（长度：{len(current_html_charts)} 字符）：
{current_html_charts[:200]}
...
---

用户修改需求：{user_message}

请根据用户需求，重新生成改进后的报告。
"""
```

**响应处理**：

```python
if parsed_response.get("action_type") == "regenerate_report":
    result = {
        "response": parsed_response.get("response"),
        "new_report_text": parsed_response.get("new_report_text"),
        "new_html_charts": parsed_response.get("new_html_charts"),
        "conversation_id": api_response.get("conversation_id"),
        "action_type": "regenerate_report"
    }
```

## 使用示例

### 示例1：修改图表颜色

**用户**：把第一个图表改成红色

**AI处理**：
1. 接收当前报告内容
2. 理解用户需求：修改第一个图表颜色为红色
3. 重新生成HTML图表代码（红色主题）
4. 保持报告文字不变
5. 返回新报告

**前端显示**：
- 右侧报告自动更新
- 图表变为红色
- 文字内容保持不变

### 示例2：调整图表类型

**用户**：把柱状图改成折线图

**AI处理**：
1. 识别当前的柱状图
2. 生成折线图的HTML代码
3. 调整相关的文字描述
4. 返回新报告

**前端显示**：
- 图表从柱状图变为折线图
- 相关描述文字也更新

### 示例3：优化报告内容

**用户**：让报告更专业一些

**AI处理**：
1. 分析当前报告内容
2. 优化文字表达
3. 调整图表样式
4. 返回改进后的完整报告

**前端显示**：
- 文字和图表都更新
- 整体更专业

## 优势

### 1. 用户体验好

- ✅ 用户只需提出需求，无需关心技术细节
- ✅ 所见即所得，实时看到效果
- ✅ 支持自然语言交互

### 2. 功能强大

- ✅ 可以修改图表样式、颜色、类型
- ✅ 可以优化报告文字
- ✅ 可以调整整体布局
- ✅ 支持复杂的修改需求

### 3. 技术实现简单

- ✅ 不需要复杂的图表配置解析
- ✅ 不需要维护图表状态
- ✅ AI直接生成HTML，前端直接显示
- ✅ 兼容HTML模式和JSON模式

### 4. 扩展性强

- ✅ 可以添加更多修改类型
- ✅ 可以支持批量修改
- ✅ 可以保存修改历史
- ✅ 可以导出修改后的报告

## 测试步骤

### 1. 准备测试环境

```bash
# 重启后端
docker restart operation-analysis-v2-backend

# 等待5秒
Start-Sleep -Seconds 5

# 刷新前端页面
```

### 2. 生成初始报告

1. 上传Excel文件
2. 输入分析需求
3. 生成报告
4. 等待报告完成

### 3. 测试对话功能

**测试1：修改图表颜色**

```
用户：把图表改成蓝色主题
预期：AI重新生成蓝色主题的图表
```

**测试2：修改图表类型**

```
用户：把折线图改成柱状图
预期：AI重新生成柱状图
```

**测试3：优化报告**

```
用户：让报告更简洁一些
预期：AI优化报告文字和图表
```

**测试4：添加内容**

```
用户：在报告中添加趋势分析
预期：AI在报告中添加趋势分析部分
```

### 4. 验证结果

- [ ] 右侧报告自动更新
- [ ] 图表样式正确
- [ ] 文字内容正确
- [ ] 对话历史保存
- [ ] 可以继续对话

## 调试方法

### 前端调试

**查看传递的数据**：

```javascript
// 在 DialogPanel.vue 的 sendMessage 函数中
console.log('[DialogPanel] 发送数据:', {
  reportText: props.reportText?.length,
  htmlCharts: props.htmlCharts?.length
})
```

**查看AI响应**：

```javascript
// 在 handleDialogResponse 函数中
console.log('[DataAnalysis] AI响应:', response)
```

### 后端调试

**查看接收的数据**：

```python
logger.info(f"[对话API] 接收数据 - 文字: {len(current_report_text)}, HTML: {len(current_html_charts)}")
```

**查看AI返回**：

```python
logger.info(f"[BailianDialogService] AI返回 - action_type: {parsed_response.get('action_type')}")
```

## 注意事项

### 1. AI生成质量

- AI可能无法完美理解所有需求
- 需要清晰的用户指令
- 复杂修改可能需要多轮对话

### 2. 性能考虑

- 重新生成报告需要时间（5-10秒）
- 需要显示加载状态
- 可以添加进度提示

### 3. 错误处理

- AI生成失败时的降级方案
- 网络错误的重试机制
- 用户友好的错误提示

### 4. 数据保存

- 修改后的报告需要保存到数据库
- 对话历史需要记录
- 支持撤销功能（可选）

## 后续优化

### 1. 添加预览功能

在应用修改前，先预览效果

### 2. 支持批量修改

一次修改多个图表

### 3. 修改历史

查看和恢复历史版本

### 4. 导出功能

导出修改后的报告

### 5. 模板功能

保存常用的修改模板

## 总结

这个方案将AI对话功能从"图表修改"升级为"报告重新生成"，更符合实际使用场景，用户体验更好，技术实现也更简单。

**核心优势**：
- ✅ 用户只需提出需求
- ✅ AI重新生成完整报告
- ✅ 前端实时显示更新
- ✅ 支持复杂的修改需求

现在可以测试了！刷新页面，打开对话面板，试试看效果如何。
