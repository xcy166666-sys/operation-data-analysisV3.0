import request from '@/utils/request'
import type { ApiResponse, User } from '@/types'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  user: User
  token: string
  session_id: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
  full_name?: string
}

/**
 * 登录
 */
export function login(data: LoginRequest) {
  return request.post<ApiResponse<LoginResponse>>('/auth/login', data)
}

/**
 * 登出
 */
export function logout() {
  return request.post('/auth/logout')
}

/**
 * 注册
 */
export function register(data: RegisterRequest) {
  return request.post<ApiResponse<LoginResponse>>('/auth/register', data)
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser() {
  return request.get<ApiResponse<User>>('/auth/me')
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/**
 * 修改密码
 */
export function changePassword(data: ChangePasswordRequest) {
  return request.put<ApiResponse>('/auth/change-password', data)
}

