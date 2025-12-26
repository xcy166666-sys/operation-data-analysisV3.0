# AI编辑功能 - 文本选择集成总结

## 功能概述

已成功在所有分析页面中集成"选中文字自动引用到AI对话输入框"的功能，用户选中报告中的文字后，会自动传递到AI对话面板，方便进行针对性的修改。

---

## 已集成的页面

### ✅ 1. 单文件分析页面
**文件：** `frontend/src/views/Operation/DataAnalysis.vue`

**实现状态：** 完整实现

**核心功能：**
- 监听用户在报告区域的文本选择
- 自动提取选中文字及上下文（前后各500字符）
- 传递给DialogPanel组件显示
- 添加高亮动画效果
- 支持快捷指令（润色、简化、扩写）

**关键代码：**
```typescript
// 文本选择监听
const handleTextSelection = () => {
  if (!showDialogPanel.value) return
  
  const selection = window.getSelection()
  const selectedText = selection?.toString().trim()
  
  if (!selectedText || selectedText.length < 2) return
  
  // 检查是否在报告区域内
  const reportArea = reportDisplayRef.value
  if (!reportArea || !selection?.anchorNode) return
  if (!reportArea.contains(selection.anchorNode)) return
  
  // 添加高亮动画
  addSelectionHighlight(selection)
  
  // 提取上下文
  const context = extractTextContext(selectedText, reportArea)
  
  // 传递给DialogPanel
  if (dialogPanelRef.value) {
    dialogPanelRef.value.setSelectedText(selectedText, context)
  }
}

// 生命周期
onMounted(() => {
  document.addEventListener('mouseup', handleTextSelection)
})

onBeforeUnmount(() => {
  document.removeEventListener('mouseup', handleTextSelection)
})
```

---

### ✅ 2. 批量分析页面
**文件：** `frontend/src/views/Operation/BatchAnalysis.vue`

**实现状态：** 完整实现

**核心功能：**
- 与单文件分析相同的文本选择监听
- 支持多个Sheet报告的文本选择
- 自动识别当前查看的报告
- 高亮动画和上下文提取

**关键代码：**
```typescript
// 文本选择监听
const handleTextSelection = () => {
  if (!showDialogPanel.value) return
  
  const selection = window.getSelection()
  const selectedText = selection?.toString().trim()
  
  if (!selectedText || selectedText.length < 2) return
  
  // 检查是否在报告区域内
  const reportArea = document.querySelector('.dialog-right-panel')
  if (!reportArea || !selection?.anchorNode) return
  if (!reportArea.contains(selection.anchorNode)) return
  
  // 添加高亮动画
  addSelectionHighlight(selection)
  
  // 提取上下文
  const context = extractTextContext(selectedText, reportArea as HTMLElement)
  
  // 传递给DialogPanel
  if (dialogPanelRef.value) {
    dialogPanelRef.value.setSelectedText(selectedText, context)
  }
}

// 生命周期
onMounted(async () => {
  // ... 其他初始化代码
  
  // 添加文本选择监听
  document.addEventListener('mouseup', handleTextSelection)
})

onBeforeUnmount(() => {
  stopStatusPolling()
  // 移除文本选择监听
  document.removeEventListener('mouseup', handleTextSelection)
})
```

---

### ✅ 3. 定制化批量分析页面
**文件：** `frontend/src/views/Operation/CustomBatchAnalysis.vue`

**实现状态：** 完整实现

**核心功能：**
- 与批量分析页面相同的实现
- 支持自定义Prompt的报告文本选择
- 完整的上下文提取和传递

**关键代码：**
```typescript
// 与批量分析页面相同的实现
const handleTextSelection = () => {
  if (!showDialogPanel.value) return
  // ... 相同的逻辑
}

onMounted(async () => {
  // ... 其他初始化代码
  
  // 添加文本选择监听
  document.addEventListener('mouseup', handleTextSelection)
})

onBeforeUnmount(() => {
  stopStatusPolling()
  // 移除文本选择监听
  document.removeEventListener('mouseup', handleTextSelection)
})
```

---

## 核心组件

### DialogPanel 组件
**文件：** `frontend/src/views/Operation/components/DialogPanel.vue`

**核心方法：**

#### 1. setSelectedText
```typescript
const setSelectedText = (text: string, context?: { 
  beforeContext: string
  afterContext: string
  fullText: string 
}) => {
  selectedTextRef.value = text
  selectedTextContext.value = context || null
  console.log('[DialogPanel] 收到选中文字:', text.substring(0, 50) + '...')
}
```

#### 2. clearSelectedText
```typescript
const clearSelectedText = () => {
  selectedTextRef.value = ''
  selectedTextContext.value = null
}
```

**UI显示：**
```vue
<!-- 选中文字引用区 -->
<div v-if="selectedTextRef" class="selected-text-quote">
  <div class="quote-header">
    <span class="quote-icon">📝</span>
    <span class="quote-title">已选中文字</span>
    <el-button size="small" text @click="clearSelectedText">
      清除
    </el-button>
  </div>
  <div class="quote-text">{{ selectedTextRef }}</div>
</div>

<!-- 快捷指令（当有选中文字时显示） -->
<div v-if="selectedTextRef" class="quick-actions">
  <span class="quick-label">快捷指令：</span>
  <el-button size="small" text @click="setQuickInstruction('润色这段话')">润色</el-button>
  <el-button size="small" text @click="setQuickInstruction('简化表达')">简化</el-button>
  <el-button size="small" text @click="setQuickInstruction('扩写内容')">扩写</el-button>
</div>
```

---

## 辅助函数

### 1. addSelectionHighlight
**功能：** 为选中的文字添加高亮动画效果

```typescript
const addSelectionHighlight = (selection: Selection) => {
  try {
    const range = selection.getRangeAt(0)
    
    // 创建高亮元素
    const highlight = document.createElement('span')
    highlight.className = 'text-selection-highlight'
    highlight.style.cssText = `
      background: linear-gradient(120deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
      border-radius: 4px;
      padding: 2px 0;
      animation: highlightPulse 0.5s ease-out;
    `
    
    // 包裹选中的内容
    range.surroundContents(highlight)
    
    // 2秒后移除高亮效果
    setTimeout(() => {
      if (highlight.parentNode) {
        const parent = highlight.parentNode
        while (highlight.firstChild) {
          parent.insertBefore(highlight.firstChild, highlight)
        }
        parent.removeChild(highlight)
      }
    }, 2000)
  } catch (e) {
    // 如果无法包裹（跨元素选择），忽略错误
    console.log('无法添加高亮效果（可能是跨元素选择）')
  }
}
```

### 2. extractTextContext
**功能：** 提取选中文字的上下文

```typescript
const extractTextContext = (selectedText: string, container: HTMLElement) => {
  const fullText = container.innerText || ''
  const startIndex = fullText.indexOf(selectedText)
  
  if (startIndex === -1) {
    return {
      beforeContext: '',
      afterContext: '',
      fullText: fullText
    }
  }
  
  const endIndex = startIndex + selectedText.length
  const CONTEXT_LENGTH = 500
  
  return {
    beforeContext: fullText.substring(Math.max(0, startIndex - CONTEXT_LENGTH), startIndex),
    afterContext: fullText.substring(endIndex, Math.min(fullText.length, endIndex + CONTEXT_LENGTH)),
    fullText: fullText
  }
}
```

---

## 使用流程

### 用户操作流程

1. **打开AI对话面板**
   - 点击页面右上角的"AI对话"按钮
   - 页面切换为左右分栏布局

2. **选中文字**
   - 在右侧报告区域用鼠标选中想要修改的文字
   - 选中后会出现短暂的高亮动画效果

3. **查看引用**
   - 左侧对话面板会自动显示"已选中文字"区域
   - 显示选中的文字内容
   - 提供"清除"按钮可以取消选择

4. **使用快捷指令或自定义输入**
   - 点击快捷指令按钮（润色、简化、扩写）
   - 或在输入框中输入自定义修改指令
   - 按Enter发送

5. **AI处理**
   - AI会根据选中的文字和上下文进行理解
   - 生成修改建议或新的文字
   - 显示在对话历史中

### 技术流程

```
用户选中文字
    ↓
触发 mouseup 事件
    ↓
handleTextSelection 函数
    ↓
检查是否在报告区域内
    ↓
添加高亮动画 (addSelectionHighlight)
    ↓
提取上下文 (extractTextContext)
    ↓
调用 DialogPanel.setSelectedText()
    ↓
DialogPanel 显示选中文字
    ↓
用户输入指令并发送
    ↓
AI 处理并返回结果
```

---

## 技术特点

### 1. 智能上下文提取
- 自动提取选中文字前后各500字符
- 确保AI能够理解文字的语境
- 提高修改的准确性和连贯性

### 2. 视觉反馈
- 选中文字时显示渐变高亮动画
- 2秒后自动消失，不影响阅读
- 对话面板中清晰显示引用的文字

### 3. 用户体验优化
- 只在AI对话面板打开时监听
- 只响应报告区域内的文本选择
- 提供快捷指令，降低使用门槛
- 支持清除选择，灵活控制

### 4. 性能优化
- 使用事件委托，避免重复绑定
- 在组件卸载时清理监听器
- 高亮动画使用CSS，性能优秀

---

## 注意事项

### 1. 选择范围限制
- 只监听报告显示区域内的文本选择
- 不响应其他区域（如侧边栏、标题栏）的选择
- 最小选择长度为2个字符

### 2. 跨元素选择
- 如果选择跨越多个HTML元素，高亮动画可能无法显示
- 但文字仍会正常传递到对话面板
- 不影响核心功能使用

### 3. 上下文长度
- 固定提取前后各500字符
- 对于特别长的报告，可能无法获取完整上下文
- 但通常500字符足够AI理解语境

### 4. 浏览器兼容性
- 使用标准的 Selection API
- 支持所有现代浏览器
- IE浏览器可能不支持

---

## 后续优化建议

### 1. 可配置的上下文长度
```typescript
// 允许用户自定义上下文长度
const CONTEXT_LENGTH = ref(500) // 可以通过设置面板调整
```

### 2. 选择历史记录
```typescript
// 记录最近的几次选择
const selectionHistory = ref<Array<{
  text: string
  context: any
  timestamp: number
}>>([])
```

### 3. 多段选择支持
```typescript
// 支持选择多段文字进行批量修改
const multipleSelections = ref<string[]>([])
```

### 4. 智能建议
```typescript
// 根据选中的文字类型，自动推荐合适的修改指令
const suggestInstructions = (text: string) => {
  if (text.length > 200) return ['简化表达', '分段']
  if (text.length < 50) return ['扩写内容', '添加细节']
  return ['润色这段话', '改写']
}
```

---

## 测试清单

### 功能测试
- [x] 单文件分析页面 - 文本选择
- [x] 批量分析页面 - 文本选择
- [x] 定制化批量分析页面 - 文本选择
- [x] 高亮动画显示
- [x] 上下文提取
- [x] DialogPanel显示选中文字
- [x] 快捷指令按钮
- [x] 清除选择功能
- [x] 发送后自动清除

### 边界测试
- [x] 选择长度小于2字符 - 不响应
- [x] 选择非报告区域文字 - 不响应
- [x] AI对话面板关闭时选择 - 不响应
- [x] 跨元素选择 - 正常传递，高亮可能失败
- [x] 组件卸载时清理监听器

### 性能测试
- [x] 大量文本选择 - 响应流畅
- [x] 频繁选择切换 - 无内存泄漏
- [x] 高亮动画性能 - 流畅无卡顿

---

## 总结

✅ **已完成：**
- 三个分析页面全部集成文本选择功能
- DialogPanel组件完整支持
- 高亮动画和上下文提取
- 快捷指令和清除功能
- 完整的生命周期管理

🎯 **效果：**
- 用户体验大幅提升
- AI修改更加精准
- 操作流程更加流畅
- 降低使用门槛

📝 **文档：**
- 使用指南：`docs/AI编辑功能-使用指南.md`
- 集成总结：本文档

---

**创建时间：** 2024-12-26  
**最后更新：** 2024-12-26  
**维护者：** 开发团队
