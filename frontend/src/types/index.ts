/**
 * 类型定义
 */

export interface User {
  id: number
  username: string
  full_name?: string
  email?: string
  is_superadmin?: boolean
  is_admin?: boolean
  is_active?: boolean
  created_at?: string
  updated_at?: string
  last_login_at?: string
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: {
    code: string
    message: string
    details?: any
  }
}

// 用户管理相关类型
export interface UserListQuery {
  page?: number
  page_size?: number
  search?: string
}

export interface UserCreate {
  username: string
  password: string
  email?: string
  full_name?: string
}

export interface UserUpdate {
  email?: string
  full_name?: string
}

export interface PaginationInfo {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface PaginatedData<T> {
  items: T[]
  pagination: PaginationInfo
}

