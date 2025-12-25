import request from '@/utils/request'
import type { ApiResponse } from '@/types'

/**
 * 功能模块类型
 */
export interface FunctionModule {
  id: number
  function_key: string
  name: string
  description?: string
  route_path?: string
  icon?: string
  category: string
  is_enabled: boolean
  sort_order: number
  created_at: string
  updated_at: string
  workflow?: Workflow
  workflows?: Array<{ sheet_index: number; workflow: Workflow }>  // 用于定制化批量分析
}

export interface Workflow {
  id: number
  name: string
  category: string
  platform: string
  config: Record<string, any>
  description?: string
  is_active: boolean
  created_by?: number
  created_at: string
  updated_at: string
}

/**
 * 功能配置请求
 */
export interface FunctionConfigRequest {
  platform: 'dify' | 'langchain' | 'ragflow'
  name: string
  description?: string
  config: Record<string, any>
}

/**
 * 功能切换请求
 */
export interface FunctionToggleRequest {
  is_enabled: boolean
}

/**
 * 定制化批量分析工作流配置
 */
export interface CustomBatchWorkflowConfig {
  sheet_index: number
  platform: 'dify' | 'langchain' | 'ragflow'
  name: string
  description?: string
  config: Record<string, any>
}

/**
 * 定制化批量分析配置请求
 */
export interface CustomBatchConfigRequest {
  workflows: CustomBatchWorkflowConfig[]
}

/**
 * 获取功能列表
 */
export function getFunctions(params?: { search?: string; is_enabled?: boolean }) {
  return request.get<ApiResponse<FunctionModule[]>>('/admin/functions', { params })
}

/**
 * 获取单个功能的配置
 */
export function getFunction(functionKey: string) {
  return request.get<ApiResponse<FunctionModule>>(`/admin/functions/${functionKey}`)
}

/**
 * 配置功能的API（全局配置）
 */
export function setFunctionConfig(functionKey: string, data: FunctionConfigRequest) {
  return request.post<ApiResponse<{ workflow_id: number; function_key: string }>>(
    `/admin/functions/${functionKey}/config`,
    data
  )
}

/**
 * 更新功能的API配置
 */
export function updateFunctionConfig(functionKey: string, data: FunctionConfigRequest) {
  return request.put<ApiResponse<{ workflow_id: number; function_key: string }>>(
    `/admin/functions/${functionKey}/config`,
    data
  )
}

/**
 * 测试API配置
 */
export function testFunctionConfig(functionKey: string, data: FunctionConfigRequest) {
  return request.post<ApiResponse<{ connected: boolean; message: string }>>(
    `/admin/functions/${functionKey}/test-config`,
    data
  )
}

/**
 * 删除功能的API配置
 */
export function deleteFunctionConfig(functionKey: string) {
  return request.delete<ApiResponse<{ function_key: string }>>(
    `/admin/functions/${functionKey}/config`
  )
}

/**
 * 启用/禁用功能
 */
export function toggleFunction(functionKey: string, data: FunctionToggleRequest) {
  return request.patch<ApiResponse<{ function_key: string; is_enabled: boolean }>>(
    `/admin/functions/${functionKey}/toggle`,
    data
  )
}

/**
 * 配置定制化批量分析的6个工作流
 */
export function setCustomBatchConfig(functionKey: string, data: CustomBatchConfigRequest) {
  return request.post<ApiResponse<{ function_key: string; workflow_ids: number[]; workflow_count: number }>>(
    `/admin/functions/${functionKey}/config-batch`,
    data
  )
}

