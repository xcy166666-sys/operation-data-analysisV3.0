<template>
  <div class="login-container">
    <div class="login-content">
      <div class="login-header">
        <h1 class="title">运营数据分析系统</h1>
        <p class="subtitle">{{ isAdminLogin ? '使用管理员账号登录' : '登录您的账户' }}</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            size="large"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          @click="handleLogin"
          style="width: 100%"
        >
          {{ loading ? '登录中...' : '登录' }}
        </el-button>
      </el-form>
      
      <div class="login-switch">
        <el-button
          v-if="!isAdminLogin"
          type="text"
          @click="switchToAdmin"
          style="width: 100%; color: var(--el-color-primary)"
        >
          <el-icon><User /></el-icon>
          切换到管理员登录
        </el-button>
        <el-button
          v-else
          type="text"
          @click="switchToNormal"
          style="width: 100%"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回普通登录
        </el-button>
      </div>
      
      <!-- 注册按钮（仅普通登录模式显示） -->
      <div class="register-section" v-if="!isAdminLogin">
        <el-button
          type="text"
          @click="showRegisterDialog = true"
          style="width: 100%; color: var(--el-color-primary)"
        >
          还没有账号？立即注册
        </el-button>
      </div>
      
      <div class="login-tips" v-if="isAdminLogin">
        <p>管理员账号: <code>admin7</code> / <code>admin123456</code></p>
      </div>
    </div>

    <!-- 注册对话框 -->
    <el-dialog
      v-model="showRegisterDialog"
      title="注册新用户"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名（3-50个字符）"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱（可选）"
          />
        </el-form-item>
        
        <el-form-item label="全名" prop="full_name">
          <el-input
            v-model="registerForm.full_name"
            placeholder="请输入全名（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showRegisterDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="registerLoading"
          @click="handleRegister"
        >
          注册
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, ArrowLeft } from '@element-plus/icons-vue'
import { login, register } from '@/api/auth'
import { useAuthStore } from '@/store/auth'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const registerLoading = ref(false)
const loginFormRef = ref()
const registerFormRef = ref<FormInstance>()
const showRegisterDialog = ref(false)

// 判断是否为管理员登录模式
const isAdminLogin = computed(() => {
  return route.query.admin === 'true'
})

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  full_name: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 验证确认密码
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3到50个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid: boolean) => {
    if (!valid) {
      ElMessage.warning('请检查输入信息')
      return
    }
    
    loading.value = true
    
    try {
      const res = await login(loginForm)
      
      if (res.success && res.data) {
        // 如果是管理员登录模式，只允许 admin7 登录
        if (isAdminLogin.value) {
          if (res.data.user.username !== 'admin7') {
            ElMessage.error('管理员登录界面仅允许 admin7 账号登录')
            loading.value = false
            return
          }
          if (!res.data.user.is_superadmin && !res.data.user.is_admin) {
            ElMessage.error('该账号不是管理员账号')
            loading.value = false
            return
          }
        }
        
        authStore.setAuth(res.data.user, res.data.token)
        ElMessage.success('登录成功')
        
        // 如果是管理员登录，跳转到用户管理页面
        if (isAdminLogin.value && (res.data.user.is_superadmin || res.data.user.is_admin)) {
          router.push({ name: 'admin-users' })
        } else {
          // 普通用户登录，跳转到首页或指定页面
          const redirect = route.query.redirect as string
          router.push(redirect || '/')
        }
      } else {
        ElMessage.error(res.message || '登录失败')
      }
    } catch (error: any) {
      console.error('登录失败:', error)
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else if (!error.response) {
        ElMessage.error('网络错误，请检查后端服务是否正常运行')
      } else {
        ElMessage.error('登录失败')
      }
    } finally {
      loading.value = false
    }
  })
}

const switchToAdmin = () => {
  router.push({ name: 'login', query: { admin: 'true' } })
}

const switchToNormal = () => {
  router.push({ name: 'login' })
}

// 注册处理
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid: boolean) => {
    if (!valid) {
      ElMessage.warning('请检查输入信息')
      return
    }
    
    registerLoading.value = true
    
    try {
      const res = await register({
        username: registerForm.username,
        password: registerForm.password,
        email: registerForm.email || undefined,
        full_name: registerForm.full_name || undefined
      })
      
      if (res.success && res.data) {
        authStore.setAuth(res.data.user, res.data.token)
        ElMessage.success('注册成功，已自动登录')
        showRegisterDialog.value = false
        
        // 跳转到首页
        router.push({ name: 'home' })
      } else {
        ElMessage.error(res.message || '注册失败')
      }
    } catch (error: any) {
      console.error('注册失败:', error)
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else if (!error.response) {
        ElMessage.error('网络错误，请检查后端服务是否正常运行')
      } else {
        ElMessage.error('注册失败')
      }
    } finally {
      registerLoading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--apple-bg-gradient);
  padding: var(--apple-space-xl);
}

.login-content {
  width: 100%;
  max-width: 420px;
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-xl);
  padding: var(--apple-space-4xl);
  box-shadow: var(--apple-shadow-lg);
  border: 1px solid var(--apple-border-light);
}

.login-header {
  text-align: center;
  margin-bottom: var(--apple-space-3xl);
}

.title {
  font-size: var(--apple-font-2xl);
  font-weight: 600;
  margin-bottom: var(--apple-space-sm);
  color: var(--apple-text-primary);
  letter-spacing: -0.3px;
}

.subtitle {
  font-size: var(--apple-font-sm);
  color: var(--apple-text-secondary);
  margin: 0;
}

.login-form {
  margin-bottom: var(--apple-space-xl);
}

.login-switch {
  text-align: center;
  margin-bottom: var(--apple-space-lg);
}

.login-tips {
  text-align: center;
  font-size: var(--apple-font-sm);
  color: var(--apple-text-tertiary);
}

.login-tips code {
  background: var(--apple-bg-secondary);
  padding: 2px var(--apple-space-sm);
  border-radius: var(--apple-radius-sm);
  font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
  border: 1px solid var(--apple-border-light);
}

.register-section {
  text-align: center;
  margin-bottom: var(--apple-space-lg);
}
</style>

