import axios, { type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import router from '@/router'
import type { ApiResponse } from '@/types'

// 创建axios实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 300000, // 5分钟超时
  withCredentials: true,
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 - 返回 ApiResponse<T> 而不是 AxiosResponse
service.interceptors.response.use(
  (response: AxiosResponse<ApiResponse<any>>): any => {
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return response
    }
    
    const res = response.data
    
    if (res.success) {
      // 直接返回 ApiResponse，而不是包装在 AxiosResponse 中
      return res
    }
    
    const errorMessage = res.error?.message || res.message || '操作失败'
    ElMessage.error(errorMessage)
    return Promise.reject(new Error(errorMessage))
  },
  (error) => {
    console.error('响应错误:', error)
    
    if (error.response) {
      const status = error.response.status
      
      if (status === 401) {
        const authStore = useAuthStore()
        // 只有在已登录状态下才清除认证信息
        if (authStore.token) {
          authStore.clearAuth()
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
        } else {
          // 登录失败的情况，显示具体错误信息
          const message = error.response.data?.detail || error.response.data?.error?.message || error.response.data?.message || '用户名或密码错误'
          ElMessage.error(message)
        }
      } else if (status === 403) {
        ElMessage.error('没有权限执行此操作')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (status >= 500) {
        ElMessage.error('服务器错误，请稍后重试')
      } else {
        const message = error.response.data?.error?.message || error.response.data?.detail || error.response.data?.message || '请求失败'
        ElMessage.error(message)
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查后端服务是否正常运行')
    } else {
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

// 创建包装函数，确保返回类型正确
const requestWrapper = {
  get: <T = any>(url: string, config?: any): Promise<ApiResponse<T> | AxiosResponse> => {
    const result = service.get(url, config) as any
    // 如果是 Blob 响应，返回原始响应
    if (config?.responseType === 'blob' || config?.responseType === 'arraybuffer') {
      return result as Promise<AxiosResponse>
    }
    return result as Promise<ApiResponse<T>>
  },
  post: <T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T> | AxiosResponse> => {
    const result = service.post(url, data, config) as any
    // 如果是 Blob 响应，返回原始响应
    if (config?.responseType === 'blob' || config?.responseType === 'arraybuffer') {
      return result as Promise<AxiosResponse>
    }
    return result as Promise<ApiResponse<T>>
  },
  put: <T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T> | AxiosResponse> => {
    const result = service.put(url, data, config) as any
    // 如果是 Blob 响应，返回原始响应
    if (config?.responseType === 'blob' || config?.responseType === 'arraybuffer') {
      return result as Promise<AxiosResponse>
    }
    return result as Promise<ApiResponse<T>>
  },
  patch: <T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T> | AxiosResponse> => {
    const result = service.patch(url, data, config) as any
    // 如果是 Blob 响应，返回原始响应
    if (config?.responseType === 'blob' || config?.responseType === 'arraybuffer') {
      return result as Promise<AxiosResponse>
    }
    return result as Promise<ApiResponse<T>>
  },
  delete: <T = any>(url: string, config?: any): Promise<ApiResponse<T> | AxiosResponse> => {
    const result = service.delete(url, config) as any
    // 如果是 Blob 响应，返回原始响应
    if (config?.responseType === 'blob' || config?.responseType === 'arraybuffer') {
      return result as Promise<AxiosResponse>
    }
    return result as Promise<ApiResponse<T>>
  }
}

export default requestWrapper

