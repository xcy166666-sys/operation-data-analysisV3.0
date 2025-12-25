import request from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface Session {
  id: number
  title: string
  status: 'draft' | 'in_progress' | 'completed'
  created_at: string
  updated_at: string
  file_name?: string
  report_id?: number
  messages?: Array<{
    role: string
    content?: string
    timestamp?: string
    file_name?: string
    charts?: any[]
    html_charts?: string  // 新增：HTML图表内容
    tables?: any[]
  }>
}

export interface UploadResponse {
  file_id: number
  file_name: string
  row_count: number
  column_info: Record<string, string>
}

export interface ReportContent {
  text: string
  charts?: Array<{
    type: string
    data: any
    config?: any
  }>
  html_charts?: string  // 新增：HTML图表内容
  tables?: Array<{
    columns: Array<{ prop: string; label: string }>
    data: any[]
  }>
  metrics?: Record<string, number>
}

export interface ReportResponse {
  report_id: number
  content: ReportContent
}

// 会话版本
export interface SessionVersionMeta {
  id: number
  version_no: number
  summary?: string
  created_at: string
  is_current: boolean
}

export interface SessionVersionDetail {
  id: number
  version_no: number
  summary?: string
  report_text?: string
  report_html_charts?: string
  report_charts_json?: any
  created_at: string
}

// ==================== 批量分析相关接口 ====================

export interface BatchSheet {
  id: number
  sheet_name: string
  sheet_index: number
  split_file_path: string
  report_status: 'pending' | 'generating' | 'completed' | 'failed'
}

export interface BatchSession {
  id: number
  original_file_name: string
  sheet_count: number
  status: 'processing' | 'completed' | 'failed' | 'partial_failed'
  created_at: string
  updated_at: string
}

export interface BatchUploadResponse {
  batch_session_id: number
  sheet_count: number
  sheets: BatchSheet[]
  status: string
}

export interface BatchStatusResponse {
  batch_session_id: number
  status: string
  total_sheets: number
  completed_sheets: number
  failed_sheets: number
  generating_sheets: number
  pending_sheets: number
  reports: Array<{
    id: number
    sheet_name: string
    sheet_index: number
    report_status: string
    report_content?: ReportContent
    error_message?: string
  }>
}

export interface SheetReportDetail {
  id: number
  sheet_name: string
  sheet_index: number
  report_status: string
  report_content: ReportContent
  error_message?: string
  created_at?: string
  updated_at?: string
}

/**
 * 获取会话列表（简化版，移除project_id参数）
 */
export function getSessions(params?: {
  page?: number
  page_size?: number
  search?: string
}) {
  return request.get<ApiResponse<{ items: Session[], total: number }>>(
    `/operation/sessions`,
    { params }
  )
}

/**
 * 创建新会话（简化版，移除project_id参数）
 */
export function createSession(title?: string) {
  const data: any = {}
  if (title) {
    data.title = title
  }
  return request.post<ApiResponse<Session>>(
    `/operation/sessions`,
    data
  )
}

/**
 * 获取会话详情
 */
export function getSessionDetail(sessionId: number) {
  return request.get<ApiResponse<Session>>(`/operation/sessions/${sessionId}`)
}

/**
 * 删除会话
 */
export function deleteSession(sessionId: number) {
  return request.delete<ApiResponse<{
    deleted_id: number
  }>>(`/operation/sessions/${sessionId}`)
}

// ==================== 会话版本相关 ====================
export function getSessionVersions(sessionId: number) {
  return request.get<ApiResponse<SessionVersionMeta[]>>(
    `/operation/sessions/${sessionId}/versions`
  )
}

export function getSessionVersionDetail(sessionId: number, versionId: number) {
  return request.get<ApiResponse<SessionVersionDetail>>(
    `/operation/sessions/${sessionId}/versions/${versionId}`
  )
}

export function createSessionVersion(sessionId: number, payload: {
  summary?: string
  report_text?: string
  report_html_charts?: string
  report_charts_json?: any
}) {
  return request.post<ApiResponse<SessionVersionDetail>>(
    `/operation/sessions/${sessionId}/versions`,
    payload
  )
}

/**
 * 上传Excel文件（简化版，移除project_id参数）
 */
export function uploadExcel(file: File, sessionId: number, onProgress?: (progress: number) => void) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('session_id', sessionId.toString())
  
  return request.post<ApiResponse<UploadResponse>>(
    '/operation/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent: any) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100)
          onProgress(percent)
        }
      }
    }
  )
}

/**
 * 生成分析报告（简化版，移除project_id参数）
 */
export function generateReport(data: {
  session_id: number
  file_id: number
  analysis_request: string
  chart_customization_prompt?: string  // 新增：图表定制prompt
  chart_generation_mode?: string  // 新增：图表生成模式 "html" 或 "json"
}) {
  const formData = new FormData()
  formData.append('session_id', data.session_id.toString())
  formData.append('file_id', data.file_id.toString())
  formData.append('analysis_request', data.analysis_request)
  if (data.chart_customization_prompt) {
    formData.append('chart_customization_prompt', data.chart_customization_prompt)
  }
  if (data.chart_generation_mode) {
    formData.append('chart_generation_mode', data.chart_generation_mode)
  }
  
  return request.post<ApiResponse<ReportResponse>>(
    '/operation/generate',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
}

/**
 * 获取报告详情
 */
export function getReport(reportId: number) {
  return request.get<ApiResponse<ReportResponse>>(`/operation/reports/${reportId}`)
}

/**
 * 图表图片数据接口
 */
export interface ChartImage {
  index: number
  title: string
  image: string  // Base64编码的图片数据 (data:image/png;base64,...)
}

/**
 * 下载报告PDF（支持图表图片）（简化版，移除project_id参数）
 */
export function downloadReportPDF(
  reportId: string, 
  sessionId: number,
  chartImages?: ChartImage[]
) {
  return request.post(
    `/operation/reports/${reportId}/download`,
    {
      session_id: sessionId,
      chart_images: chartImages || []
    },
    {
      responseType: 'blob'
    }
  )
}

/**
 * 下载报告图片（PNG格式，避免PDF中文乱码）（简化版，移除project_id参数）
 */
export function downloadReportImage(
  reportId: string,
  sessionId: number
) {
  return request.get(
    `/operation/reports/${reportId}/download-image`,
    {
      params: {
        session_id: sessionId
      },
      responseType: 'blob'
    }
  )
}

/**
 * 下载Excel模板
 */
export function downloadTemplate() {
  return request.get(
    '/operation/template',
    {
      responseType: 'blob'
    }
  )
}

// ==================== 批量分析相关API ====================

/**
 * 上传多Sheet文件并拆分（简化版，移除project_id参数）
 */
export function uploadBatchExcel(
  file: File,
  analysisRequest: string,
  onProgress?: (progress: number) => void
) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('analysis_request', analysisRequest)
  
  return request.post<ApiResponse<BatchUploadResponse>>(
    '/operation/batch/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent: any) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100)
          onProgress(percent)
        }
      }
    }
  )
}

/**
 * 开始批量分析（简化版，移除project_id参数）
 */
export function startBatchAnalysis(
  batchSessionId: number, 
  analysisRequest: string,
  chartCustomizationPrompt?: string,
  chartGenerationMode: string = "html"
) {
  const formData = new FormData()
  formData.append('batch_session_id', batchSessionId.toString())
  formData.append('analysis_request', analysisRequest)
  formData.append('chart_generation_mode', chartGenerationMode)
  if (chartCustomizationPrompt) {
    formData.append('chart_customization_prompt', chartCustomizationPrompt)
  }
  
  return request.post<ApiResponse<{
    batch_session_id: number
    status: string
    total_sheets: number
    completed_sheets: number
  }>>(
    '/operation/batch/analyze',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
}

/**
 * 获取批量分析状态（用于轮询）（简化版，移除project_id参数）
 */
export function getBatchAnalysisStatus(batchSessionId: number) {
  return request.get<ApiResponse<BatchStatusResponse>>(
    `/operation/batch/${batchSessionId}/status`
  )
}

/**
 * 获取单个Sheet报告详情（批量分析）（简化版，移除project_id参数）
 */
export function getSheetReport(reportId: number) {
  return request.get<ApiResponse<SheetReportDetail>>(
    `/operation/batch/reports/${reportId}`
  )
}

/**
 * 创建新的批量分析会话（简化版，移除project_id参数）
 */
export function createBatchSession(title?: string) {
  const data: any = {}
  if (title) {
    data.title = title
  }
  return request.post<ApiResponse<BatchSession>>(
    '/operation/batch/sessions',
    data
  )
}

/**
 * 获取批量分析会话列表（简化版，移除project_id参数）
 */
export function getBatchSessions(params?: {
  page?: number
  page_size?: number
}) {
  return request.get<ApiResponse<{
    sessions: BatchSession[]
    pagination: {
      page: number
      page_size: number
      total: number
      pages: number
    }
  }>>(
    '/operation/batch/sessions',
    { params }
  )
}

/**
 * 删除批量分析会话（简化版，移除project_id参数）
 */
export function deleteBatchSession(batchSessionId: number) {
  return request.delete<ApiResponse<{
    deleted_id: number
  }>>(
    `/operation/batch/sessions/${batchSessionId}`
  )
}

/**
 * 下载批量分析报告PDF（支持图表图片）（简化版，移除project_id参数）
 */
export function downloadBatchReportPDF(
  reportId: number,
  chartImages?: ChartImage[]
) {
  return request.post(
    `/operation/batch/reports/${reportId}/download`,
    {
      chart_images: chartImages || []
    },
    {
      responseType: 'blob'
    }
  )
}

// ==================== 定制化批量分析相关API ====================

/**
 * 上传多Sheet文件并拆分（定制化批量分析）
 */
export function uploadCustomBatchExcel(
  file: File,
  analysisRequest: string,
  onProgress?: (progress: number) => void
) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('analysis_request', analysisRequest)
  
  return request.post<ApiResponse<BatchUploadResponse>>(
    '/operation/custom-batch/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent: any) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100)
          onProgress(percent)
        }
      }
    }
  )
}

/**
 * 开始定制化批量分析
 */
export function startCustomBatchAnalysis(batchSessionId: number, analysisRequest: string) {
  const formData = new FormData()
  formData.append('batch_session_id', batchSessionId.toString())
  formData.append('analysis_request', analysisRequest)
  
  return request.post<ApiResponse<{
    batch_session_id: number
    status: string
    total_sheets: number
    completed_sheets: number
  }>>(
    '/operation/custom-batch/analyze',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
}

/**
 * 获取定制化批量分析状态（用于轮询）
 */
export function getCustomBatchAnalysisStatus(batchSessionId: number) {
  return request.get<ApiResponse<BatchStatusResponse>>(
    `/operation/custom-batch/${batchSessionId}/status`
  )
}

/**
 * 获取单个Sheet报告详情（定制化批量分析）
 */
export function getCustomSheetReport(reportId: number) {
  return request.get<ApiResponse<SheetReportDetail>>(
    `/operation/custom-batch/reports/${reportId}`
  )
}

/**
 * 创建新的定制化批量分析会话
 */
export function createCustomBatchSession(title?: string) {
  const data: any = {}
  if (title) {
    data.title = title
  }
  return request.post<ApiResponse<BatchSession>>(
    '/operation/custom-batch/sessions',
    data
  )
}

/**
 * 获取定制化批量分析会话列表
 */
export function getCustomBatchSessions(params?: {
  page?: number
  page_size?: number
}) {
  return request.get<ApiResponse<{
    sessions: BatchSession[]
    pagination: {
      page: number
      page_size: number
      total: number
      pages: number
    }
  }>>(
    '/operation/custom-batch/sessions',
    { params }
  )
}

/**
 * 删除定制化批量分析会话
 */
export function deleteCustomBatchSession(batchSessionId: number) {
  return request.delete<ApiResponse<{
    deleted_id: number
  }>>(
    `/operation/custom-batch/sessions/${batchSessionId}`
  )
}

/**
 * 下载定制化批量分析报告PDF（支持图表图片）
 */
export function downloadCustomBatchReportPDF(
  reportId: number,
  chartImages?: ChartImage[]
) {
  return request.post(
    `/operation/custom-batch/reports/${reportId}/download`,
    {
      chart_images: chartImages || []
    },
    {
      responseType: 'blob'
    }
  )
}

// ==================== AI对话相关接口 ====================

export interface DialogMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  modified_charts?: any[]
  isError?: boolean
}

export interface DialogResponse {
  response: string
  modified_charts: any[]
  conversation_id: string
  action_type: 'chat' | 'modify_chart' | 'analysis' | 'error'
}

export interface DialogHistoryResponse {
  messages: DialogMessage[]
  conversation_id?: string
  file_id?: string
}

/**
 * 发送对话消息
 */
export function sendDialogMessage(data: {
  session_id: number
  user_message: string
  current_charts?: any[]
  conversation_id?: string
}) {
  const formData = new FormData()
  formData.append('session_id', data.session_id.toString())
  formData.append('user_message', data.user_message)
  formData.append('current_charts', JSON.stringify(data.current_charts || []))
  if (data.conversation_id) {
    formData.append('conversation_id', data.conversation_id)
  }

  return request.post<ApiResponse<DialogResponse>>(
    '/operation/dialog',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
}

/**
 * 获取对话历史
 */
export function getDialogHistory(sessionId: number, limit: number = 50) {
  return request.get<ApiResponse<DialogHistoryResponse>>(
    '/operation/dialog/history',
    {
      params: {
        session_id: sessionId,
        limit
      }
    }
  )
}

/**
 * 清除对话历史
 */
export function clearDialogHistory(sessionId: number) {
  return request.delete<ApiResponse<{
    cleared_session_id: number
  }>>(
    '/operation/dialog/history',
    {
      params: {
        session_id: sessionId
      }
    }
  )
}

