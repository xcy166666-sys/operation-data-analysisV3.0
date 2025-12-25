<template>
  <div class="function-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">功能管理</h1>
    </div>

    <!-- 搜索和筛选栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索功能名称或功能键"
        clearable
        style="width: 300px"
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-select
        v-model="statusFilter"
        placeholder="筛选状态"
        clearable
        style="width: 150px"
        @change="handleSearch"
      >
        <el-option label="全部" value="" />
        <el-option label="启用" :value="true" />
        <el-option label="禁用" :value="false" />
      </el-select>
    </div>

    <!-- 功能列表表格 -->
    <div class="table-container">
      <el-table
        v-loading="loading"
        :data="functionList"
        stripe
        style="width: 100%"
        empty-text="暂无功能数据"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="功能名称" width="200" />
        <el-table-column prop="function_key" label="功能键" width="250" />
        <el-table-column prop="route_path" label="路由" width="200">
          <template #default="{ row }">
            {{ row.route_path || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="工作流名称" width="200">
          <template #default="{ row }">
            <template v-if="row.function_key === 'custom_operation_data_analysis'">
              <template v-if="row.workflows && row.workflows.length > 0">
                <el-tag type="info" size="small">
                  已配置{{ row.workflows.length }}个工作流
                </el-tag>
              </template>
              <span v-else class="text-muted">未配置</span>
            </template>
            <template v-else>
              <el-tag v-if="row.workflow" type="success" size="small">
                {{ row.workflow.name }}
              </el-tag>
              <span v-else class="text-muted">未配置</span>
            </template>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              :loading="row.toggling"
              @change="handleToggle(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleConfig(row)"
            >
              配置API
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- API配置对话框 -->
    <FunctionConfigDialog
      v-if="currentFunction && currentFunction.function_key !== 'custom_operation_data_analysis'"
      v-model="configDialogVisible"
      :function-data="currentFunction"
      @saved="handleConfigSaved"
    />
    
    <!-- 定制化批量分析配置对话框 -->
    <CustomBatchConfigDialog
      v-if="currentFunction && currentFunction.function_key === 'custom_operation_data_analysis'"
      v-model="configDialogVisible"
      :function-data="currentFunction"
      @saved="handleConfigSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getFunctions, deleteFunctionConfig, toggleFunction } from '@/api/admin'
import type { FunctionModule } from '@/api/admin'
import type { ApiResponse } from '@/types'
import FunctionConfigDialog from './components/FunctionConfigDialog.vue'
import CustomBatchConfigDialog from './components/CustomBatchConfigDialog.vue'

const loading = ref(false)
const searchKeyword = ref('')
const statusFilter = ref<boolean | ''>('')
const functionList = ref<FunctionModule[]>([])
const configDialogVisible = ref(false)
const currentFunction = ref<FunctionModule | null>(null)

// 加载功能列表
const loadFunctions = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (statusFilter.value !== '') {
      params.is_enabled = statusFilter.value
    }
    
    const res = await getFunctions(params) as unknown as ApiResponse<any>
    if (res.success && res.data) {
      // 为每个功能添加 toggling 状态标记
      const functions = res.data as unknown as FunctionModule[]
      functionList.value = functions.map((func) => ({
        ...func,
        toggling: false
      }))
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取功能列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  loadFunctions()
}

// 配置API
const handleConfig = (row: FunctionModule) => {
  currentFunction.value = row
  configDialogVisible.value = true
}

// 删除配置
const handleDelete = async (row: FunctionModule) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除功能"${row.name}"的API配置吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteFunctionConfig(row.function_key)
    ElMessage.success('删除成功')
    loadFunctions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 配置保存后刷新
const handleConfigSaved = () => {
  loadFunctions()
}

// 切换启用/禁用状态
const handleToggle = async (row: FunctionModule & { toggling?: boolean }) => {
  if (row.toggling) return
  
  row.toggling = true
  const originalValue = !row.is_enabled
  
  try {
    const res = await toggleFunction(row.function_key, { is_enabled: row.is_enabled }) as unknown as ApiResponse<any>
    if (res.success) {
      ElMessage.success(res.message || `功能"${row.name}"已${row.is_enabled ? '启用' : '禁用'}`)
    } else {
      // 恢复原状态
      row.is_enabled = originalValue
      ElMessage.error(res.message || '操作失败')
    }
  } catch (error: any) {
    // 恢复原状态
    row.is_enabled = originalValue
    ElMessage.error(error.response?.data?.detail || error.message || '操作失败')
  } finally {
    row.toggling = false
  }
}

onMounted(() => {
  loadFunctions()
})
</script>

<style scoped lang="scss">
.function-management {
  padding: 20px;
  background-color: #fff;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.table-container {
  background-color: #fff;
  border-radius: 4px;
  overflow: hidden;
}

.text-muted {
  color: #909399;
  font-size: 14px;
}
</style>

