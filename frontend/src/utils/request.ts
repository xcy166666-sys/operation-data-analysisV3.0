import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import router from '@/router'

// 创建axios实例
const service: AxiosInstance = axios.create({
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

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return response
    }
    
    const res = response.data
    
    if (res.success) {
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
        authStore.clearAuth()
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      } else if (status === 403) {
        ElMessage.error('没有权限执行此操作')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (status >= 500) {
        ElMessage.error('服务器错误，请稍后重试')
      } else {
        const message = error.response.data?.error?.message || error.response.data?.message || '请求失败'
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

export default service

