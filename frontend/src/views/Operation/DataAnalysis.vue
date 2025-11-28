<template>
  <div class="data-analysis-page">
    <!-- 左侧历史会话栏（仅在非嵌入模式下显示） -->
    <HistorySidebar
      v-if="viewMode !== 'embed'"
      @session-selected="handleSessionSelected"
      @session-created="handleSessionCreated"
      ref="sidebarRef"
    />

    <!-- 右侧主内容区 -->
    <div class="main-content">
      <!-- 顶部：标题和操作按钮 -->
      <div class="content-header">
        <div class="header-text">
          <h1>游戏运营数据分析助手</h1>
          <p>上传Excel数据，输入需求即可生成包含图表的运营报告</p>
        </div>
        <div class="header-actions">
          <el-button 
            :icon="ArrowLeft"
            @click="goToHome"
          >
            返回首页
          </el-button>
          <el-button 
            type="primary"
            :icon="DataAnalysis"
            @click="goToBatchAnalysis"
          >
            批量分析
          </el-button>
          <el-button 
            type="primary"
            :icon="DataAnalysis"
            @click="goToCustomBatchAnalysis"
          >
            定制化批量分析
          </el-button>
          <el-button 
            :icon="Setting"
            circle
            @click="openSettings"
            title="配置工作流"
          />
        </div>
      </div>

      <!-- 工作流状态提示 -->
      <div class="workflow-status-bar" v-if="!currentWorkflow">
        <el-alert
          title="未配置工作流，请联系管理员"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>
      <div class="workflow-status-bar" v-else>
        <el-tag size="small" type="success">
          <el-icon><Check /></el-icon>
          工作流: {{ currentWorkflow.name }}
        </el-tag>
      </div>

      <!-- 模式切换：上传分析 vs Dify嵌入 -->
      <div class="mode-switch" v-if="currentWorkflow && difyEmbedUrl">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button value="upload">上传分析</el-radio-button>
          <el-radio-button value="embed">Dify嵌入</el-radio-button>
        </el-radio-group>
        <el-alert
          v-if="viewMode === 'embed'"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 12px;"
        >
          <template #title>
            <span style="font-size: 12px;">提示：Dify嵌入模式下，历史对话由Dify内部管理，左侧会话栏已隐藏</span>
          </template>
        </el-alert>
      </div>

      <!-- Dify嵌入模式 -->
      <div v-if="viewMode === 'embed' && difyEmbedUrl" class="dify-embed-container">
        <iframe
          :src="difyEmbedUrl"
          style="width: 100%; height: 100%; min-height: 700px; border: none;"
          frameborder="0"
          allow="microphone"
        ></iframe>
      </div>

      <!-- 上传分析模式 -->
      <template v-if="viewMode === 'upload' || !difyEmbedUrl">
      <!-- Excel上传区 -->
      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          class="excel-uploader"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :on-error="handleUploadError"
          accept=".xlsx,.csv"
          :limit="1"
          :file-list="fileList"
          :show-file-list="true"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p>拖拽Excel至此处，或点击上传</p>
            <p class="upload-hint">支持.xlsx/.csv，文件大小不超过10MB</p>
          </div>
          <template #tip>
            <div class="upload-tip">
              <el-button 
                type="primary" 
                :icon="Folder"
                @click.stop="triggerFileSelect"
              >
                选择本地文件
              </el-button>
            </div>
          </template>
        </el-upload>
        <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
          <el-progress :percentage="uploadProgress" />
        </div>
      </div>

      <!-- 分析需求输入区 -->
      <div class="input-section">
        <div class="input-header">
          <h3>输入分析需求</h3>
        </div>
        <el-input
          v-model="analysisRequest"
          type="textarea"
          :rows="6"
          placeholder="例如：生成一份关注新手留存的周度报告"
          :maxlength="1000"
          show-word-limit
        />
        <div class="input-examples">
          <el-tag 
            v-for="example in examples" 
            :key="example"
            class="example-tag"
            @click="useExample(example)"
          >
            例: {{ example }}
          </el-tag>
        </div>
        <div class="submit-section">
          <el-button 
            type="primary" 
            size="large"
            :icon="Promotion"
            :loading="isGenerating"
            :disabled="!canSubmit"
            @click="submitAnalysis"
          >
            {{ isGenerating ? '生成中...' : '提交生成报告' }}
          </el-button>
        </div>
      </div>

      <!-- 报告显示区（对话形式） -->
      <div class="report-section" v-if="reportContent">
        <div class="report-message">
          <div class="message-avatar">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="message-content">
            <div class="report-text" v-html="formatReportText(reportContent.text)"></div>
            <div class="report-charts" v-if="reportContent.charts && reportContent.charts.length > 0">
              <div 
                v-for="(chart, index) in reportContent.charts" 
                :key="index"
                class="chart-container"
              >
                <div :id="`chart-${index}`" class="chart" :ref="el => setChartRef(el, index)"></div>
              </div>
            </div>
            <div class="report-actions">
              <el-button 
                type="primary" 
                :icon="Download"
                @click="downloadReport"
              >
                下载报告 (PDF)
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 流式交互体验说明 -->
      <div class="flow-info" v-if="!reportContent">
        <el-alert
          type="info"
          :closable="false"
          show-icon
        >
          <template #title>
            <div class="flow-info-content">
              <el-icon><Refresh /></el-icon>
              <span>流式交互体验</span>
            </div>
          </template>
          <p>系统会保存每次报告，便于回溯与复用。也可继续提问：如"对比渠道A与渠道B的收入差异"。</p>
        </el-alert>
      </div>
      </template>
    </div>

    <!-- 工作流配置弹窗 -->
    <el-dialog
      v-model="showSettings"
      :title="currentWorkflow ? '编辑工作流配置' : '配置工作流'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="settingsForm" label-width="120px">
        <!-- 步骤1: 选择平台 -->
        <el-form-item label="AI平台">
          <el-radio-group v-model="settingsForm.platform" @change="handlePlatformChange">
            <el-radio-button value="dify">Dify</el-radio-button>
            <el-radio-button value="langchain">Langchain</el-radio-button>
            <el-radio-button value="ragflow">Ragflow</el-radio-button>
            <el-radio-button value="other" disabled>其他（开发中）</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 步骤2: 根据平台显示不同配置 -->
        <template v-if="settingsForm.platform">
          <!-- Dify配置 -->
          <template v-if="settingsForm.platform === 'dify'">
            <el-divider content-position="left">工作流API配置</el-divider>
            
            <el-form-item label="API Key" required>
              <el-input 
                v-model="settingsForm.config.api_key" 
                type="password"
                placeholder="例如: app-G5TRX6MyLsQdfj4V4NRWAplZ"
                show-password
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  您的Dify API密钥
                </div>
              </template>
            </el-form-item>

            <el-form-item label="文件上传URL" required>
              <el-input 
                v-model="settingsForm.config.url_file" 
                placeholder="例如: http://118.89.16.95/v1/files/upload"
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  文件上传接口地址
                </div>
              </template>
            </el-form-item>

            <el-form-item label="工作流URL" required>
              <el-input 
                v-model="settingsForm.config.url_work" 
                placeholder="例如: http://118.89.16.95/v1/chat-messages"
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  工作流执行接口地址
                </div>
              </template>
            </el-form-item>

            <el-form-item label="文件参数名" required>
              <el-input 
                v-model="settingsForm.config.file_param" 
                placeholder="例如: excell"
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  传入文件的参数名称
                </div>
              </template>
            </el-form-item>

            <el-form-item label="对话参数名" required>
              <el-input 
                v-model="settingsForm.config.query_param" 
                placeholder="例如: query"
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  传入对话内容的参数名称
                </div>
              </template>
            </el-form-item>
          </template>

          <!-- Langchain配置 -->
          <template v-if="settingsForm.platform === 'langchain'">
            <el-divider content-position="left">Langchain配置</el-divider>
            
            <el-form-item label="工作流名称" required>
              <el-input v-model="settingsForm.name" placeholder="例如：运营数据分析工作流" />
            </el-form-item>

            <el-form-item label="模型类型" required>
              <el-select v-model="settingsForm.config.model_type" placeholder="选择模型">
                <el-option label="OpenAI" value="openai" />
                <el-option label="Claude" value="claude" />
                <el-option label="本地模型" value="local" />
              </el-select>
            </el-form-item>

            <el-form-item label="API Key" required>
              <el-input 
                v-model="settingsForm.config.api_key" 
                type="password"
                placeholder="输入模型API Key"
                show-password
              />
            </el-form-item>

            <el-form-item label="模型名称">
              <el-input 
                v-model="settingsForm.config.model_name" 
                placeholder="例如：gpt-4, claude-3-opus"
              />
            </el-form-item>

            <el-form-item label="提示词模板">
              <el-input 
                v-model="settingsForm.config.prompt_template" 
                type="textarea"
                :rows="3"
                placeholder="输入提示词模板，使用{input}作为占位符"
              />
            </el-form-item>

            <el-form-item label="描述">
              <el-input 
                v-model="settingsForm.description" 
                type="textarea"
                :rows="2"
                placeholder="可选的工作流描述"
              />
            </el-form-item>
          </template>

          <!-- Ragflow配置 -->
          <template v-if="settingsForm.platform === 'ragflow'">
            <el-divider content-position="left">Ragflow配置</el-divider>
            
            <el-form-item label="工作流名称" required>
              <el-input v-model="settingsForm.name" placeholder="例如：运营数据分析工作流" />
            </el-form-item>

            <el-form-item label="Ragflow API地址" required>
              <el-input 
                v-model="settingsForm.config.api_url" 
                placeholder="https://your-ragflow.com/api"
              />
            </el-form-item>

            <el-form-item label="API Key" required>
              <el-input 
                v-model="settingsForm.config.api_key" 
                type="password"
                placeholder="输入Ragflow API Key"
                show-password
              />
            </el-form-item>

            <el-form-item label="知识库ID">
              <el-input 
                v-model="settingsForm.config.kb_id" 
                placeholder="关联的知识库ID（可选）"
              />
            </el-form-item>

            <el-form-item label="对话模型">
              <el-input 
                v-model="settingsForm.config.chat_model" 
                placeholder="例如：gpt-4"
              />
            </el-form-item>

            <el-form-item label="描述">
              <el-input 
                v-model="settingsForm.description" 
                type="textarea"
                :rows="2"
                placeholder="可选的工作流描述"
              />
            </el-form-item>
          </template>
        </template>

        <el-alert
          v-else
          title="请先选择AI平台"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>

      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveWorkflowConfig"
          :disabled="!canSaveWorkflow"
          :loading="saving"
        >
          {{ currentWorkflow ? '保存配置' : '保存并绑定' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Download,
  UploadFilled,
  Folder,
  Promotion,
  DataAnalysis,
  Refresh,
  Setting,
  Check,
  Warning,
  ArrowLeft
} from '@element-plus/icons-vue'
import type { UploadFile, UploadInstance } from 'element-plus'
import HistorySidebar from './components/HistorySidebar.vue'
import { useOperationStore } from '@/stores/operation'
import { useAuthStore } from '@/store/auth'
import {
  uploadExcel,
  generateReport,
  downloadReportPDF,
  getSessionDetail,
  getReport,
  createSession
} from '@/api/operation'
import { 
  getFunctionWorkflow, 
  bindFunctionWorkflow,
  createWorkflow,
  updateWorkflow
} from '@/api/workflow'

// 导入 echarts
import * as echarts from 'echarts'
// 导入 marked 用于 Markdown 渲染
import { marked } from 'marked'

const router = useRouter()
const authStore = useAuthStore()
const operationStore = useOperationStore()

const sidebarRef = ref<InstanceType<typeof HistorySidebar> | null>(null)
const uploadRef = ref<UploadInstance | null>(null)

const fileList = ref<UploadFile[]>([])
const uploadProgress = ref(0)
const analysisRequest = computed({
  get: () => operationStore.analysisRequest,
  set: (val) => operationStore.setAnalysisRequest(val)
})
const isGenerating = computed(() => operationStore.isGenerating)
const canSubmit = computed(() => operationStore.canSubmit)
const reportContent = computed(() => operationStore.reportContent)

const examples = [
  '生成一份关注新手留存的周度报告',
  '分析用户活跃度趋势',
  '对比不同渠道的收入表现',
  '生成DAU和MAU的月度分析'
]

const chartInstances = ref<Map<number, any>>(new Map())

// 视图模式：upload（上传分析）或 embed（Dify嵌入）
const viewMode = ref<'upload' | 'embed'>('upload')

// Dify嵌入URL
const difyEmbedUrl = computed(() => {
  if (currentWorkflow.value?.config?.embed_url) {
    return currentWorkflow.value.config.embed_url
  }
  return null
})

// 工作流配置相关（简化版，移除权限检查）
const currentWorkflow = ref<any>(null)
const showSettings = ref(false)
const saving = ref(false)
const settingsForm = ref({
  platform: '' as string,
  name: '',
  description: '',
  config: {} as Record<string, any>
})

// 可以保存的条件
const canSaveWorkflow = computed(() => {
  if (!settingsForm.value.platform) return false
  
  const config = settingsForm.value.config
  
  switch (settingsForm.value.platform) {
    case 'dify':
      // 检查用户配置的必需字段
      return !!(config.api_key && config.url_file && config.url_work && config.file_param && config.query_param)
    case 'langchain':
      return config.model_type && config.api_key
    case 'ragflow':
      return config.api_url && config.api_key
    default:
      return false
  }
})

// 切换平台时重置配置
const handlePlatformChange = () => {
  settingsForm.value.config = {}
  settingsForm.value.name = ''
  settingsForm.value.description = ''
}

// 加载工作流配置（静默处理，不显示错误）（简化版，移除project_id参数）
const loadFunctionWorkflow = async () => {
  try {
    const res = await getFunctionWorkflow('operation_data_analysis', true)
    if (res.success && res.data) {
      currentWorkflow.value = res.data.workflow
      // 如果配置了嵌入URL，默认显示嵌入模式
      if (res.data.workflow?.config?.embed_url) {
        viewMode.value = 'embed'
      }
    } else {
      currentWorkflow.value = null
    }
  } catch (error: any) {
    // 静默处理404和其他错误，不在控制台显示
    currentWorkflow.value = null
  }
}

// 填充设置表单（用于编辑现有配置）
const fillSettingsForm = () => {
  if (currentWorkflow.value) {
    // 已有配置，填充表单
    const config = currentWorkflow.value.config || {}
    settingsForm.value = {
      platform: 'dify', // 固定为dify
      name: currentWorkflow.value.name || '',
      description: currentWorkflow.value.description || '',
      config: {
        api_key: config.api_key || '',
        url_file: config.url_file || '',
        url_work: config.url_work || '',
        file_param: config.file_param || 'excell',
        query_param: config.query_param || 'query'
      }
    }
  } else {
    // 没有配置，重置表单
    settingsForm.value = {
      platform: 'dify',
      name: '',
      description: '',
      config: {
        api_key: '',
        url_file: '',
        url_work: '',
        file_param: 'excell',
        query_param: 'query'
      }
    }
  }
}

// 打开设置弹窗（简化版，移除权限检查）
// 跳转到批量分析页面
const goToBatchAnalysis = () => {
  router.push({ name: 'operation-batch' })
}

// 跳转到定制化批量分析页面
const goToCustomBatchAnalysis = () => {
  router.push({ name: 'operation-custom-batch' })
}

// 返回首页
const goToHome = () => {
  router.push({ name: 'home' })
}

const openSettings = () => {
  // 简化版：所有用户都可以配置工作流（或根据实际需求调整）
  fillSettingsForm()
  showSettings.value = true
}

// 监听来自批量分析页面的设置打开事件
const handleOpenSettings = () => {
  openSettings()
}

onMounted(() => {
  window.addEventListener('open-workflow-settings', handleOpenSettings)
  
  // 如果没有当前会话，自动创建新会话
  if (!operationStore.currentSessionId) {
    sidebarRef.value?.loadSessions()
  }
  
  // 加载工作流配置
  loadFunctionWorkflow()
  
  // 初始化图表容器
  nextTick(() => {
    if (chartContainerRef.value) {
      renderCharts()
    }
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('open-workflow-settings', handleOpenSettings)
})

// 保存工作流配置（用户级配置）
const saveWorkflowConfig = async () => {
  if (!canSaveWorkflow.value) return

  saving.value = true
  try {
    // 将用户配置转换为工作流配置格式
    const config = {
      api_key: settingsForm.value.config.api_key,
      api_url: settingsForm.value.config.url_file?.replace('/files/upload', '').replace('/chat-messages', '') || '',
      url_file: settingsForm.value.config.url_file,
      url_work: settingsForm.value.config.url_work,
      workflow_id: '1', // 固定为1，实际使用url_work
      workflow_type: 'chatflow', // 固定为chatflow
      file_param: settingsForm.value.config.file_param || 'excell',
      query_param: settingsForm.value.config.query_param || 'query',
      input_field: `${settingsForm.value.config.file_param || 'excell'},${settingsForm.value.config.query_param || 'query'}`
    }

    const workflowData = {
      name: '运营数据分析工作流',
      category: 'operation',
      platform: 'dify',
      description: '用户配置的工作流',
      config: config,
      is_active: true
    }

    let workflowId: number

    if (currentWorkflow.value) {
      // 更新现有工作流
      const updateRes = await updateWorkflow(currentWorkflow.value.id, workflowData)
      
      if (!updateRes.success || !updateRes.data) {
        throw new Error('更新工作流失败')
      }
      
      workflowId = updateRes.data.id
      ElMessage.success('工作流配置已更新')
    } else {
      // 创建新工作流
      const createRes = await createWorkflow(workflowData)
      
      if (!createRes.success || !createRes.data) {
        throw new Error('创建工作流失败')
      }

      workflowId = createRes.data.id

      // 绑定工作流到当前功能（用户级绑定）
      await bindFunctionWorkflow({
        function_key: 'operation_data_analysis',
        workflow_id: workflowId
      })

      ElMessage.success('工作流配置成功')
    }

    showSettings.value = false
    
    // 重新加载配置
    await loadFunctionWorkflow()
  } catch (error: any) {
    console.error('保存工作流配置失败:', error)
    ElMessage.error(error.message || '保存工作流配置失败')
  } finally {
    saving.value = false
  }
}

// 文件处理
const validateFile = (file: File): boolean => {
  const validTypes = ['.xlsx', '.csv']
  const maxSize = 10 * 1024 * 1024 // 10MB
  
  const ext = file.name.substring(file.name.lastIndexOf('.'))
  if (!validTypes.includes(ext.toLowerCase())) {
    ElMessage.error('只支持 .xlsx 和 .csv 格式的文件')
    return false
  }
  
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  
  return true
}

const handleFileChange = async (file: UploadFile) => {
  if (!file.raw) return
  
  // 验证文件格式和大小
  if (!validateFile(file.raw)) {
    uploadRef.value?.clearFiles()
    return
  }
  
  try {
    // 如果没有会话，先创建一个新会话
    let sessionId = operationStore.currentSessionId
    if (!sessionId) {
      ElMessage.info('正在创建新会话...')
      try {
        const createResponse = await createSession()  // 移除project_id参数
        if (createResponse.success && createResponse.data) {
          const newSession = createResponse.data
          operationStore.addSession(newSession)
          operationStore.setCurrentSession(newSession.id)
          sessionId = newSession.id
          // 通知侧边栏刷新
          sidebarRef.value?.loadSessions()
          ElMessage.success('新会话已创建')
        } else {
          console.error('创建会话响应格式错误:', createResponse)
          ElMessage.error('创建会话失败，请重试')
          uploadRef.value?.clearFiles()
          return
        }
      } catch (error: any) {
        console.error('创建会话失败:', error)
        ElMessage.error(error.message || '创建会话失败，请重试')
        uploadRef.value?.clearFiles()
        return
      }
    }
    
    // 开始上传文件
    uploadProgress.value = 0
    ElMessage.info('正在上传文件...')
    
    const response = await uploadExcel(
      file.raw,
      sessionId,
      (progress) => {
        uploadProgress.value = progress
      }
    )
    
    if (response.success && response.data) {
      operationStore.setFileId(response.data.file_id)
      operationStore.setCurrentFile(file.raw)
      ElMessage.success(`文件上传成功: ${file.name}`)
      uploadProgress.value = 100
      
      // 更新文件列表显示
      fileList.value = [{
        name: file.name,
        status: 'success',
        uid: file.uid,
        raw: file.raw
      }]
      
      // 刷新历史会话列表，确保新创建的会话显示在历史记录中
      sidebarRef.value?.loadSessions()
    } else {
      console.error('文件上传响应格式错误:', response)
      ElMessage.error(response.message || '文件上传失败')
      uploadRef.value?.clearFiles()
      uploadProgress.value = 0
    }
  } catch (error: any) {
    console.error('文件上传错误:', error)
    const errorMsg = error.response?.data?.error?.message || error.message || '文件上传失败'
    ElMessage.error(errorMsg)
    uploadRef.value?.clearFiles()
    uploadProgress.value = 0
  }
}

const handleFileRemove = () => {
  operationStore.setFileId(null)
  operationStore.setCurrentFile(null)
  uploadProgress.value = 0
  fileList.value = []
}

const handleUploadError = (error: Error, file: UploadFile) => {
  console.error('文件上传错误:', error, file)
  ElMessage.error(`文件上传失败: ${error.message || '未知错误'}`)
  uploadRef.value?.clearFiles()
  uploadProgress.value = 0
}

const triggerFileSelect = () => {
  const input = uploadRef.value?.$el?.querySelector('input[type="file"]')
  if (input) {
    input.click()
  } else {
    ElMessage.warning('无法打开文件选择器，请直接拖拽文件')
  }
}

// 分析需求提交（简化版，移除project_id参数）
const submitAnalysis = async () => {
  if (!canSubmit.value) {
    ElMessage.warning('请先上传Excel文件并输入分析需求')
    return
  }
  
  if (!operationStore.currentSessionId || !operationStore.fileId) {
    ElMessage.warning('请先创建会话并上传文件')
    return
  }
  
  operationStore.setGenerating(true)
  
  try {
    const response = await generateReport({
      session_id: operationStore.currentSessionId,
      file_id: operationStore.fileId,
      analysis_request: analysisRequest.value
    })
    
    if (response.success && response.data) {
      const reportData = response.data
      operationStore.setReportContent(reportData.content)
      operationStore.setReportId(reportData.report_id)
      
      // 渲染图表
      await nextTick()
      renderCharts(reportData.content.charts || [])
      
      ElMessage.success('报告生成成功')
    }
  } catch (error: any) {
    console.error('报告生成失败:', error)
    
    let errorMsg = '报告生成失败，请重试'
    
    if (error.response?.data) {
      const data = error.response.data
      errorMsg = data.detail || data.error?.message || data.message || errorMsg
    } else if (error.message) {
      errorMsg = error.message
    }
    
    ElMessage.error({
      message: errorMsg,
      duration: 5000,
      showClose: true
    })
    
    if (errorMsg.includes('Dify') || errorMsg.includes('dify') || errorMsg.includes('工作流')) {
      console.warn('可能是 Dify 工作流配置或执行问题，请检查：')
      console.warn('1. Dify API 地址和 API Key 是否正确')
      console.warn('2. Dify Chatflow 是否配置正确')
      console.warn('3. 文件是否成功上传到 Dify')
    }
  } finally {
    operationStore.setGenerating(false)
  }
}

// 渲染图表
const renderCharts = async (charts: any[]) => {
  if (!charts || charts.length === 0) return
  
  await nextTick()
  
  charts.forEach((chart, index) => {
    const chartElement = document.getElementById(`chart-${index}`)
    if (!chartElement) return
    
    // 如果已存在实例，先销毁
    const existingInstance = chartInstances.value.get(index)
    if (existingInstance) {
      existingInstance.dispose()
    }
    
    const chartInstance = echarts.init(chartElement)
    chartInstances.value.set(index, chartInstance)
    
    // 设置图表配置
    const option = chart.config || {
      title: {
        text: chart.title || '图表'
      },
      tooltip: {},
      xAxis: {
        type: 'category',
        data: chart.data?.xAxis || []
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        type: chart.type || 'line',
        data: chart.data?.series || []
      }]
    }
    
    chartInstance.setOption(option)
    
    // 响应式调整
    window.addEventListener('resize', () => {
      chartInstance.resize()
    })
  })
}

const setChartRef = (el: any, index: number) => {
  // 图表容器引用已通过ID设置
}

// 格式化报告文本（使用 Markdown 渲染）
const formatReportText = (text: string) => {
  if (!text) return ''
  
  try {
    marked.setOptions({
      breaks: true,
      gfm: true,
    })
    
    const html = marked.parse(text)
    // 移除所有表格（包括table标签及其内容）
    const htmlWithoutTables = html.replace(/<table[\s\S]*?<\/table>/gi, '')
    return htmlWithoutTables
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return text.replace(/\n/g, '<br>')
  }
}

// 导出图表为Base64图片数组
const exportChartsAsImages = async () => {
  const chartImages: Array<{index: number, title: string, image: string}> = []
  
  // 遍历所有图表实例
  for (const [index, chartInstance] of chartInstances.value.entries()) {
    try {
      const imageDataUrl = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff'
      })
      
      const chartTitle = reportContent.value?.charts?.[index]?.title || 
                        reportContent.value?.charts?.[index]?.config?.title?.text ||
                        `图表${index + 1}`
      
      chartImages.push({
        index: index,
        title: chartTitle,
        image: imageDataUrl
      })
    } catch (error) {
      console.error(`导出图表${index}失败:`, error)
    }
  }
  
  return chartImages
}

// 下载报告（简化版，移除project_id参数）
const downloadReport = async () => {
  if (!operationStore.currentSessionId) {
    ElMessage.warning('会话ID不存在，请先创建会话并生成报告')
    return
  }
  
  if (!operationStore.reportContent) {
    ElMessage.warning('报告内容不存在，请先生成报告')
    return
  }
  
  try {
    ElMessage.info('正在准备下载，请稍候...')
    
    if (chartInstances.value.size === 0) {
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
    
    // 1. 导出图表为图片
    const chartImages = await exportChartsAsImages()
    
    // 2. 调用后端API，传递图表图片（移除project_id参数）
    const reportId = operationStore.reportId || `report_${operationStore.currentSessionId}`
    const response = await downloadReportPDF(
      reportId,
      operationStore.currentSessionId,
      chartImages
    )
    
    // 检查响应是否是 Blob
    if (response.data instanceof Blob) {
      const contentType = response.headers?.['content-type'] || ''
      if (contentType.includes('application/json')) {
        const text = await response.data.text()
        try {
          const jsonData = JSON.parse(text)
          const errorMsg = jsonData?.error?.message || jsonData?.detail || jsonData?.message || '报告下载失败'
          ElMessage.error(errorMsg)
          return
        } catch {
          ElMessage.error('报告下载失败')
          return
        }
      }
      
      // 是 PDF 文件，创建下载链接
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const sessionTitle = operationStore.currentSession?.title || '数据分析报告'
      link.download = `${sessionTitle}_${new Date().getTime()}.pdf`
      link.click()
      window.URL.revokeObjectURL(url)
      ElMessage.success('报告下载成功')
    } else {
      ElMessage.error('响应格式错误')
    }
  } catch (error: any) {
    console.error('下载报告失败:', error)
    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text()
        const jsonData = JSON.parse(text)
        const errorMsg = jsonData?.error?.message || jsonData?.detail || jsonData?.message || '报告下载失败'
        ElMessage.error(errorMsg)
      } catch {
        ElMessage.error('报告下载失败')
      }
    } else {
      const errorMsg = error.response?.data?.detail || error.message || '报告下载失败'
      ElMessage.error(errorMsg)
    }
  }
}


// 使用示例
const useExample = (example: string) => {
  analysisRequest.value = example
}

// 会话选择处理
const handleSessionSelected = async (sessionId: number) => {
  try {
    const response = await getSessionDetail(sessionId)
    if (response.success && response.data) {
      const session = response.data
      
      // 加载历史消息
      if (session.messages && session.messages.length > 0) {
        const userMessages = session.messages.filter((msg: any) => msg.role === 'user')
        const lastUserMsg = userMessages.length > 0 ? userMessages[userMessages.length - 1] : null
        
        if (lastUserMsg?.file_name) {
          fileList.value = [{
            name: lastUserMsg.file_name,
            status: 'success'
          } as UploadFile]
          ElMessage.info(`已加载历史会话：${session.title}`)
        }
        
        const assistantMessages = session.messages.filter((msg: any) => msg.role === 'assistant')
        const lastAssistantMsg = assistantMessages.length > 0 ? assistantMessages[assistantMessages.length - 1] : null
        
        if (lastAssistantMsg) {
          operationStore.setReportContent({
            text: lastAssistantMsg.content || '',
            charts: lastAssistantMsg.charts || [],
            tables: lastAssistantMsg.tables || [],
            metrics: {}
          })
          
          if (lastAssistantMsg.report_id) {
            operationStore.setReportId(lastAssistantMsg.report_id)
          }
          
          await nextTick()
          renderCharts(lastAssistantMsg.charts || [])
          
          ElMessage.success('历史会话已加载')
        } else {
          operationStore.setReportContent(null)
          operationStore.setReportId(null)
        }
      } else {
        fileList.value = []
        operationStore.setReportContent(null)
        operationStore.setReportId(null)
        analysisRequest.value = ''
      }
    }
  } catch (error: any) {
    console.error('加载会话详情失败:', error)
    ElMessage.error('加载会话详情失败')
  }
}

// 会话创建处理
const handleSessionCreated = (session: any) => {
  // 重置状态（清空文件上传和报告内容）
  fileList.value = []
  uploadProgress.value = 0
  operationStore.setFileId(null)
  operationStore.setCurrentFile(null)
  operationStore.setReportContent(null)
  operationStore.setReportId(null)
  analysisRequest.value = ''
  
  // 注意：不需要重新加载会话列表，因为HistorySidebar已经处理了
  // 只需要确保当前会话已设置
  if (session && session.id) {
    operationStore.setCurrentSession(session.id)
  }
}

// 组件卸载时清理图表实例
onMounted(() => {
  // 如果没有当前会话，自动创建新会话
  if (!operationStore.currentSessionId) {
    sidebarRef.value?.loadSessions()
  }
  
  // 加载工作流配置
  loadFunctionWorkflow()
  
  // 初始化图表容器
  nextTick(() => {
    renderCharts()
  })
})
</script>

<style scoped>
.data-analysis-page {
  display: flex;
  height: 100vh;
  background: var(--apple-bg-gradient);
}

.main-content {
  flex: 1;
  padding: var(--apple-space-2xl);
  overflow-y: auto;
  background: var(--apple-bg-primary);
}

.data-analysis-page:has(.dify-embed-container) .main-content {
  width: 100%;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--apple-space-2xl);
  padding-bottom: var(--apple-space-2xl);
  border-bottom: 1px solid var(--apple-border-light);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.workflow-status-bar {
  margin-bottom: 16px;
}

.mode-switch {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.dify-embed-container {
  width: 100%;
  height: calc(100vh - 300px);
  min-height: 700px;
  border: 1px solid var(--apple-border-light);
  border-radius: var(--apple-radius-lg);
  overflow: hidden;
  background: var(--apple-bg-primary);
  box-shadow: var(--apple-shadow-md);
}

.header-text {
  border-bottom: none;
}

.header-text h1 {
  margin: 0 0 var(--apple-space-sm) 0;
  font-size: var(--apple-font-2xl);
  font-weight: 600;
  color: var(--apple-text-primary);
  letter-spacing: -0.3px;
}

.header-text p {
  margin: 0;
  color: var(--apple-text-secondary);
  font-size: var(--apple-font-sm);
}

.upload-section {
  margin-bottom: 24px;
}

.excel-uploader {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  padding: var(--apple-space-4xl);
  border: 2px dashed var(--apple-border);
  border-radius: var(--apple-radius-lg);
  background: var(--apple-bg-primary);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--apple-primary);
  background: rgba(0, 122, 255, 0.02);
  box-shadow: var(--apple-shadow-sm);
}

.upload-icon {
  font-size: 48px;
  color: var(--apple-primary);
  margin-bottom: var(--apple-space-lg);
}

.upload-text {
  text-align: center;
}

.upload-text p {
  margin: var(--apple-space-sm) 0;
  color: var(--apple-text-primary);
  font-size: var(--apple-font-base);
}

.upload-hint {
  color: var(--apple-text-secondary);
  font-size: var(--apple-font-sm);
}

.upload-tip {
  margin-top: 16px;
  text-align: center;
}

.upload-progress {
  margin-top: 16px;
}

.input-section {
  margin-bottom: var(--apple-space-2xl);
  padding: var(--apple-space-2xl);
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  border: 1px solid var(--apple-border-light);
  box-shadow: var(--apple-shadow-sm);
}

.input-header {
  margin-bottom: var(--apple-space-lg);
}

.input-header h3 {
  margin: 0;
  font-size: var(--apple-font-xl);
  font-weight: 600;
  color: var(--apple-text-primary);
  letter-spacing: -0.2px;
}

.input-examples {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.example-tag:hover {
  background: var(--notion-primary);
  color: #fff;
}

.submit-section {
  margin-top: 24px;
  text-align: center;
}

.report-section {
  margin-top: var(--apple-space-2xl);
  padding: var(--apple-space-2xl);
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  border: 1px solid var(--apple-border-light);
  box-shadow: var(--apple-shadow-md);
}

.report-message {
  display: flex;
  gap: 16px;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--apple-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: var(--apple-shadow-sm);
}

.message-content {
  flex: 1;
}

.report-text {
  color: var(--apple-text-primary);
  line-height: 1.8;
  margin-bottom: var(--apple-space-xl);
  
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin-top: 16px;
    margin-bottom: 8px;
    font-weight: 600;
    line-height: 1.3;
  }
  
  :deep(h1) { font-size: 1.8em; }
  :deep(h2) { font-size: 1.5em; }
  :deep(h3) { font-size: 1.3em; }
  
  :deep(p) {
    margin: 8px 0;
    word-break: break-word;
  }
  
  :deep(code) {
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }
  
  :deep(pre) {
    background: rgba(0, 0, 0, 0.05);
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 12px 0;
    
    code {
      background: none;
      padding: 0;
    }
  }
  
  :deep(ul), :deep(ol) {
    margin: 8px 0;
    padding-left: 24px;
  }
  
  :deep(li) {
    margin: 4px 0;
  }
  
  :deep(blockquote) {
    border-left: 3px solid var(--el-color-primary);
    padding-left: 12px;
    margin: 12px 0;
    color: var(--notion-text-secondary);
  }
  
  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    
    th, td {
      border: 1px solid var(--notion-border);
      padding: 8px;
      text-align: left;
    }
    
    th {
      background: rgba(0, 0, 0, 0.05);
      font-weight: 600;
    }
  }
  
  :deep(a) {
    color: var(--el-color-primary);
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
  
  :deep(strong) {
    font-weight: 600;
  }
  
  :deep(em) {
    font-style: italic;
  }
}

.report-charts {
  margin: 20px 0;
}

.chart-container {
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--notion-border);
}

.chart {
  width: 100%;
  height: 400px;
}

.report-tables {
  margin: 20px 0;
}

.report-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--notion-border);
}

.flow-info {
  margin-top: 24px;
}

.flow-info-content {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>

