<template>
  <div class="history-sidebar">
    <!-- 顶部：标题和新建按钮 -->
    <div class="sidebar-header">
      <div class="header-title">
        <span>历史会话</span>
        <el-icon><ChatDotRound /></el-icon>
      </div>
      <el-button 
        type="primary" 
        size="small" 
        :icon="Plus"
        @click="handleCreateNew"
      >
        新建会话
      </el-button>
    </div>

    <!-- 搜索框 -->
    <div class="search-box">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索历史会话"
        :prefix-icon="Search"
        clearable
        size="small"
      />
    </div>

    <!-- 会话列表 -->
    <div class="session-list">
      <div 
        v-for="session in filteredSessions" 
        :key="session.id"
        class="session-item"
        :class="{ active: currentSessionId === session.id }"
        @click="handleLoadSession(session.id)"
      >
        <div class="session-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="session-info">
          <div class="session-title">{{ session.title }}</div>
          <div class="session-meta">
            <span class="session-time">{{ formatTime(session.updated_at) }}</span>
            <el-tag 
              :type="getStatusType(session.status)" 
              size="small"
            >
              {{ getStatusText(session.status) }}
            </el-tag>
          </div>
        </div>
        <div class="session-actions" @click.stop>
          <el-button
            :icon="Delete"
            type="danger"
            text
            size="small"
            circle
            @click="handleDeleteSession(session.id)"
            title="删除会话"
          />
        </div>
      </div>
      <div v-if="filteredSessions.length === 0" class="empty-sessions">
        <el-empty description="暂无历史会话" :image-size="80" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChatDotRound, Plus, Search, Document, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Session } from '@/api/operation'
import { useOperationStore } from '@/stores/operation'
import { createSession, getSessions, deleteSession } from '@/api/operation'

const emit = defineEmits<{
  (e: 'session-selected', sessionId: number): void
  (e: 'session-created', session: Session): void
}>()

const operationStore = useOperationStore()
const searchKeyword = ref('')
const loading = ref(false)

const currentSessionId = computed(() => operationStore.currentSessionId)
const sessions = computed(() => operationStore.sessions)

const filteredSessions = computed(() => {
  if (!searchKeyword.value.trim()) {
    return sessions.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return sessions.value.filter(session => 
    session.title.toLowerCase().includes(keyword)
  )
})

const formatTime = (time: string) => {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return '今天'
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, 'success' | 'warning' | 'info'> = {
    completed: 'success',
    in_progress: 'warning',
    draft: 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    completed: '已完成',
    in_progress: '进行中',
    draft: '草稿'
  }
  return textMap[status] || '未知'
}

const handleCreateNew = async () => {
  try {
    loading.value = true
    const response = await createSession()
    if (response.success && response.data) {
      const newSession = response.data
      // 先添加到store（添加到列表顶部），立即显示
      operationStore.addSession(newSession)
      // 设置当前会话
      operationStore.setCurrentSession(newSession.id)
      // 触发事件通知父组件（这会重置上传界面）
      emit('session-created', newSession)
      ElMessage.success('新会话已创建')
      
      // 异步刷新会话列表以确保数据同步（不阻塞UI）
      // 延迟一点时间，确保服务器已保存
      setTimeout(async () => {
        try {
          await loadSessions()
        } catch (error) {
          // 静默处理刷新错误，不影响用户体验
          console.warn('刷新会话列表失败:', error)
        }
      }, 300)
    } else {
      ElMessage.error(response.message || '创建会话失败')
    }
  } catch (error: any) {
    console.error('创建会话失败:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '创建会话失败')
  } finally {
    loading.value = false
  }
}

const handleLoadSession = (sessionId: number) => {
  operationStore.setCurrentSession(sessionId)
  emit('session-selected', sessionId)
}

const handleDeleteSession = async (sessionId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个会话吗？删除后将无法恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const response = await deleteSession(sessionId)
    if (response.success) {
      ElMessage.success('会话已删除')
      
      // 如果删除的是当前选中的会话，清空选中状态
      if (currentSessionId.value === sessionId) {
        operationStore.setCurrentSession(null)
      }
      
      // 从store中移除会话
      operationStore.removeSession(sessionId)
      
      // 重新加载会话列表
      await loadSessions()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除会话失败')
    }
  }
}

// 加载会话列表
const loadSessions = async () => {
  try {
    loading.value = true
    const response = await getSessions()
    if (response.success && response.data) {
      // 保存当前选中的会话ID
      const currentId = operationStore.currentSessionId
      // 更新会话列表
      operationStore.setSessions(response.data.items)
      // 如果之前有选中的会话，确保它仍然被选中
      if (currentId) {
        const exists = response.data.items.find(s => s.id === currentId)
        if (exists) {
          operationStore.setCurrentSession(currentId)
        }
      }
    }
  } catch (error: any) {
    console.error('加载会话列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 暴露方法供父组件调用
defineExpose({
  loadSessions
})

// 初始化加载
loadSessions()
</script>

<style scoped>
.history-sidebar {
  width: 280px;
  height: 100vh;
  background: #2c2c2e;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #1c1c1e;
  box-shadow: var(--apple-shadow-md);
}

.sidebar-header {
  padding: var(--apple-space-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #3a3a3c;
}

.header-title {
  display: flex;
  align-items: center;
  gap: var(--apple-space-sm);
  color: #ffffff;
  font-size: var(--apple-font-lg);
  font-weight: 600;
  letter-spacing: -0.2px;
}

.search-box {
  padding: var(--apple-space-md) var(--apple-space-lg);
  border-bottom: 1px solid #3a3a3c;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: var(--apple-space-md);
  padding: var(--apple-space-md);
  margin-bottom: var(--apple-space-sm);
  border-radius: var(--apple-radius-md);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #363638;
  border: 1px solid #3a3a3c;
  position: relative;
}

.session-item:hover {
  background: #3a3a3c;
  border-color: var(--apple-primary);
  transform: translateX(2px);
}

.session-item.active {
  background: rgba(0, 122, 255, 0.2);
  border: 1px solid var(--apple-primary);
  box-shadow: 0 0 0 1px rgba(0, 122, 255, 0.3);
}

.session-icon {
  color: var(--apple-primary);
  font-size: 20px;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.session-time {
  color: #999;
  font-size: 12px;
}

.session-actions {
  display: flex;
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.empty-sessions {
  padding: 40px 20px;
  text-align: center;
}

:deep(.el-empty__description) {
  color: #a1a1a6;
}

:deep(.el-input__wrapper) {
  background: #363638;
  box-shadow: 0 0 0 1px #3a3a3c inset;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--apple-primary) inset;
}

:deep(.el-input__inner) {
  color: #ffffff;
}

:deep(.el-input__inner::placeholder) {
  color: #6e6e73;
}
</style>
