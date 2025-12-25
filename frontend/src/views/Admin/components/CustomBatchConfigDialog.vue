<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`配置API - ${functionData?.name || ''}`"
    width="900px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="custom-batch-config">
      <el-alert
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <template #default>
          <div>
            <p style="margin: 0 0 8px 0; font-weight: 600;">定制化批量分析需要配置6个工作流：</p>
            <ul style="margin: 0; padding-left: 20px;">
              <li>Sheet 0: 最后操作分布</li>
              <li>Sheet 1: 新手漏斗</li>
              <li>Sheet 2: 回流用户</li>
              <li>Sheet 3: 流失用户属性</li>
              <li>Sheet 4: 留存率</li>
              <li>Sheet 5: LTV</li>
            </ul>
          </div>
        </template>
      </el-alert>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <div
          v-for="(workflow, index) in formData.workflows"
          :key="index"
          class="workflow-config-item"
        >
          <el-card shadow="hover" style="margin-bottom: 20px">
            <template #header>
              <div class="workflow-header">
                <span class="workflow-title">Sheet {{ workflow.sheet_index }} - {{ getSheetName(workflow.sheet_index) }}</span>
              </div>
            </template>

            <el-form-item
              :label="`AI平台`"
              :prop="`workflows.${index}.platform`"
              :rules="{ required: true, message: '请选择AI平台', trigger: 'change' }"
            >
              <el-select
                v-model="workflow.platform"
                placeholder="请选择AI平台"
                style="width: 100%"
                @change="handlePlatformChange(index)"
              >
                <el-option label="Dify" value="dify" />
                <el-option label="Langchain" value="langchain" />
                <el-option label="Ragflow" value="ragflow" />
              </el-select>
            </el-form-item>

            <el-form-item
              :label="`工作流名称`"
              :prop="`workflows.${index}.name`"
              :rules="{ required: true, message: '请输入工作流名称', trigger: 'blur' }"
            >
              <el-input
                v-model="workflow.name"
                :placeholder="`${getSheetName(workflow.sheet_index)}工作流`"
              />
            </el-form-item>

            <el-form-item :label="`描述`" :prop="`workflows.${index}.description`">
              <el-input
                v-model="workflow.description"
                type="textarea"
                :rows="2"
                placeholder="请输入描述（可选）"
              />
            </el-form-item>

            <!-- Dify配置 -->
            <template v-if="workflow.platform === 'dify'">
              <el-divider content-position="left">Dify配置</el-divider>

              <el-form-item
                :label="`API地址`"
                :prop="`workflows.${index}.config.api_url`"
                :rules="{ required: true, message: '请输入API地址', trigger: 'blur' }"
              >
                <el-input
                  v-model="workflow.config.api_url"
                  placeholder="http://118.89.16.95/v1"
                />
              </el-form-item>

              <el-form-item
                :label="`API Key`"
                :prop="`workflows.${index}.config.api_key`"
                :rules="{ required: true, message: '请输入API Key', trigger: 'blur' }"
              >
                <el-input
                  v-model="workflow.config.api_key"
                  placeholder="app-xxx"
                  show-password
                />
              </el-form-item>

              <el-form-item
                :label="`文件上传URL`"
                :prop="`workflows.${index}.config.url_file`"
              >
                <el-input
                  v-model="workflow.config.url_file"
                  placeholder="http://118.89.16.95/v1/files/upload"
                />
              </el-form-item>

              <el-form-item
                :label="`工作流URL`"
                :prop="`workflows.${index}.config.url_work`"
              >
                <el-input
                  v-model="workflow.config.url_work"
                  placeholder="http://118.89.16.95/v1/chat-messages"
                />
              </el-form-item>

              <el-form-item
                :label="`工作流类型`"
                :prop="`workflows.${index}.config.workflow_type`"
              >
                <el-select
                  v-model="workflow.config.workflow_type"
                  placeholder="请选择工作流类型"
                  style="width: 100%"
                >
                  <el-option label="Chatflow" value="chatflow" />
                  <el-option label="Workflow" value="workflow" />
                </el-select>
              </el-form-item>

              <el-form-item
                :label="`文件参数名`"
                :prop="`workflows.${index}.config.file_param`"
              >
                <el-input
                  v-model="workflow.config.file_param"
                  placeholder="excell"
                />
              </el-form-item>

              <el-form-item
                :label="`查询参数名`"
                :prop="`workflows.${index}.config.query_param`"
              >
                <el-input
                  v-model="workflow.config.query_param"
                  placeholder="sys.query"
                />
              </el-form-item>
            </template>
          </el-card>
        </div>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          保存配置
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getFunction, setCustomBatchConfig } from '@/api/admin'
import type { FunctionModule, CustomBatchWorkflowConfig } from '@/api/admin'
import type { ApiResponse } from '@/types'

const props = defineProps<{
  modelValue: boolean
  functionData: FunctionModule | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': []
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formRef = ref<FormInstance>()
const submitting = ref(false)

// Sheet名称映射
const sheetNames = [
  '最后操作分布',
  '新手漏斗',
  '回流用户',
  '流失用户属性',
  '留存率',
  'LTV'
]

const getSheetName = (index: number) => {
  return sheetNames[index] || `Sheet ${index}`
}

// 初始化6个工作流配置
const initWorkflows = (): CustomBatchWorkflowConfig[] => {
  return [0, 1, 2, 3, 4, 5].map((index) => ({
    sheet_index: index,
    platform: 'dify' as const,
    name: `${getSheetName(index)}工作流`,
    description: `${getSheetName(index)}分析工作流配置`,
    config: {
      api_url: '',
      api_key: '',
      url_file: '',
      url_work: '',
      workflow_type: 'chatflow',
      file_param: 'excell',
      query_param: 'sys.query'
    }
  }))
}

const formData = reactive<{ workflows: CustomBatchWorkflowConfig[] }>({
  workflows: initWorkflows()
})

const formRules: FormRules = {}

// 监听functionData变化，加载现有配置
watch(() => props.functionData, async (newData) => {
  if (newData && dialogVisible.value) {
    await loadFunctionConfig(newData)
  }
}, { immediate: true })

// 加载功能配置
const loadFunctionConfig = async (func: FunctionModule) => {
  try {
    const res = await getFunction(func.function_key) as unknown as ApiResponse<any>
    if (res.success && res.data) {
      const funcData = res.data as unknown as FunctionModule
      const workflows = funcData.workflows || []
      
      if (workflows.length > 0) {
        // 加载已有配置
        workflows.forEach((item: any) => {
          const index = item.sheet_index
          if (index >= 0 && index < 6) {
            const workflow = item.workflow
            if (workflow) {
              formData.workflows[index].platform = workflow.platform as 'dify' | 'langchain' | 'ragflow'
              formData.workflows[index].name = workflow.name
              formData.workflows[index].description = workflow.description || ''
              formData.workflows[index].config = { ...workflow.config }
            }
          }
        })
      } else {
        // 没有配置，使用默认值
        resetForm()
      }
    }
  } catch (error: any) {
    // 如果获取失败，使用默认值
    resetForm()
  }
}

// 重置表单
const resetForm = () => {
  formData.workflows = initWorkflows()
  formRef.value?.clearValidate()
}

// 平台切换
const handlePlatformChange = (index: number) => {
  const workflow = formData.workflows[index]
  if (workflow.platform === 'dify') {
    workflow.config = {
      api_url: '',
      api_key: '',
      url_file: '',
      url_work: '',
      workflow_type: 'chatflow',
      file_param: 'excell',
      query_param: 'sys.query'
    }
  } else if (workflow.platform === 'langchain') {
    workflow.config = {
      api_url: '',
      api_key: '',
      model_name: ''
    }
  } else if (workflow.platform === 'ragflow') {
    workflow.config = {
      api_url: '',
      api_key: '',
      knowledge_base_id: ''
    }
  }
}

// 提交配置
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请检查输入信息')
      return
    }

    if (!props.functionData) return

    submitting.value = true
    try {
      await setCustomBatchConfig(props.functionData.function_key, {
        workflows: formData.workflows
      })

      ElMessage.success('6个工作流配置保存成功')
      emit('saved')
      handleClose()
    } catch (error: any) {
      ElMessage.error(error.message || '保存配置失败')
    } finally {
      submitting.value = false
    }
  })
}

// 关闭对话框
const handleClose = () => {
  dialogVisible.value = false
  resetForm()
}
</script>

<style scoped lang="scss">
.custom-batch-config {
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 10px;
}

.workflow-config-item {
  margin-bottom: 20px;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.workflow-title {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

