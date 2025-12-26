<template>
  <div class="dialog-panel">
    <div class="dialog-header">
      <div class="header-left">
        <h4>💬 AI 对话助手</h4>
        <span class="status-badge" :class="{ online: isOnline }">
          {{ isOnline ? '在线' : '离线' }}
        </span>
      </div>
      <div class="header-actions">
        <el-button 
          size="small" 
          text 
          @click="handleExitEdit"
          title="退出编辑"
          class="exit-btn"
        >
          <el-icon><Close /></el-icon>
          <span>退出编辑</span>
        </el-button>
        <el-button 
          size="small" 
          text 
          @click="loadHistory"
          :loading="isLoadingHistory"
          title="刷新历史"
        >
          <el-icon><Refresh /></el-icon>
        </el-button>
        <el-button 
          size="small" 
          text 
          @click="handleClearHistory"
          title="清除历史"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <div class="dialog-content">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0 && !selectedTextRef" class="welcome-message">
        <div class="welcome-icon">💬</div>
        <p class="welcome-title">AI对话助手</p>
        <p class="welcome-desc">您可以通过对话来调整图表样式、修改数据范围等</p>
        <p class="welcome-desc" style="color: #667eea; font-weight: 500;">💡 提示：选中右侧报告中的文字，可以针对性地修改</p>
        <div class="welcome-examples">
          <p class="examples-title">试试这些：</p>
          <el-tag 
            v-for="example in examples" 
            :key="example"
            class="example-tag"
            @click="useExample(example)"
          >
            {{ example }}
          </el-tag>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-else class="message-list" ref="messageListRef">
        <div 
          v-for="message in messages" 
          :key="message.id" 
          class="message-item"
          :class="message.role"
        >
          <!-- 版本保存点标记 -->
          <div v-if="message.role === 'system' && message.extra_data?.type === 'version_marker'" class="version-marker">
            <div class="marker-line"></div>
            <div class="marker-badge">
              <el-icon><Flag /></el-icon>
              <span class="marker-text">{{ message.content }}</span>
            </div>
            <div class="marker-time">{{ formatTime(message.timestamp) }}</div>
          </div>
          
          <!-- 普通消息 -->
          <template v-else-if="message.role !== 'system'">
            <div class="message-avatar">
              <el-icon v-if="message.role === 'user'"><User /></el-icon>
              <el-icon v-else><ChatDotRound /></el-icon>
            </div>
            <div class="message-bubble">
              <!-- 显示引用的文字 -->
              <div v-if="message.quoted_text" class="message-quote">
                <div class="quote-label">📝 引用文字：</div>
                <div class="quote-content">{{ message.quoted_text }}</div>
              </div>
              <div class="message-content">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
              <!-- 显示修改的图表数量 -->
              <div v-if="message.modified_charts && message.modified_charts.length > 0" class="message-charts">
                <el-icon><PieChart /></el-icon>
                <span>已修改 {{ message.modified_charts.length }} 个图表</span>
              </div>
            </div>
          </template>
        </div>
        
        <!-- 思考过程显示 -->
        <div v-if="isSending && thinkingText" class="message-item assistant thinking">
          <div class="message-avatar">
            <el-icon class="thinking-icon"><Loading /></el-icon>
          </div>
          <div class="message-bubble thinking-bubble">
            <div class="thinking-header">
              <span class="thinking-label">🧠 AI 正在思考...</span>
              <el-button 
                size="small" 
                text 
                @click="toggleThinkingExpand"
                class="expand-btn"
              >
                {{ isThinkingExpanded ? '收起' : '展开' }}
              </el-button>
            </div>
            <div 
              class="thinking-content" 
              :class="{ expanded: isThinkingExpanded }"
            >
              {{ thinkingText }}
            </div>
          </div>
        </div>
        
        <!-- 加载中提示（无思考内容时显示） -->
        <div v-else-if="isSending" class="message-item assistant loading">
          <div class="message-avatar">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="message-bubble">
            <div class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 选中文字引用区 -->
      <div v-if="selectedTextRef" class="selected-text-quote">
        <div class="quote-header">
          <span class="quote-icon">📝</span>
          <span class="quote-title">已选中文字</span>
          <el-button 
            size="small" 
            text 
            @click="clearSelectedText"
            class="clear-quote-btn"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div class="quote-text">{{ selectedTextRef }}</div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          :placeholder="selectedTextRef ? '输入修改指令，如：润色这段话、简化表达、扩写内容...' : '输入消息，按 Enter 发送，Shift+Enter 换行...'"
          :maxlength="500"
          show-word-limit
          @keydown.enter="handleKeyDown"
          :disabled="isSending"
        />
        <el-button 
          type="primary" 
          :icon="Promotion"
          @click="sendMessage"
          :loading="isSending"
          :disabled="!inputMessage.trim()"
        >
          发送
        </el-button>
      </div>
      
      <!-- 快捷指令（当有选中文字时显示） -->
      <div v-if="selectedTextRef" class="quick-actions">
        <span class="quick-label">快捷指令：</span>
        <el-button size="small" text @click="setQuickInstruction('润色这段话')">润色</el-button>
        <el-button size="small" text @click="setQuickInstruction('简化表达')">简化</el-button>
        <el-button size="small" text @click="setQuickInstruction('扩写这段内容')">扩写</el-button>
        <el-button size="small" text @click="setQuickInstruction('改写这段话')">改写</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, 
  Delete, 
  User, 
  ChatDotRound, 
  PieChart,
  Promotion,
  Close,
  Loading,
  Flag,
  Edit
} from '@element-plus/icons-vue'
import { 
  sendDialogMessageStream,
  getDialogHistory, 
  clearDialogHistory,
  type DialogMessage 
} from '@/api/dialog'

// 扩展DialogMessage类型，添加quoted_text字段
interface ExtendedDialogMessage extends DialogMessage {
  quoted_text?: string
  extra_data?: {
    type?: string
    version_id?: number
    version_no?: number
    summary?: string
    [key: string]: any
  }
}

// 组件属性
interface Props {
  sessionId: number
  charts: any[]
  conversationId?: string
  reportText?: string  // 当前报告文字
}

const props = withDefaults(defineProps<Props>(), {
  conversationId: '',
  reportText: ''
})

const emit = defineEmits<{
  'dialog-response': [response: any]
  'panel-toggle': [collapsed: boolean]
  'history-cleared': []
  'exit-edit': []
}>()

// 响应式数据
const messages = ref<ExtendedDialogMessage[]>([])
const inputMessage = ref('')
const isSending = ref(false)
const isLoadingHistory = ref(false)
const isOnline = ref(true)
const messageListRef = ref<HTMLElement | null>(null)
const currentConversationId = ref(props.conversationId)

// 思考过程相关
const thinkingText = ref('')
const isThinkingExpanded = ref(false)

// 选中文字相关
const selectedTextRef = ref<string>('')
const selectedTextContext = ref<{
  beforeContext: string
  afterContext: string
  fullText: string
} | null>(null)

// 示例消息
const examples = [
  '将第一个图表改为柱状图',
  '修改图表颜色为蓝色',
  '分析数据趋势'
]

// 切换思考过程展开/收起
const toggleThinkingExpand = () => {
  isThinkingExpanded.value = !isThinkingExpanded.value
}

// 格式化时间
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

// 加载历史消息
const loadHistory = async () => {
  isLoadingHistory.value = true
  try {
    const res: any = await getDialogHistory(props.sessionId, 50)
    if (res.success && res.data) {
      messages.value = res.data.messages
      scrollToBottom()
    }
  } catch (error: any) {
    console.error('[DialogPanel] 加载历史失败:', error)
    // 静默失败，不显示错误提示
  } finally {
    isLoadingHistory.value = false
  }
}

// 设置选中的文字（供父组件调用）
const setSelectedText = (text: string, context?: { beforeContext: string; afterContext: string; fullText: string }) => {
  selectedTextRef.value = text
  selectedTextContext.value = context || null
  console.log('[DialogPanel] 收到选中文字:', text.substring(0, 50) + '...')
}

// 清除选中的文字
const clearSelectedText = () => {
  selectedTextRef.value = ''
  selectedTextContext.value = null
}

// 设置快捷指令
const setQuickInstruction = (instruction: string) => {
  inputMessage.value = instruction
}

// 发送消息（使用流式API）
const sendMessage = async () => {
  const userMessage = inputMessage.value.trim()
  if (!userMessage || isSending.value) return

  // 保存当前选中的文字（发送后清除）
  const quotedText = selectedTextRef.value
  const quotedContext = selectedTextContext.value

  // 添加用户消息到界面
  const userMessageObj: ExtendedDialogMessage = {
    id: `user_${Date.now()}`,
    role: 'user',
    content: userMessage,
    timestamp: new Date().toISOString(),
    quoted_text: quotedText || undefined
  }
  messages.value.push(userMessageObj)
  
  // 清空输入和选中文字，重置思考状态
  inputMessage.value = ''
  clearSelectedText()
  thinkingText.value = ''
  isThinkingExpanded.value = false
  isSending.value = true
  scrollToBottom()

  try {
    // 构建请求参数
    const requestParams: any = {
      session_id: props.sessionId,
      message: userMessage,
      conversation_id: currentConversationId.value || undefined,
      current_charts: props.charts,
      current_report_text: props.reportText,
      current_html_charts: props.htmlCharts
    }

    // 如果有选中的文字，添加到请求中
    if (quotedText) {
      requestParams.selected_text = quotedText
      if (quotedContext) {
        requestParams.selected_text_context = quotedContext
      }
    }

    // 使用流式API
    await sendDialogMessageStream(
      requestParams,
      // onThinking - 收到思考内容
      (thinkingContent: string) => {
        thinkingText.value += thinkingContent
        scrollToBottom()
      },
      // onContent - 收到正式内容（暂时不处理，等done时一起处理）
      (_contentText: string) => {
        // 可以在这里实时显示内容，但目前我们等done时统一处理
      },
      // onDone - 完成
      (result: any) => {
        // 更新conversation_id
        currentConversationId.value = result.conversation_id

        // 添加AI回复到界面
        const aiMessageObj: ExtendedDialogMessage = {
          id: `ai_${Date.now()}`,
          role: 'assistant',
          content: result.response,
          timestamp: new Date().toISOString(),
          modified_charts: result.modified_charts
        }
        messages.value.push(aiMessageObj)

        // 通知父组件更新报告
        if (result.action_type === 'regenerate_report') {
          emit('dialog-response', {
            action_type: 'regenerate_report',
            new_report_text: result.new_report_text,
            new_html_charts: result.new_html_charts
          })
        } else if (result.action_type === 'modify_text') {
          emit('dialog-response', {
            action_type: 'modify_text',
            new_report_text: result.new_report_text,
            original_text: quotedText,
            modified_text: result.modified_text
          })
        } else if (result.action_type === 'add_content') {
          // 添加新内容到报告
          emit('dialog-response', {
            action_type: 'add_content',
            new_report_text: result.new_report_text
          })
        } else if (result.action_type === 'delete_content') {
          // 删除内容
          emit('dialog-response', {
            action_type: 'delete_content',
            new_report_text: result.new_report_text
          })
        } else if (result.modified_charts && result.modified_charts.length > 0) {
          emit('dialog-response', {
            charts: result.modified_charts,
            action_type: result.action_type
          })
        }

        // 清除思考内容，完成发送
        thinkingText.value = ''
        isSending.value = false
        scrollToBottom()
      },
      // onError - 错误
      (error: string) => {
        console.error('[DialogPanel] 流式请求错误:', error)
        ElMessage.error(error || '发送消息失败，请重试')
        
        // 添加错误消息
        const errorMessageObj: ExtendedDialogMessage = {
          id: `error_${Date.now()}`,
          role: 'assistant',
          content: '抱歉，处理您的请求时出现了错误，请重试。',
          timestamp: new Date().toISOString()
        }
        messages.value.push(errorMessageObj)
        
        thinkingText.value = ''
        isSending.value = false
        scrollToBottom()
      }
    )
  } catch (error: any) {
    console.error('[DialogPanel] 发送消息失败:', error)
    ElMessage.error(error.message || '发送消息失败，请重试')
    
    // 添加错误消息
    const errorMessageObj: ExtendedDialogMessage = {
      id: `error_${Date.now()}`,
      role: 'assistant',
      content: '抱歉，处理您的请求时出现了错误，请重试。',
      timestamp: new Date().toISOString()
    }
    messages.value.push(errorMessageObj)
    
    thinkingText.value = ''
    isSending.value = false
    scrollToBottom()
  }
}

// 处理键盘事件
const handleKeyDown = (event: Event | KeyboardEvent) => {
  const e = event as KeyboardEvent
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 使用示例
const useExample = (example: string) => {
  inputMessage.value = example
  sendMessage()
}

// 清除历史
const handleClearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除所有对话历史吗？此操作不可恢复。',
      '确认清除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await clearDialogHistory(props.sessionId)
    messages.value = []
    currentConversationId.value = ''
    emit('history-cleared')
    ElMessage.success('对话历史已清除')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('[DialogPanel] 清除历史失败:', error)
      ElMessage.error('清除历史失败')
    }
  }
}

// 退出编辑模式
const handleExitEdit = () => {
  emit('exit-edit')
}

// 暴露方法给父组件
defineExpose({
  setSelectedText,
  clearSelectedText
})

// 监听sessionId变化，重新加载历史
watch(() => props.sessionId, (newId) => {
  if (newId) {
    messages.value = []
    currentConversationId.value = props.conversationId
    loadHistory()
  }
})

// 组件挂载时加载历史
onMounted(() => {
  if (props.sessionId) {
    loadHistory()
  }
})
</script>

<style scoped>
.dialog-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 0;
  border-right: 1px solid #e0e0e0;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  background: #ffffff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dialog-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  background: #e8f5e9;
  color: #2e7d32;
  font-weight: 500;
}

.status-badge.online {
  background: #e8f5e9;
  color: #2e7d32;
}

.header-actions {
  display: flex;
  gap: 4px;
}

.header-actions :deep(.el-button) {
  color: #666;
}

.header-actions .exit-btn {
  color: #f56c6c !important;
  font-weight: 500;
}

.header-actions .exit-btn:hover {
  background: #fef0f0 !important;
  color: #f56c6c !important;
}

.header-actions :deep(.el-button:hover) {
  background: #f5f5f5;
  color: #333;
}

.dialog-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 欢迎消息 */
.welcome-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0 0 8px 0;
}

.welcome-desc {
  font-size: 14px;
  color: #86868b;
  margin: 0 0 24px 0;
  line-height: 1.5;
}

.welcome-examples {
  width: 100%;
}

.examples-title {
  font-size: 13px;
  color: #86868b;
  margin: 0 0 12px 0;
}

.example-tag {
  margin: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.example-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 消息列表 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-list::-webkit-scrollbar {
  width: 6px;
}

.message-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.message-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

.message-item {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease-in;
}

/* 版本保存点标记样式 */
.version-marker {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 24px 0;
  position: relative;
}

.marker-line {
  width: 100%;
  height: 1px;
  background: linear-gradient(to right, transparent, #e0e0e0, transparent);
  margin-bottom: 12px;
}

.marker-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  }
  50% {
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.5);
  }
}

.marker-text {
  white-space: nowrap;
}

.marker-time {
  margin-top: 6px;
  font-size: 11px;
  color: #999;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: #667eea;
  color: #ffffff;
}

.message-item.user .message-avatar {
  background: #409eff;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  background: #f5f5f7;
}

.message-item.user .message-bubble {
  background: #409eff;
  color: #ffffff;
}

.message-content {
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-time {
  font-size: 11px;
  color: #86868b;
  margin-top: 6px;
}

.message-item.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.message-charts {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  font-size: 12px;
  color: #667eea;
}

.message-item.user .message-charts {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

/* 加载动画 */
.message-item.loading .message-bubble {
  padding: 16px;
}

.loading-dots {
  display: flex;
  gap: 6px;
  align-items: center;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #667eea;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* 思考过程样式 */
.message-item.thinking .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.thinking-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.thinking-bubble {
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%) !important;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.thinking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.thinking-label {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
}

.expand-btn {
  font-size: 12px !important;
  padding: 2px 8px !important;
  color: #999 !important;
}

.expand-btn:hover {
  color: #667eea !important;
}

.thinking-content {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  max-height: 80px;
  overflow: hidden;
  transition: max-height 0.3s ease;
  white-space: pre-wrap;
  word-break: break-word;
}

.thinking-content.expanded {
  max-height: 400px;
  overflow-y: auto;
}

.thinking-content::-webkit-scrollbar {
  width: 4px;
}

.thinking-content::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 2px;
}

/* 输入区 */
.input-area {
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background: #ffffff;
}

.input-area :deep(.el-textarea__inner) {
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  resize: none;
  font-size: 14px;
}

.input-area :deep(.el-textarea__inner:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.input-area :deep(.el-button) {
  border-radius: 12px;
  padding: 12px 20px;
  height: auto;
}

/* 选中文字引用区 */
.selected-text-quote {
  margin: 0 20px 12px 20px;
  padding: 12px;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
  border-radius: 12px;
  border-left: 4px solid #667eea;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.quote-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.quote-icon {
  font-size: 16px;
}

.quote-title {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
  flex: 1;
}

.clear-quote-btn {
  padding: 4px !important;
  color: #999 !important;
}

.clear-quote-btn:hover {
  color: #667eea !important;
}

.quote-text {
  font-size: 13px;
  color: #333;
  line-height: 1.6;
  max-height: 80px;
  overflow-y: auto;
  padding: 8px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
}

.quote-text::-webkit-scrollbar {
  width: 4px;
}

.quote-text::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 2px;
}

/* 消息中的引用样式 */
.message-quote {
  margin-bottom: 10px;
  padding: 10px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.message-item.user .message-quote {
  background: rgba(255, 255, 255, 0.2);
  border-left-color: rgba(255, 255, 255, 0.5);
}

.quote-label {
  font-size: 11px;
  color: #667eea;
  font-weight: 600;
  margin-bottom: 4px;
}

.message-item.user .quote-label {
  color: rgba(255, 255, 255, 0.9);
}

.quote-content {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message-item.user .quote-content {
  color: rgba(255, 255, 255, 0.85);
}

/* 快捷指令 */
.quick-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px 16px 20px;
  flex-wrap: wrap;
}

.quick-label {
  font-size: 12px;
  color: #999;
}

.quick-actions :deep(.el-button) {
  font-size: 12px;
  padding: 4px 10px;
  color: #667eea;
  border: 1px solid #e0e0e0;
  border-radius: 16px;
  background: #fff;
}

.quick-actions :deep(.el-button:hover) {
  background: #f0f4ff;
  border-color: #667eea;
}
</style>
