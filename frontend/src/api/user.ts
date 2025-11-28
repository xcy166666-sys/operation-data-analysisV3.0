import request from '@/utils/request'
import type { ApiResponse, User, UserListQuery, UserCreate, UserUpdate, PaginatedData } from '@/types'

/**
 * 获取用户列表
 */
export function getUserList(params: UserListQuery) {
  return request.get<ApiResponse<PaginatedData<User>>>('/users', { params })
}

/**
 * 创建用户
 */
export function createUser(data: UserCreate) {
  return request.post<ApiResponse<User>>('/users', data)
}

/**
 * 更新用户
 */
export function updateUser(userId: number, data: UserUpdate) {
  return request.put<ApiResponse<User>>(`/users/${userId}`, data)
}

/**
 * 删除用户
 */
export function deleteUser(userId: number) {
  return request.delete<ApiResponse>(`/users/${userId}`)
}

