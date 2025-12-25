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
      <template v-for="session in filteredSessions" :key="session.id">
        <div 
          class="session-item"
          :class="{ 
            active: currentSessionId === session.id,
            expanded: expandedSessionId === session.id 
          }"
        >
          <!-- 会话主体 -->
          <div class="session-main" @click="handleLoadSession(session.id)">
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
                :icon="expandedSessionId === session.id ? ArrowUp : ArrowDown"
                text
                size="small"
                circle
                @click="toggleVersions(session.id)"
                :title="expandedSessionId === session.id ? '收起版本' : '展开版本'"
              />
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
          
          <!-- 版本列表二级菜单（使用 transition 实现平滑展开） -->
          <transition name="version-expand">
            <div 
              v-if="expandedSessionId === session.id" 
              class="version-submenu"
            >
              <div v-if="versionsLoading[session.id]" class="version-loading">
                <el-icon class="spin"><Loading /></el-icon>
                <span>正在加载版本...</span>
              </div>
              <template v-else>
                <div 
                  v-for="version in versionsMap[session.id] || []" 
                  :key="version.id" 
                  class="version-item"
                  :class="{ current: version.is_current }"
                  @click.stop="handleSelectVersion(session.id, version.id)"
                >
                  <div class="version-icon">
                    <el-icon><Document /></el-icon>
                  </div>
                  <div class="version-content">
                    <div class="version-header">
                      <span class="version-no">V{{ version.version_no }}</span>
                      <el-tag v-if="version.is_current" size="small" type="success">当前</el-tag>
                    </div>
                    <div class="version-details">
                      <span class="version-time">{{ formatTime(version.created_at) }}</span>
                      <span v-if="version.summary" class="version-summary">- {{ version.summary }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="(versionsMap[session.id] || []).length === 0" class="version-empty">
                  <el-icon><InfoFilled /></el-icon>
                  <span>暂无保存的版本</span>
                </div>
              </template>
            </div>
          </transition>
        </div>
      </template>
      <div v-if="filteredSessions.length === 0" class="empty-sessions">
        <el-empty description="暂无历史会话" :image-size="80" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChatDotRound, Plus, Search, Document, Delete, Loading, ArrowDown, ArrowUp, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Session, SessionVersionMeta, SessionVersionDetail } from '@/api/operation'
import type { ApiResponse } from '@/types'
import { useOperationStore } from '@/stores/operation'
import { createSession, getSessions, deleteSession, getSessionVersions, getSessionVersionDetail } from '@/api/operation'

const emit = defineEmits<{
  (e: 'session-selected', sessionId: number): void
  (e: 'session-created', session: Session): void
  (e: 'version-selected', payload: { sessionId: number; version: SessionVersionDetail }): void
}>()

const operationStore = useOperationStore()
const searchKeyword = ref('')
const loading = ref(false)
const expandedSessionId = ref<number | null>(null)
const versionsMap = ref<Record<number, SessionVersionMeta[]>>({})
const versionsLoading = ref<Record<number, boolean>>({})

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
    const createResponse = response as unknown as ApiResponse<any>
    if (createResponse.success && createResponse.data) {
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
      const createResponse = response as unknown as ApiResponse<any>
      ElMessage.error(createResponse.message || '创建会话失败')
    }
  } catch (error: any) {
    console.error('创建会话失败:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '创建会话失败')
  } finally {
    loading.value = false
  }
}

const handleLoadSession = (sessionId: number) => {
  console.log('🟢🟢🟢 [HistorySidebar] handleLoadSession被调用:', sessionId)
  operationStore.setCurrentSession(sessionId)
  // 持久化到localStorage
  localStorage.setItem('currentSessionId', String(sessionId))
  console.log('🟢🟢🟢 [HistorySidebar] 触发session-selected事件:', sessionId)
  emit('session-selected', sessionId)
  console.log('🟢🟢🟢 [HistorySidebar] session-selected事件已触发')
}

const toggleVersions = async (sessionId: number) => {
  if (expandedSessionId.value === sessionId) {
    expandedSessionId.value = null
    return
  }
  expandedSessionId.value = sessionId
  if (!versionsMap.value[sessionId]) {
    await loadVersions(sessionId)
  }
}

const loadVersions = async (sessionId: number) => {
  versionsLoading.value = { ...versionsLoading.value, [sessionId]: true }
  try {
    const res = await getSessionVersions(sessionId) as unknown as ApiResponse<SessionVersionMeta[]>
    if (res.success && res.data) {
      versionsMap.value = { ...versionsMap.value, [sessionId]: res.data }
    } else {
      versionsMap.value = { ...versionsMap.value, [sessionId]: [] }
    }
  } catch (error) {
    console.error('加载版本列表失败:', error)
    versionsMap.value = { ...versionsMap.value, [sessionId]: [] }
  } finally {
    versionsLoading.value = { ...versionsLoading.value, [sessionId]: false }
  }
}

const handleSelectVersion = async (sessionId: number, versionId: number) => {
  try {
    const res = await getSessionVersionDetail(sessionId, versionId) as unknown as ApiResponse<SessionVersionDetail>
    if (res.success && res.data) {
      emit('version-selected', { sessionId, version: res.data })
      ElMessage.success(`已切换到版本 V${res.data.version_no}`)
    } else {
      ElMessage.error(res.message || '获取版本详情失败')
    }
  } catch (error: any) {
    console.error('获取版本详情失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取版本详情失败')
  }
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
    const deleteResponse = response as unknown as ApiResponse<any>
    if (deleteResponse.success) {
      ElMessage.success('会话已删除')
      
      // 如果删除的是当前选中的会话，清空选中状态
      if (currentSessionId.value === sessionId) {
        operationStore.setCurrentSession(null)
        localStorage.removeItem('currentSessionId')
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
    const sessionsResponse = response as unknown as ApiResponse<any>
    if (sessionsResponse.success && sessionsResponse.data) {
      // 尝试从localStorage恢复currentSessionId（页面刷新后）
      const savedSessionId = localStorage.getItem('currentSessionId')
      const currentId = savedSessionId ? parseInt(savedSessionId, 10) : operationStore.currentSessionId
      
      // 更新会话列表
      operationStore.setSessions(sessionsResponse.data.items)
      
      // 如果之前有选中的会话（从Store或localStorage），确保它仍然被选中
      if (currentId) {
        const exists = sessionsResponse.data.items.find((s: any) => s.id === currentId)
        if (exists) {
          operationStore.setCurrentSession(currentId)
          // 注意：不在这里触发session-selected事件，让父组件的onMounted统一处理
        } else {
          // 如果会话不存在，清除localStorage
          localStorage.removeItem('currentSessionId')
          operationStore.setCurrentSession(null)
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
  margin-bottom: var(--apple-space-sm);
  border-radius: var(--apple-radius-md);
  background: #363638;
  border: 1px solid #3a3a3c;
  overflow: hidden;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.session-item.active {
  border-color: var(--apple-primary);
  box-shadow: 0 0 0 1px rgba(0, 122, 255, 0.3);
}

.session-item.expanded {
  background: #3a3a3c;
}

.session-main {
  display: flex;
  align-items: center;
  gap: var(--apple-space-md);
  padding: var(--apple-space-md);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.session-main:hover {
  background: rgba(255, 255, 255, 0.05);
}

.session-item.active .session-main {
  background: rgba(0, 122, 255, 0.15);
}

.session-icon {
  color: var(--apple-primary);
  font-size: 20px;
  flex-shrink: 0;
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
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-main:hover .session-actions {
  opacity: 1;
}

/* 版本二级菜单 */
.version-submenu {
  background: #2c2c2e;
  border-top: 1px solid #3a3a3c;
  padding: 4px 0;
}

/* 版本展开动画 */
.version-expand-enter-active,
.version-expand-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 500px;
  overflow: hidden;
}

.version-expand-enter-from,
.version-expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.version-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #bbb;
  font-size: 13px;
}

.version-loading .spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.version-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px 10px 40px;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.version-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-left-color: var(--apple-primary);
}

.version-item.current {
  background: rgba(76, 222, 128, 0.1);
  border-left-color: #4ade80;
}

.version-icon {
  color: #888;
  font-size: 16px;
  flex-shrink: 0;
}

.version-item.current .version-icon {
  color: #4ade80;
}

.version-content {
  flex: 1;
  min-width: 0;
}

.version-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.version-no {
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.version-details {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #888;
}

.version-time {
  color: #888;
}

.version-summary {
  color: #aaa;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.version-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #777;
  font-size: 12px;
}

.version-empty .el-icon {
  font-size: 16px;
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
