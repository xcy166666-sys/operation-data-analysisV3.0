import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  
  const isLoggedIn = computed(() => !!token.value)
  const isSuperadmin = computed(() => {
    if (!user.value) return false
    // 检查 is_superadmin 或 is_admin 字段，确保是 true 才返回 true
    return !!(user.value.is_superadmin || user.value.is_admin)
  })
  
  function setAuth(userData: User, tokenValue: string) {
    user.value = userData
    token.value = tokenValue
    localStorage.setItem('token', tokenValue)
    localStorage.setItem('user', JSON.stringify(userData))
  }
  
  function clearAuth() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
  
  function loadAuth() {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    
    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
    }
  }
  
  return {
    user,
    token,
    isLoggedIn,
    isSuperadmin,
    setAuth,
    clearAuth,
    loadAuth
  }
})

