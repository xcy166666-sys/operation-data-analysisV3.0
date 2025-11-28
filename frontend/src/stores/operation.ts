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
    // 计算属性
    currentSession,
    canSubmit,
    currentReport,
    batchProgress,
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
    // 批量分析方法
    setBatchSession,
    setBatchReports,
    setCurrentReportIndex,
    setBatchStatus,
    setBatchSessions,
    setBatchStatusData,
    resetBatch
  }
})

