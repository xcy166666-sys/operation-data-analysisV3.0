<template>
  <div class="personal-settings">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">个人设置</h1>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 基本信息 -->
      <el-tab-pane label="基本信息" name="basic">
        <el-card class="settings-card">
          <el-form
            ref="basicFormRef"
            :model="basicForm"
            :rules="basicFormRules"
            label-width="100px"
          >
            <el-form-item label="用户名">
              <el-input
                v-model="basicForm.username"
                disabled
                placeholder="用户名不可修改"
              />
            </el-form-item>

            <el-form-item label="姓名" prop="full_name">
              <el-input
                v-model="basicForm.full_name"
                placeholder="请输入姓名"
                clearable
              />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="basicForm.email"
                placeholder="请输入邮箱"
                clearable
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="saving"
                @click="handleSaveBasic"
              >
                保存
              </el-button>
              <el-button @click="handleResetBasic">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 修改密码 -->
      <el-tab-pane label="修改密码" name="password">
        <el-card class="settings-card">
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordFormRules"
            label-width="100px"
          >
            <el-form-item label="当前密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码（至少6位）"
                show-password
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="changingPassword"
                @click="handleChangePassword"
              >
                修改密码
              </el-button>
              <el-button @click="handleResetPassword">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { updateUser } from '@/api/user'
import { changePassword } from '@/api/auth'
import type { User, UserUpdate, ApiResponse } from '@/types'

const authStore = useAuthStore()

const activeTab = ref('basic')
const saving = ref(false)
const changingPassword = ref(false)
const basicFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

const basicForm = reactive({
  username: authStore.user?.username || '',
  full_name: authStore.user?.full_name || '',
  email: authStore.user?.email || ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 验证确认密码
const validateConfirmPassword = (_rule: any, value: any, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const basicFormRules: FormRules = {
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const passwordFormRules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 加载用户信息
onMounted(() => {
  loadUserInfo()
})

const loadUserInfo = () => {
  if (authStore.user) {
    basicForm.username = authStore.user.username || ''
    basicForm.full_name = authStore.user.full_name || ''
    basicForm.email = authStore.user.email || ''
  }
}

// 保存基本信息
const handleSaveBasic = async () => {
  if (!basicFormRef.value) return

  await basicFormRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请检查输入信息')
      return
    }

    if (!authStore.user?.id) {
      ElMessage.error('用户信息不存在')
      return
    }

    saving.value = true
    try {
      const updateData: UserUpdate = {
        full_name: basicForm.full_name || undefined,
        email: basicForm.email || undefined
      }

      const res = await updateUser(authStore.user.id, updateData) as unknown as ApiResponse<User>
      if (res.success && res.data) {
        // 更新store中的用户信息
        const userData = res.data
        authStore.setUser(userData)
        ElMessage.success('保存成功')
      } else {
        const updateErrorResponse = res as unknown as ApiResponse<any>
        ElMessage.error(updateErrorResponse.message || '保存失败')
      }
    } catch (error: any) {
      console.error('保存失败:', error)
      ElMessage.error(error.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

// 重置基本信息
const handleResetBasic = () => {
  loadUserInfo()
  basicFormRef.value?.clearValidate()
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请检查输入信息')
      return
    }

    changingPassword.value = true
    try {
      const res = await changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password
      }) as unknown as ApiResponse<any>
      
      if (res.success) {
        ElMessage.success('密码修改成功，请重新登录')
        handleResetPassword()
        // 延迟跳转到登录页
        setTimeout(() => {
          authStore.logout()
          window.location.href = '/login'
        }, 1500)
      } else {
        const changePasswordErrorResponse = res as unknown as ApiResponse<any>
        ElMessage.error(changePasswordErrorResponse.message || '密码修改失败')
      }
    } catch (error: any) {
      console.error('密码修改失败:', error)
      ElMessage.error(error.response?.data?.detail || '密码修改失败')
    } finally {
      changingPassword.value = false
    }
  })
}

// 重置密码表单
const handleResetPassword = () => {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordFormRef.value?.clearValidate()
}
</script>

<style scoped lang="scss">
.personal-settings {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.page-header {
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;

  .page-title {
    font-size: 24px;
    font-weight: bold;
    color: #303133;
    margin: 0;
  }
}

.settings-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 20px;
  }

  :deep(.el-tabs__item) {
    font-size: 16px;
    padding: 0 20px;
  }
}

.settings-card {
  max-width: 600px;
  margin: 0 auto;
}
</style>

