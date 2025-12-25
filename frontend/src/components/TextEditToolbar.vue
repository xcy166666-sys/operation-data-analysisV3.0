<template>
  <teleport to="body">
    <div
      v-if="visible"
      ref="menuRef"
      class="text-edit-toolbar"
      :style="menuStyle"
      @click.stop
    >
      <div class="toolbar-content">
        <el-input
          v-model="instruction"
          placeholder="输入修改指令，如：润色这段话"
          size="small"
          class="instruction-input"
          @keyup.enter="handleSubmit"
          :disabled="loading"
        />
        <el-button
          type="primary"
          size="small"
          :loading="loading"
          @click="handleSubmit"
          :disabled="!instruction.trim()"
        >
          {{ loading ? '处理中...' : '提交' }}
        </el-button>
        <el-button
          size="small"
          @click="closeMenu"
          :disabled="loading"
        >
          取消
        </el-button>
      </div>
      
      <!-- 快捷指令按钮 -->
      <div class="quick-actions" v-if="!loading">
        <el-button
          size="small"
          text
          @click="setInstruction('润色这段话')"
        >
          润色
        </el-button>
        <el-button
          size="small"
          text
          @click="setInstruction('简化表达')"
        >
          简化
        </el-button>
        <el-button
          size="small"
          text
          @click="setInstruction('扩写这段内容')"
        >
          扩写
        </el-button>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { sendTextEditRequest } from '@/api/textEdit'

// Props
const props = defineProps({
  targetElement: {
    type: [String, HTMLElement],
    default: 'body'
  }
})

// 状态
const visible = ref(false)
const position = ref({ top: 0, left: 0 })
const instruction = ref('')
const loading = ref(false)
const context = ref(null)
const menuRef = ref(null)
const currentSelection = ref(null)

// 计算菜单样式
const menuStyle = computed(() => ({
  top: `${position.value.top}px`,
  left: `${position.value.left}px`
}))

// 获取目标元素
function getTargetElement() {
  if (typeof props.targetElement === 'string') {
    return document.querySelector(props.targetElement)
  }
  return props.targetElement
}

// 监听文本选择
function handleTextSelection(e) {
  // 延迟执行，确保选择完成
  setTimeout(() => {
    const selection = window.getSelection()
    const selectedText = selection.toString().trim()
    
    // 如果没有选中文本，隐藏菜单
    if (!selectedText) {
      visible.value = false
      return
    }
    
    // 检查选中的文本是否在目标元素内
    const targetEl = getTargetElement()
    if (targetEl && !targetEl.contains(selection.anchorNode)) {
      visible.value = false
      return
    }
    
    // 保存当前选区
    currentSelection.value = {
      selection: selection,
      range: selection.getRangeAt(0).cloneRange()
    }
    
    // 获取选区位置
    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    
    // 计算菜单位置（显示在选区上方）
    const menuHeight = 120 // 预估菜单高度
    const menuWidth = 400 // 预估菜单宽度
    
    let top = rect.top + window.scrollY - menuHeight - 10
    let left = rect.left + window.scrollX
    
    // 如果上方空间不足，显示在下方
    if (rect.top < menuHeight + 20) {
      top = rect.bottom + window.scrollY + 10
    }
    
    // 确保不超出右边界
    if (left + menuWidth > window.innerWidth) {
      left = window.innerWidth - menuWidth - 20
    }
    
    // 确保不超出左边界
    if (left < 10) {
      left = 10
    }
    
    position.value = { top, left }
    
    // 提取上下文
    context.value = extractContext(selectedText, targetEl)
    
    // 显示菜单
    visible.value = true
    
    // 聚焦输入框
    nextTick(() => {
      const input = menuRef.value?.querySelector('input')
      input?.focus()
    })
  }, 10)
}

// 提取上下文
function extractContext(selectedText, targetEl) {
  try {
    // 获取完整文本
    const fullText = targetEl ? targetEl.innerText : document.body.innerText
    
    // 找到选中文本的位置
    const startIndex = fullText.indexOf(selectedText)
    
    if (startIndex === -1) {
      console.warn('[TextEditToolbar] 无法在完整文本中找到选中文本')
      return {
        selectedText,
        beforeContext: '',
        afterContext: '',
        startIndex: 0,
        endIndex: selectedText.length
      }
    }
    
    const endIndex = startIndex + selectedText.length
    
    // 提取前后各500字符的上下文
    const CONTEXT_LENGTH = 500
    const beforeStart = Math.max(0, startIndex - CONTEXT_LENGTH)
    const afterEnd = Math.min(fullText.length, endIndex + CONTEXT_LENGTH)
    
    const beforeContext = fullText.substring(beforeStart, startIndex)
    const afterContext = fullText.substring(endIndex, afterEnd)
    
    console.log('[TextEditToolbar] 上下文提取成功', {
      selectedLength: selectedText.length,
      beforeLength: beforeContext.length,
      afterLength: afterContext.length,
      totalLength: selectedText.length + beforeContext.length + afterContext.length
    })
    
    return {
      selectedText,
      beforeContext,
      afterContext,
      startIndex,
      endIndex,
      fullText
    }
  } catch (error) {
    console.error('[TextEditToolbar] 提取上下文失败:', error)
    return {
      selectedText,
      beforeContext: '',
      afterContext: '',
      startIndex: 0,
      endIndex: selectedText.length
    }
  }
}

// 设置快捷指令
function setInstruction(text) {
  instruction.value = text
}

// 提交处理
async function handleSubmit() {
  if (!instruction.value.trim()) {
    ElMessage.warning('请输入修改指令')
    return
  }
  
  if (!context.value) {
    ElMessage.error('上下文信息丢失，请重新选择文本')
    return
  }
  
  loading.value = true
  
  try {
    console.log('[TextEditToolbar] 发送AI请求', {
      instruction: instruction.value,
      selectedText: context.value.selectedText.substring(0, 50) + '...',
      contextLength: context.value.beforeContext.length + context.value.afterContext.length
    })
    
    // 调用后端API
    const response = await sendTextEditRequest({
      selectedText: context.value.selectedText,
      beforeContext: context.value.beforeContext,
      afterContext: context.value.afterContext,
      instruction: instruction.value
    })
    
    if (response.success && response.newText) {
      console.log('[TextEditToolbar] AI返回成功', {
        originalLength: context.value.selectedText.length,
        newLength: response.newText.length
      })
      
      // 替换文本
      replaceText(response.newText)
      
      ElMessage.success('文本修改成功')
      
      // 关闭菜单
      closeMenu()
    } else {
      throw new Error(response.error || '修改失败')
    }
  } catch (error) {
    console.error('[TextEditToolbar] 提交失败:', error)
    ElMessage.error(error.message || '修改失败，请重试')
  } finally {
    loading.value = false
  }
}

// 替换文本
function replaceText(newText) {
  try {
    if (!currentSelection.value) {
      throw new Error('选区信息丢失')
    }
    
    const { selection, range } = currentSelection.value
    
    // 恢复选区
    selection.removeAllRanges()
    selection.addRange(range)
    
    // 删除原内容
    range.deleteContents()
    
    // 插入新文本
    const textNode = document.createTextNode(newText)
    range.insertNode(textNode)
    
    // 清除选区
    selection.removeAllRanges()
    
    // 将光标移到新文本末尾
    const newRange = document.createRange()
    newRange.setStartAfter(textNode)
    newRange.collapse(true)
    selection.addRange(newRange)
    
    console.log('[TextEditToolbar] 文本替换成功')
  } catch (error) {
    console.error('[TextEditToolbar] 文本替换失败:', error)
    ElMessage.error('文本替换失败')
  }
}

// 关闭菜单
function closeMenu() {
  visible.value = false
  instruction.value = ''
  context.value = null
  currentSelection.value = null
}

// 点击外部关闭
function handleClickOutside(e) {
  if (visible.value && menuRef.value && !menuRef.value.contains(e.target)) {
    closeMenu()
  }
}

// ESC键关闭
function handleEscKey(e) {
  if (e.key === 'Escape' && visible.value) {
    closeMenu()
  }
}

// 生命周期
onMounted(() => {
  document.addEventListener('mouseup', handleTextSelection)
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleEscKey)
  console.log('[TextEditToolbar] 组件已挂载，开始监听文本选择')
})

onUnmounted(() => {
  document.removeEventListener('mouseup', handleTextSelection)
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleEscKey)
  console.log('[TextEditToolbar] 组件已卸载')
})
</script>

<style scoped>
.text-edit-toolbar {
  position: fixed;
  z-index: 9999;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 12px;
  min-width: 400px;
  max-width: 500px;
}

.toolbar-content {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.instruction-input {
  flex: 1;
}

.quick-actions {
  display: flex;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px solid #eee;
}

.quick-actions .el-button {
  font-size: 12px;
  padding: 4px 8px;
}
</style>
