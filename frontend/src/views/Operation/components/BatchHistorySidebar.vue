<template>
  <div class="history-sidebar">
    <!-- 顶部：标题和新建按钮 -->
    <div class="sidebar-header">
      <div class="header-title">
        <span>批量分析历史</span>
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
        placeholder="搜索批量分析会话"
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
          <el-icon><DocumentCopy /></el-icon>
        </div>
        <div class="session-info">
          <div class="session-title">{{ getSessionTitle(session) }}</div>
          <div class="session-meta">
            <span class="session-time">{{ formatTime(session.updated_at) }}</span>
            <el-tag 
              :type="getStatusType(session.status)" 
              size="small"
            >
              {{ getStatusText(session.status) }}
            </el-tag>
          </div>
          <div class="session-extra">
            <span class="sheet-count">{{ session.sheet_count }} 个Sheet</span>
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
      <div v-if="filteredSessions.length === 0 && !loading" class="empty-sessions">
        <el-empty description="暂无批量分析历史" :image-size="80" />
      </div>
      <div v-if="loading" class="loading-sessions">
        <el-skeleton :rows="3" animated />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChatDotRound, Plus, Search, DocumentCopy, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { BatchSession } from '@/api/operation'
import type { ApiResponse } from '@/types'
import { getBatchSessions, deleteBatchSession, createBatchSession } from '@/api/operation'
import { useOperationStore } from '@/stores/operation'

const emit = defineEmits<{
  (e: 'session-selected', sessionId: number): void
  (e: 'create-new'): void
}>()

const operationStore = useOperationStore()
const searchKeyword = ref('')
const loading = ref(false)
const sessions = ref<BatchSession[]>([])

const currentSessionId = computed(() => operationStore.batchSessionId)

const filteredSessions = computed(() => {
  if (!searchKeyword.value.trim()) {
    return sessions.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return sessions.value.filter(session => 
    session.original_file_name.toLowerCase().includes(keyword)
  )
})

const getSessionTitle = (session: BatchSession) => {
  const fileName = session.original_file_name
  if (fileName) {
    const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '')
    return nameWithoutExt || fileName
  }
  return `批量分析_${session.id}`
}

const formatTime = (time: string) => {
  if (!time) return ''
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
  const statusMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    draft: 'info',
    completed: 'success',
    processing: 'warning',
    failed: 'danger',
    partial_failed: 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    completed: '已完成',
    processing: '处理中',
    failed: '失败',
    partial_failed: '部分失败'
  }
  return textMap[status] || '未知'
}

const handleLoadSession = (sessionId: number) => {
  operationStore.setBatchSession(sessionId)
  emit('session-selected', sessionId)
}

const handleCreateNew = async () => {
  try {
    loading.value = true
    const response = await createBatchSession()
    const createResponse = response as unknown as ApiResponse<any>
    if (createResponse.success && createResponse.data) {
      const newSession = createResponse.data
      // 添加到列表顶部，立即显示
      sessions.value.unshift(newSession)
      // 设置当前会话
      operationStore.setBatchSession(newSession.id)
      // 触发事件通知父组件（这会重置上传界面）
      emit('create-new')
      ElMessage.success('新批量分析会话已创建')
      
      // 异步刷新会话列表以确保数据同步
      setTimeout(async () => {
        try {
          await loadSessions()
        } catch (error) {
          console.warn('刷新批量分析会话列表失败:', error)
        }
      }, 300)
    } else {
      const createErrorResponse = response as unknown as ApiResponse<any>
      ElMessage.error(createErrorResponse.message || '创建批量分析会话失败')
    }
  } catch (error: any) {
    console.error('创建批量分析会话失败:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '创建批量分析会话失败')
  } finally {
    loading.value = false
  }
}

const handleDeleteSession = async (sessionId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个批量分析会话吗？删除后将无法恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const response = await deleteBatchSession(sessionId)
    const deleteResponse = response as unknown as ApiResponse<any>
    if (deleteResponse.success) {
      ElMessage.success('会话已删除')
      
      if (currentSessionId.value === sessionId) {
        operationStore.setBatchSession(null)
      }
      
      await loadSessions()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除会话失败')
    }
  }
}

const loadSessions = async () => {
  try {
    loading.value = true
    const response = await getBatchSessions()
    const batchResponse = response as unknown as ApiResponse<any>
    if (batchResponse.success && batchResponse.data) {
      sessions.value = response.data.sessions || []
    }
  } catch (error: any) {
    console.error('加载批量分析会话列表失败:', error)
    ElMessage.error('加载批量分析会话列表失败')
  } finally {
    loading.value = false
  }
}

defineExpose({
  loadSessions
})

onMounted(() => {
  loadSessions()
})
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
  align-items: flex-start;
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
  margin-top: 2px;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  color: #ffffff;
  font-size: var(--apple-font-sm);
  font-weight: 500;
  margin-bottom: var(--apple-space-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--apple-space-sm);
  margin-bottom: var(--apple-space-xs);
}

.session-time {
  color: #a1a1a6;
  font-size: var(--apple-font-sm);
}

.session-extra {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sheet-count {
  color: #a1a1a6;
  font-size: 11px;
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

.loading-sessions {
  padding: 20px;
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
