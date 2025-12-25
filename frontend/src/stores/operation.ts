import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Session, ReportContent, BatchSession, BatchSheet, BatchStatusResponse } from '@/api/operation'

export const useOperationStore = defineStore('operation', () => {
  // 状态
  const currentSessionId = ref<number | null>(null)
  const sessions = ref<Session[]>([])
  const currentFile = ref<File | null>(null)
  const fileId = ref<number | null>(null)
  const reportContent = ref<ReportContent | null>(null)
  const reportId = ref<string | null>(null)
  const isGenerating = ref(false)
  const analysisRequest = ref('')
  
  // 批量分析相关状态
  const batchSessionId = ref<number | null>(null)
  const batchReports = ref<BatchSheet[]>([])
  const currentReportIndex = ref<number>(0)
  const batchStatus = ref<'idle' | 'uploading' | 'splitting' | 'analyzing' | 'completed' | 'failed'>('idle')
  const batchSessions = ref<BatchSession[]>([])
  const batchStatusData = ref<BatchStatusResponse | null>(null)
  
  // 定制化批量分析相关状态（独立存储）
  const customBatchSessionId = ref<number | null>(null)
  const customBatchReports = ref<BatchSheet[]>([])
  const customCurrentReportIndex = ref<number>(0)
  const customBatchStatus = ref<'idle' | 'uploading' | 'splitting' | 'analyzing' | 'completed' | 'failed'>('idle')
  const customBatchSessions = ref<BatchSession[]>([])
  const customBatchStatusData = ref<BatchStatusResponse | null>(null)
  
  // 计算属性
  const currentSession = computed(() => {
    return sessions.value.find(s => s.id === currentSessionId.value)
  })
  
  const canSubmit = computed(() => {
    return fileId.value !== null && analysisRequest.value.trim().length > 0
  })
  
  // 方法
  function setCurrentSession(sessionId: number | null) {
    currentSessionId.value = sessionId
  }
  
  function setSessions(sessionList: Session[]) {
    sessions.value = sessionList
  }
  
  function addSession(session: Session) {
    sessions.value.unshift(session)
  }
  
  function updateSession(session: Session) {
    const index = sessions.value.findIndex(s => s.id === session.id)
    if (index !== -1) {
      sessions.value[index] = session
    }
  }
  
  function removeSession(sessionId: number) {
    const index = sessions.value.findIndex(s => s.id === sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)
    }
    // 如果删除的是当前选中的会话，清空选中状态
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
    }
  }
  
  function setCurrentFile(file: File | null) {
    currentFile.value = file
  }
  
  function setFileId(id: number | null) {
    fileId.value = id
  }
  
  function setReportContent(content: ReportContent | null) {
    // 确保 text 字段是有效的字符串，不是 Promise 或其字符串表示
    if (content && content.text) {
      if (typeof content.text !== 'string') {
        console.error('[Store] content.text 不是字符串:', typeof content.text, content.text)
        content.text = String(content.text) || ''
      }
      // 检查是否是 Promise 的字符串表示
      if (content.text.includes('[object Promise]') || content.text === '[object Object]') {
        console.error('[Store] content.text 包含无效值:', content.text)
        content.text = '报告内容加载异常，请重新生成'
      }
    }
    reportContent.value = content
  }
  
  function setReportId(id: string | null) {
    reportId.value = id
  }
  
  function setGenerating(generating: boolean) {
    isGenerating.value = generating
  }
  
  function setAnalysisRequest(request: string) {
    analysisRequest.value = request
  }
  
  function reset() {
    currentSessionId.value = null
    currentFile.value = null
    fileId.value = null
    reportContent.value = null
    reportId.value = null
    analysisRequest.value = ''
    isGenerating.value = false
  }
  
  function clearSession() {
    // 清空当前会话的所有状态
    currentSessionId.value = null
    currentFile.value = null
    fileId.value = null
    reportContent.value = null
    reportId.value = null
    analysisRequest.value = ''
    isGenerating.value = false
  }
  
  // 批量分析相关方法
  function setBatchSession(id: number | null) {
    batchSessionId.value = id
  }
  
  function setBatchReports(reports: BatchSheet[]) {
    batchReports.value = reports
  }
  
  function setCurrentReportIndex(index: number) {
    currentReportIndex.value = index
  }
  
  function setBatchStatus(status: 'idle' | 'uploading' | 'splitting' | 'analyzing' | 'completed' | 'failed') {
    batchStatus.value = status
  }
  
  function setBatchSessions(sessions: BatchSession[]) {
    batchSessions.value = sessions
  }
  
  function setBatchStatusData(data: BatchStatusResponse | null) {
    batchStatusData.value = data
  }
  
  function resetBatch() {
    batchSessionId.value = null
    batchReports.value = []
    currentReportIndex.value = 0
    batchStatus.value = 'idle'
    batchSessions.value = []
    batchStatusData.value = null
  }
  
  // 定制化批量分析相关方法
  function setCustomBatchSession(id: number | null) {
    customBatchSessionId.value = id
  }
  
  function setCustomBatchReports(reports: BatchSheet[]) {
    customBatchReports.value = reports
  }
  
  function setCustomCurrentReportIndex(index: number) {
    customCurrentReportIndex.value = index
  }
  
  function setCustomBatchStatus(status: 'idle' | 'uploading' | 'splitting' | 'analyzing' | 'completed' | 'failed') {
    customBatchStatus.value = status
  }
  
  function setCustomBatchSessions(sessions: BatchSession[]) {
    customBatchSessions.value = sessions
  }
  
  function setCustomBatchStatusData(data: BatchStatusResponse | null) {
    customBatchStatusData.value = data
  }
  
  function resetCustomBatch() {
    customBatchSessionId.value = null
    customBatchReports.value = []
    customCurrentReportIndex.value = 0
    customBatchStatus.value = 'idle'
    customBatchSessions.value = []
    customBatchStatusData.value = null
  }
  
  // 批量分析计算属性
  const currentReport = computed(() => {
    if (batchReports.value.length === 0 || currentReportIndex.value < 0 || currentReportIndex.value >= batchReports.value.length) {
      return null
    }
    return batchReports.value[currentReportIndex.value]
  })
  
  const batchProgress = computed(() => {
    if (!batchStatusData.value || batchStatusData.value.total_sheets === 0) {
      return 0
    }
    return Math.round((batchStatusData.value.completed_sheets / batchStatusData.value.total_sheets) * 100)
  })
  
  // 定制化批量分析计算属性
  const customCurrentReport = computed(() => {
    if (customBatchReports.value.length === 0 || customCurrentReportIndex.value < 0 || customCurrentReportIndex.value >= customBatchReports.value.length) {
      return null
    }
    return customBatchReports.value[customCurrentReportIndex.value]
  })
  
  const customBatchProgress = computed(() => {
    if (!customBatchStatusData.value || customBatchStatusData.value.total_sheets === 0) {
      return 0
    }
    return Math.round((customBatchStatusData.value.completed_sheets / customBatchStatusData.value.total_sheets) * 100)
  })
  
  return {
    // 状态
    currentSessionId,
    sessions,
    currentFile,
    fileId,
    reportContent,
    reportId,
    isGenerating,
    analysisRequest,
    // 批量分析状态
    batchSessionId,
    batchReports,
    currentReportIndex,
    batchStatus,
    batchSessions,
    batchStatusData,
    // 定制化批量分析状态（独立）
    customBatchSessionId,
    customBatchReports,
    customCurrentReportIndex,
    customBatchStatus,
    customBatchSessions,
    customBatchStatusData,
    // 计算属性
    currentSession,
    canSubmit,
    currentReport,
    batchProgress,
    customCurrentReport,
    customBatchProgress,
    // 方法
    setCurrentSession,
    setSessions,
    addSession,
    updateSession,
    removeSession,
    setCurrentFile,
    setFileId,
    setReportContent,
    setReportId,
    setGenerating,
    setAnalysisRequest,
    reset,
    clearSession,
    // 批量分析方法
    setBatchSession,
    setBatchReports,
    setCurrentReportIndex,
    setBatchStatus,
    setBatchSessions,
    setBatchStatusData,
    resetBatch,
    // 定制化批量分析方法（独立）
    setCustomBatchSession,
    setCustomBatchReports,
    setCustomCurrentReportIndex,
    setCustomBatchStatus,
    setCustomBatchSessions,
    setCustomBatchStatusData,
    resetCustomBatch
  }
})

