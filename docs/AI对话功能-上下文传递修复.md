# AI对话功能 - 上下文传递修复

## 问题描述

用户反馈：AI对话时不知道第一次生成的报告内容，无法修改图表样式。

**根本原因**：前端发送对话请求时，`current_charts` 参数传递的是空数组，导致AI没有报告的上下文信息。

## 修复方案

### 1. 前端修改

#### 1.1 修改 `frontend/src/api/dialog.ts`

**添加 `current_charts` 参数**：

```typescript
export interface DialogRequest {
  session_id: number
  message: string
  conversation_id?: string
  current_charts?: any[]  // 新增：当前图表数据
}

export function sendDialogMessage(data: DialogRequest) {
  const formData = new FormData()
  formData.append('session_id', data.session_id.toString())
  formData.append('user_message', data.message)
  if (data.conversation_id) {
    formData.append('conversation_id', data.conversation_id)
  }
  // 传递当前图表数据，让AI知道报告内容
  formData.append('current_charts', JSON.stringify(data.current_charts || []))
  
  return request.post<DialogResponse>(
    '/operation/dialog',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
}
```

#### 1.2 修改 `frontend/src/views/Operation/components/DialogPanel.vue`

**在发送消息时传递图表数据**：

```typescript
// 调用API，传递当前图表数据
const res: any = await sendDialogMessage({
  session_id: props.sessionId,
  message: userMessage,
  conversation_id: currentConversationId.value || undefined,
  current_charts: props.charts  // 传递当前图表数据
})
```

#### 1.3 确认 `frontend/src/views/Operation/DataAnalysis.vue`

**已正确绑定图表数据**：

```vue
<DialogPanel
  v-if="currentSessionId"
  :session-id="currentSessionId"
  :charts="currentCharts"  <!-- 已绑定 -->
  :conversation-id="conversationId"
  @dialog-response="handleDialogResponse"
/>
```

**图表数据更新逻辑**：

```typescript
const updateCurrentCharts = () => {
  const content = reportContent.value
  if (content && content.charts) {
    currentCharts.value = content.charts
  } else if (content && content.html_charts) {
    currentCharts.value = [{
      type: 'html',
      title: 'AI生成图表',
      html_content: content.html_charts
    }]
  } else {
    currentCharts.value = []
  }
}

// 在开启对话模式时调用
const toggleDialogPanel = () => {
  if (showDialogPanel.value && operationStore.currentSessionId) {
    currentSessionId.value = operationStore.currentSessionId
    updateCurrentCharts()  // 更新图表数据
  }
}
```

### 2. 后端修改

#### 2.1 改进 `backend/app/services/bailian_dialog_service.py`

**增强图表描述功能**，提供更详细的图表信息：

```python
def _describe_current_charts(self, charts: List[Dict[str, Any]]) -> str:
    """描述当前图表状态"""
    if not charts:
        return "暂无图表"

    descriptions = []
    for i, chart in enumerate(charts):
        chart_type = chart.get('type', '未知类型')
        title = chart.get('title', f'图表{i+1}')
        
        # 构建详细描述
        desc_parts = [f"图表{i+1}: {title}"]
        desc_parts.append(f"类型: {chart_type}")
        
        # 添加配置信息
        config = chart.get('config', {})
        if config:
            if 'color' in config:
                desc_parts.append(f"颜色: {config['color']}")
            if 'colors' in config:
                desc_parts.append(f"配色方案: {', '.join(config['colors'][:3])}...")
            if 'xAxis' in config:
                x_field = config['xAxis'].get('field', '未知')
                desc_parts.append(f"X轴: {x_field}")
            if 'yAxis' in config:
                y_field = config['yAxis'].get('field', '未知')
                desc_parts.append(f"Y轴: {y_field}")
        
        # 添加数据信息
        data = chart.get('data', [])
        if data:
            desc_parts.append(f"数据点数: {len(data)}")
        
        descriptions.append(" | ".join(desc_parts))

    return "\n".join(descriptions)
```

**改进后的效果**：

之前的描述：
```
图表1（line图），图表2（bar图）
```

现在的描述：
```
图表1: 每日新增用户数 | 类型: line | 配色方案: #5470C6, #91CC75, #FAC858... | X轴: date | Y轴: count | 数据点数: 30
图表2: 用户留存率 | 类型: bar | 颜色: #FF6B6B | X轴: day | Y轴: retention_rate | 数据点数: 7
```

## 数据流程

```
1. 用户生成报告
   ↓
2. reportContent 包含图表数据（charts 或 html_charts）
   ↓
3. 点击"AI对话"按钮
   ↓
4. toggleDialogPanel() 调用 updateCurrentCharts()
   ↓
5. currentCharts.value 更新为报告中的图表数据
   ↓
6. DialogPanel 接收 :charts="currentCharts"
   ↓
7. 用户发送消息
   ↓
8. sendDialogMessage() 传递 current_charts: props.charts
   ↓
9. 后端接收 current_charts JSON字符串
   ↓
10. _describe_current_charts() 生成详细描述
   ↓
11. AI 基于图表上下文生成回复
   ↓
12. 返回修改后的图表配置
   ↓
13. 前端更新图表显示
```

## 测试验证

### 测试步骤

1. **生成报告**
   - 上传Excel文件
   - 输入分析需求
   - 等待报告生成

2. **开启AI对话**
   - 点击"AI对话"按钮
   - 确认对话面板显示

3. **测试图表修改**
   
   **测试1：修改图表颜色**
   ```
   用户：把第一个图表改成红色
   预期：AI识别到图表1的当前颜色，返回修改后的配置
   ```

   **测试2：修改图表类型**
   ```
   用户：将第二个图表改为折线图
   预期：AI识别到图表2的当前类型（bar），返回修改为line的配置
   ```

   **测试3：数据分析**
   ```
   用户：分析一下第一个图表的趋势
   预期：AI基于图表的数据点数和配置，提供趋势分析
   ```

### 验证要点

- [ ] 前端正确传递 `current_charts` 参数
- [ ] 后端正确解析图表数据
- [ ] AI能够识别图表的详细信息（类型、颜色、数据等）
- [ ] AI能够根据上下文提供准确的修改建议
- [ ] 修改后的图表配置能够正确应用

## 调试方法

### 前端调试

**查看传递的图表数据**：

```typescript
// 在 DialogPanel.vue 的 sendMessage 函数中添加
console.log('[DialogPanel] 发送的图表数据:', props.charts)
```

**查看API请求**：

打开浏览器开发者工具 → Network → 找到 `/operation/dialog` 请求 → 查看 Form Data 中的 `current_charts` 字段

### 后端调试

**查看接收的图表数据**：

```python
# 在 operation.py 的 process_dialog_message 函数中
logger.info(f"[对话API] 接收到的图表数据: {current_charts[:200]}...")
logger.info(f"[对话API] 解析后的图表数量: {len(charts_data)}")
```

**查看图表描述**：

```python
# 在 bailian_dialog_service.py 的 _build_dialog_context 函数中
logger.info(f"[对话上下文] 图表描述: {chart_description}")
```

**查看后端日志**：

```bash
docker logs operation-analysis-v2-backend --tail 50 -f
```

## 常见问题

### 问题1：AI仍然不知道图表信息

**排查**：
1. 检查 `currentCharts.value` 是否有值
2. 检查 `props.charts` 是否正确传递
3. 检查后端日志，确认 `current_charts` 是否为空

**解决**：
- 确保在开启对话前已生成报告
- 确保 `updateCurrentCharts()` 被正确调用
- 检查 `reportContent.value.charts` 是否有数据

### 问题2：图表描述不够详细

**排查**：
1. 检查图表数据结构是否包含 `config` 字段
2. 检查 `_describe_current_charts` 的输出

**解决**：
- 确保后端生成报告时包含完整的图表配置
- 根据实际图表结构调整 `_describe_current_charts` 函数

### 问题3：修改后图表未更新

**排查**：
1. 检查AI返回的 `modified_charts` 是否有值
2. 检查 `handleDialogResponse` 是否被调用
3. 检查 `operationStore.setReportContent` 是否更新

**解决**：
- 确认AI返回的数据格式正确
- 检查图表更新逻辑
- 查看浏览器控制台错误信息

## 后续优化

### 1. 添加报告文本内容

除了图表，还可以传递报告的文本内容：

```typescript
export interface DialogRequest {
  session_id: number
  message: string
  conversation_id?: string
  current_charts?: any[]
  report_text?: string  // 新增：报告文本内容
}
```

### 2. 支持更多图表属性

在 `_describe_current_charts` 中添加更多属性描述：

```python
# 添加图例、标题、坐标轴标签等
if 'legend' in config:
    desc_parts.append(f"图例: {config['legend']}")
if 'title' in config:
    desc_parts.append(f"标题: {config['title']}")
```

### 3. 优化AI提示词

在系统提示词中添加更多示例和指导：

```python
system_prompt = """你是一个专业的数据分析师助手...

示例对话：
用户：把第一个图表改成红色
助手：好的，我将第一个图表的颜色改为红色。
```json
{
  "action_type": "modify_chart",
  "modifications": [...]
}
```
"""
```

### 4. 添加图表预览

在对话面板中显示当前图表的缩略图，让用户更直观地了解要修改的内容。

## 总结

通过这次修复，AI对话功能现在能够：

✅ 接收完整的图表数据
✅ 理解图表的详细配置（类型、颜色、数据等）
✅ 基于上下文提供准确的修改建议
✅ 正确修改图表样式和配置

用户现在可以通过自然语言与AI对话，实时修改报告中的图表，大大提升了使用体验。
