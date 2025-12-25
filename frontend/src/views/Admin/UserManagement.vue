<template>
  <div class="user-management-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
    </div>

    <!-- 搜索和操作栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名、邮箱或全名"
        clearable
        style="width: 300px"
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-button
        type="primary"
        :icon="Plus"
        @click="handleCreate"
      >
        创建用户
      </el-button>
    </div>

    <!-- 用户列表表格 -->
    <div class="table-container">
      <el-table
        v-loading="loading"
        :data="userList"
        stripe
        style="width: 100%"
        empty-text="暂无用户数据"
      >
        <el-table-column label="ID" width="80">
          <template #default="{ $index }">
            {{ (pagination.page - 1) * pagination.page_size + $index + 1 }}
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_admin" type="danger" size="small">
              超级管理员
            </el-tag>
            <el-tag v-else type="info" size="small">
              普通用户
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" width="200">
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="full_name" label="全名" width="150">
          <template #default="{ row }">
            {{ row.full_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              :disabled="row.id === currentUserId || row.is_admin"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            :disabled="isEdit"
            placeholder="请输入用户名"
          />
        </el-form-item>
        
        <el-form-item
          v-if="!isEdit"
          label="密码"
          prop="password"
        >
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="formData.email"
            placeholder="请输入邮箱（可选）"
          />
        </el-form-item>
        
        <el-form-item label="全名" prop="full_name">
          <el-input
            v-model="formData.full_name"
            placeholder="请输入全名（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getUserList, createUser, updateUser, deleteUser } from '@/api/user'
import { useAuthStore } from '@/store/auth'
import type { User, UserCreate, UserUpdate, ApiResponse } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

const authStore = useAuthStore()

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const searchKeyword = ref('')
const userList = ref<User[]>([])
const currentUserId = computed(() => authStore.user?.id || 0)

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

const isEdit = ref(false)
const editingUserId = ref<number | null>(null)

const formData = reactive({
  username: '',
  password: '',
  email: '',
  full_name: ''
})

const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3到50个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => {
  return isEdit.value ? '编辑用户' : '创建用户'
})

// 格式化日期时间
const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 加载用户列表
const loadUserList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      search: searchKeyword.value || undefined
    }
    const res = await getUserList(params) as unknown as ApiResponse<any>
    
    if (res.success && res.data) {
      const userData = res.data
      userList.value = userData.items
      pagination.total = userData.pagination.total
      pagination.total_pages = userData.pagination.total_pages
    } else {
      const listErrorResponse = res as unknown as ApiResponse<any>
      ElMessage.error(listErrorResponse.message || '获取用户列表失败')
    }
  } catch (error: any) {
    console.error('获取用户列表失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理（防抖）
let searchTimer: NodeJS.Timeout | null = null
const handleSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    pagination.page = 1
    loadUserList()
  }, 500)
}

// 分页处理
const handleSizeChange = () => {
  pagination.page = 1
  loadUserList()
}

const handlePageChange = () => {
  loadUserList()
}

// 创建用户
const handleCreate = () => {
  isEdit.value = false
  editingUserId.value = null
  formData.username = ''
  formData.password = ''
  formData.email = ''
  formData.full_name = ''
  dialogVisible.value = true
}

// 编辑用户
const handleEdit = (user: User) => {
  isEdit.value = true
  editingUserId.value = user.id
  formData.username = user.username
  formData.password = ''
  formData.email = user.email || ''
  formData.full_name = user.full_name || ''
  dialogVisible.value = true
}

// 删除用户
const handleDelete = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复，将同时删除该用户的所有数据。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await deleteUser(user.id) as unknown as ApiResponse<any>
    if (res.success) {
      ElMessage.success('删除用户成功')
      loadUserList()
    } else {
        const deleteErrorResponse = res as unknown as ApiResponse<any>
        ElMessage.error(deleteErrorResponse.message || '删除用户失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除用户失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) {
      ElMessage.warning('请检查输入信息')
      return
    }
    
    submitting.value = true
    
    try {
      if (isEdit.value) {
        // 更新用户
        const updateData: UserUpdate = {
          email: formData.email || undefined,
          full_name: formData.full_name || undefined
        }
        const res = await updateUser(editingUserId.value!, updateData) as unknown as ApiResponse<any>
        if (res.success) {
          ElMessage.success('更新用户成功')
          dialogVisible.value = false
          loadUserList()
        } else {
          const updateErrorResponse = res as unknown as ApiResponse<any>
          ElMessage.error(updateErrorResponse.message || '更新用户失败')
        }
      } else {
        // 创建用户
        const createData: UserCreate = {
          username: formData.username,
          password: formData.password,
          email: formData.email || undefined,
          full_name: formData.full_name || undefined
        }
        const res = await createUser(createData) as unknown as ApiResponse<any>
        if (res.success) {
          ElMessage.success('创建用户成功')
          dialogVisible.value = false
          loadUserList()
        } else {
          const createErrorResponse = res as unknown as ApiResponse<any>
          ElMessage.error(createErrorResponse.message || '创建用户失败')
        }
      }
    } catch (error: any) {
      console.error('操作失败:', error)
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 初始化
onMounted(() => {
  loadUserList()
})
</script>

<style scoped>
.user-management-container {
  padding: var(--apple-space-xl);
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--apple-space-xl);
}

.page-title {
  font-size: var(--apple-font-2xl);
  font-weight: 600;
  color: var(--apple-text-primary);
  margin: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--apple-space-lg);
}

.table-container {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  padding: var(--apple-space-lg);
  box-shadow: var(--apple-shadow-sm);
  border: 1px solid var(--apple-border-light);
}

.pagination-container {
  margin-top: var(--apple-space-lg);
  display: flex;
  justify-content: flex-end;
}
</style>

