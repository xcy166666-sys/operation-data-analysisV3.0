import request from '@/utils/request'

/**
 * 获取工作流列表（简化版，移除project_id参数）
 */
export function getWorkflows(params?: { 
  category?: string
  platform?: string
  is_active?: boolean
}) {
  return request.get('/workflows', { params })
}

/**
 * 获取工作流详情
 */
export function getWorkflow(workflowId: number) {
  return request.get(`/workflows/${workflowId}`)
}

/**
 * 创建工作流（简化版，移除project_id参数）
 */
export function createWorkflow(data: any) {
  return request.post('/workflows', data)
}

/**
 * 更新工作流
 */
export function updateWorkflow(workflowId: number, data: any) {
  return request.put(`/workflows/${workflowId}`, data)
}

/**
 * 删除工作流
 */
export function deleteWorkflow(workflowId: number) {
  return request.delete(`/workflows/${workflowId}`)
}

/**
 * 绑定功能到工作流（简化版，移除project_id参数）
 */
export function bindFunctionWorkflow(data: { function_key: string, workflow_id: number }) {
  return request.post('/workflows/functions/bind', data)
}

/**
 * 获取功能绑定的工作流（简化版，移除project_id参数）
 * @param functionKey 功能键
 * @param silent 是否静默处理错误（不显示404错误提示）
 */
export function getFunctionWorkflow(functionKey: string, silent: boolean = false) {
  return request.get(`/workflows/functions/${functionKey}`, {
    silentError: silent
  } as any)
}

/**
 * 获取所有功能工作流绑定（简化版，移除project_id参数）
 * @param silent 是否静默处理错误
 */
export function getAllFunctionWorkflows(silent: boolean = false) {
  return request.get('/workflows/functions', {
    silentError: silent
  } as any)
}

/**
 * 获取对话列表（简化版，移除project_id参数）
 * @param params 查询参数
 * @param silent 是否静默处理错误
 */
export function getConversations(params?: { 
  function_key?: string
}, silent: boolean = false) {
  return request.get('/workflows/conversations', { 
    params,
    silentError: silent
  } as any)
}

/**
 * 获取对话详情
 */
export function getConversation(conversationId: number) {
  return request.get(`/workflows/conversations/${conversationId}`)
}

/**
 * 创建对话（简化版，移除project_id参数）
 */
export function createConversation(data: {
  function_key: string
  workflow_id?: number
  title?: string
  messages?: Array<{ role: string, content: string }>
}) {
  return request.post('/workflows/conversations', data)
}

/**
 * 更新对话
 */
export function updateConversation(conversationId: number, data: {
  title?: string
  messages?: Array<{ role: string, content: string }>
}) {
  return request.put(`/workflows/conversations/${conversationId}`, data)
}

/**
 * 删除对话
 */
export function deleteConversation(conversationId: number) {
  return request.delete(`/workflows/conversations/${conversationId}`)
}

/**
 * 执行工作流（简化版，移除project_id参数）
 */
export function executeWorkflow(data: {
  workflow_id: number
  function_key: string
  input: string
  extra_inputs?: Record<string, any>
  conversation_id?: number
}) {
  return request.post('/workflows/execute', data)
}

/**
 * 流式执行工作流（简化版，移除project_id参数）
 */
export function executeWorkflowStream(data: {
  workflow_id: number
  function_key: string
  input: string
  extra_inputs?: Record<string, any>
  conversation_id?: number
}) {
  return request.post('/workflows/execute-stream', data, {
    responseType: 'stream'
  })
}

