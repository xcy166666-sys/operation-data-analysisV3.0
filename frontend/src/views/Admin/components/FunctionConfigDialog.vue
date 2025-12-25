<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`配置API - ${functionData?.name || ''}`"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
    >
      <el-form-item label="AI平台" prop="platform">
        <el-select
          v-model="formData.platform"
          placeholder="请选择AI平台"
          style="width: 100%"
          @change="handlePlatformChange"
        >
          <el-option label="Dify" value="dify" />
          <el-option label="Langchain" value="langchain" />
          <el-option label="Ragflow" value="ragflow" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="工作流名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入工作流名称"
        />
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          placeholder="请输入描述（可选）"
        />
      </el-form-item>
      
      <!-- Dify配置 -->
      <template v-if="formData.platform === 'dify'">
        <el-divider content-position="left">Dify配置</el-divider>
        
        <el-form-item label="API地址" prop="config.api_url">
          <el-input
            v-model="formData.config.api_url"
            placeholder="http://118.89.16.95/v1"
          />
        </el-form-item>
        
        <el-form-item label="API Key" prop="config.api_key">
          <el-input
            v-model="formData.config.api_key"
            placeholder="app-xxx"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="文件上传URL" prop="config.url_file">
          <el-input
            v-model="formData.config.url_file"
            placeholder="http://118.89.16.95/v1/files/upload"
          />
        </el-form-item>
        
        <el-form-item label="工作流URL" prop="config.url_work">
          <el-input
            v-model="formData.config.url_work"
            placeholder="http://118.89.16.95/v1/chat-messages"
          />
        </el-form-item>
        
        <el-form-item label="工作流类型" prop="config.workflow_type">
          <el-select
            v-model="formData.config.workflow_type"
            placeholder="请选择工作流类型"
            style="width: 100%"
          >
            <el-option label="Chatflow" value="chatflow" />
            <el-option label="Workflow" value="workflow" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="文件参数名" prop="config.file_param">
          <el-input
            v-model="formData.config.file_param"
            placeholder="excell"
          />
        </el-form-item>
        
        <el-form-item label="查询参数名" prop="config.query_param">
          <el-input
            v-model="formData.config.query_param"
            placeholder="sys.query"
          />
        </el-form-item>
      </template>
      
      <!-- Langchain配置 -->
      <template v-if="formData.platform === 'langchain'">
        <el-divider content-position="left">Langchain配置</el-divider>
        
        <el-form-item label="API地址" prop="config.api_url">
          <el-input
            v-model="formData.config.api_url"
            placeholder="请输入API地址"
          />
        </el-form-item>
        
        <el-form-item label="API Key" prop="config.api_key">
          <el-input
            v-model="formData.config.api_key"
            placeholder="请输入API Key"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="模型名称" prop="config.model_name">
          <el-input
            v-model="formData.config.model_name"
            placeholder="请输入模型名称"
          />
        </el-form-item>
      </template>
      
      <!-- Ragflow配置 -->
      <template v-if="formData.platform === 'ragflow'">
        <el-divider content-position="left">Ragflow配置</el-divider>
        
        <el-form-item label="API地址" prop="config.api_url">
          <el-input
            v-model="formData.config.api_url"
            placeholder="请输入API地址"
          />
        </el-form-item>
        
        <el-form-item label="API Key" prop="config.api_key">
          <el-input
            v-model="formData.config.api_key"
            placeholder="请输入API Key"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="知识库ID" prop="config.knowledge_base_id">
          <el-input
            v-model="formData.config.knowledge_base_id"
            placeholder="请输入知识库ID"
          />
        </el-form-item>
      </template>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleTest">测试连接</el-button>
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
import {
  getFunction,
  setFunctionConfig,
  updateFunctionConfig,
  testFunctionConfig
} from '@/api/admin'
import type { FunctionModule, FunctionConfigRequest } from '@/api/admin'
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
const testing = ref(false)

const formData = reactive<FunctionConfigRequest>({
  platform: 'dify',
  name: '',
  description: '',
  config: {
    api_url: '',
    api_key: '',
    url_file: '',
    url_work: '',
    workflow_type: 'chatflow',
    file_param: 'excell',
    query_param: 'sys.query'
  }
})

const formRules: FormRules = {
  platform: [{ required: true, message: '请选择AI平台', trigger: 'change' }],
  name: [{ required: true, message: '请输入工作流名称', trigger: 'blur' }],
  'config.api_url': [{ required: true, message: '请输入API地址', trigger: 'blur' }],
  'config.api_key': [{ required: true, message: '请输入API Key', trigger: 'blur' }]
}

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
      const workflow = funcData.workflow
      if (workflow) {
        formData.platform = workflow.platform as 'dify' | 'langchain' | 'ragflow'
        formData.name = workflow.name
        formData.description = workflow.description || ''
        formData.config = { ...workflow.config }
      } else {
        // 没有配置，使用默认值
        resetForm()
        formData.name = `${func.name}工作流`
        formData.description = `${func.description || ''}工作流配置`
      }
    }
  } catch (error: any) {
    // 如果获取失败，使用默认值
    resetForm()
    if (func) {
      formData.name = `${func.name}工作流`
      formData.description = `${func.description || ''}工作流配置`
    }
  }
}

// 重置表单
const resetForm = () => {
  formData.platform = 'dify'
  formData.name = ''
  formData.description = ''
  formData.config = {
    api_url: '',
    api_key: '',
    url_file: '',
    url_work: '',
    workflow_type: 'chatflow',
    file_param: 'excell',
    query_param: 'sys.query'
  }
  formRef.value?.clearValidate()
}

// 平台切换
const handlePlatformChange = () => {
  // 切换平台时重置配置
  if (formData.platform === 'dify') {
    formData.config = {
      api_url: '',
      api_key: '',
      url_file: '',
      url_work: '',
      workflow_type: 'chatflow',
      file_param: 'excell',
      query_param: 'sys.query'
    }
  } else if (formData.platform === 'langchain') {
    formData.config = {
      api_url: '',
      api_key: '',
      model_name: ''
    }
  } else if (formData.platform === 'ragflow') {
    formData.config = {
      api_url: '',
      api_key: '',
      knowledge_base_id: ''
    }
  }
}

// 测试连接
const handleTest = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请先填写完整的配置信息')
      return
    }
    
    if (!props.functionData) return
    
    testing.value = true
    try {
      const res = await testFunctionConfig(props.functionData.function_key, formData) as unknown as ApiResponse<any>
      if (res.success && res.data) {
        ElMessage.success(res.data.message || '连接测试成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '连接测试失败')
    } finally {
      testing.value = false
    }
  })
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
      // 检查是否已有配置
      const hasConfig = props.functionData.workflow !== undefined && props.functionData.workflow !== null
      
      if (hasConfig) {
        await updateFunctionConfig(props.functionData.function_key, formData)
      } else {
        await setFunctionConfig(props.functionData.function_key, formData)
      }
      
      ElMessage.success('配置保存成功')
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
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

