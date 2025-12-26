<template>
  <div class="batch-analysis-page">
    <!-- 左侧批量分析历史会话栏 -->
    <BatchHistorySidebar
      @session-selected="handleSessionSelected"
      @create-new="handleCreateNew"
      ref="sidebarRef"
    />

    <!-- 右侧主内容区 -->
    <div class="main-content">
      <!-- 顶部：标题和上传按钮 -->
      <div class="content-header">
        <div class="header-text">
          <h1>批量数据分析</h1>
          <p>上传包含多个Sheet的Excel文件，系统将自动拆分并对每个Sheet生成分析报告</p>
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
            @click="goToSingleAnalysis"
          >
            单文件分析
          </el-button>
          <el-button 
            type="primary"
            :icon="DataAnalysis"
            @click="goToCustomBatchAnalysis"
          >
            定制化批量分析
          </el-button>
          <el-button
            v-if="currentReportDetail"
            type="success"
            :icon="ChatDotRound"
            @click="toggleDialogPanel"
            :class="{ active: showDialogPanel }"
          >
            {{ showDialogPanel ? '隐藏对话' : 'AI对话' }}
          </el-button>
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

      <!-- 上传和进度区域 -->
      <div class="upload-section" v-if="batchStatus === 'idle' || batchStatus === 'uploading' || batchStatus === 'splitting'">
        <el-upload
          ref="uploadRef"
          class="excel-uploader"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :on-error="handleUploadError"
          accept=".xlsx"
          :limit="1"
          :file-list="fileList"
          :show-file-list="true"
          :disabled="batchStatus === 'uploading' || batchStatus === 'splitting'"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p>将Excel文件拖到此处，或<em>点击上传</em></p>
            <p class="upload-tip">支持 .xlsx 格式，最大 20MB</p>
          </div>
        </el-upload>

        <!-- 上传进度和状态提示 -->
        <div v-if="batchStatus === 'uploading' || batchStatus === 'splitting'" class="upload-status-card">
          <el-card shadow="hover" class="status-card">
            <div class="status-content">
              <div class="status-icon">
                <el-icon v-if="batchStatus === 'uploading'" class="rotating">
                  <UploadFilled />
                </el-icon>
                <el-icon v-else-if="batchStatus === 'splitting'" class="rotating">
                  <Loading />
                </el-icon>
              </div>
              <div class="status-text">
                <h3 v-if="batchStatus === 'uploading'">正在上传文件...</h3>
                <h3 v-else-if="batchStatus === 'splitting'">正在拆分Excel文件...</h3>
                <p v-if="batchStatus === 'uploading'">请稍候，文件正在上传到服务器</p>
                <p v-else-if="batchStatus === 'splitting'">系统正在将Excel文件拆分为多个Sheet</p>
              </div>
            </div>
            <el-progress 
              v-if="batchStatus === 'uploading'"
              :percentage="uploadProgress" 
              :status="uploadProgress === 100 ? 'success' : undefined"
              :stroke-width="8"
              class="status-progress"
            />
            <div v-else-if="batchStatus === 'splitting'" class="splitting-indicator">
              <el-icon class="rotating"><Loading /></el-icon>
              <span>正在处理中...</span>
            </div>
          </el-card>
        </div>
        
        <!-- 上传成功提示（一直显示，只要batchSessionId存在就显示） -->
        <div v-if="batchSessionId" class="upload-success-card">
          <el-alert
            type="success"
            :closable="false"
            show-icon
            class="success-alert"
          >
            <template #title>
              <div class="success-content">
                <div class="success-icon">
                  <el-icon><CircleCheckFilled /></el-icon>
                </div>
                <div class="success-text">
                  <h3>文件上传成功！</h3>
                  <p>
                    已成功拆分为 <strong>{{ batchReports.length || batchStatusData?.total_sheets || 0 }}</strong> 个Sheet
                    <template v-if="batchStatus === 'idle'">，请在下方的输入框中输入分析需求，然后点击"提交生成报告"按钮开始分析。</template>
                    <template v-else-if="(batchStatus as any) === 'analyzing'">，正在分析中...</template>
                    <template v-else-if="(batchStatus as any) === 'completed'">，分析已完成！</template>
                  </p>
                </div>
              </div>
            </template>
          </el-alert>
        </div>

        <!-- 分析需求输入区 -->
        <div class="input-section" v-if="batchStatus === 'idle'">
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
          
          <!-- 图表定制 Prompt 输入区（可选） -->
          <div class="chart-customization-section" style="margin-top: 20px;">
            <div class="input-header" style="display: flex; justify-content: space-between; align-items: center;">
              <h3 style="margin: 0; font-size: 14px;">图表定制 Prompt（可选）</h3>
              <el-switch
                v-model="enableChartCustomization"
                size="small"
              />
            </div>
            <el-input
              v-if="enableChartCustomization"
              v-model="chartCustomizationPrompt"
              type="textarea"
              :rows="4"
              placeholder="请输入图表定制需求，例如：&#10;- 请生成折线图，展示新用户增长趋势&#10;- 使用蓝色主题，添加数据标签&#10;- 图表标题：新用户增长趋势分析"
              :maxlength="500"
              show-word-limit
              style="margin-top: 10px;"
            />
            <div v-else class="hint-text" style="margin-top: 10px; padding: 10px; background: #f5f7fa; border-radius: 4px; color: #909399; font-size: 12px;">
              💡 开启后可以定制图表样式和类型，例如指定图表类型、颜色主题、数据标签等
            </div>
          </div>
          
          <div class="submit-section">
            <el-button 
              type="primary" 
              size="large"
              :icon="Promotion"
              :loading="isStarting"
              :disabled="!canStartAnalysis"
              @click="startAnalysis"
            >
              {{ isStarting ? '分析中...' : '提交生成报告' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分析进度区域 -->
      <div class="progress-section" v-if="batchStatus === 'analyzing'">
        <el-card>
          <template #header>
            <div class="progress-header">
              <span>批量分析进度</span>
              <el-tag :type="getProgressTagType()">
                {{ batchProgress }}% ({{ completedCount }}/{{ totalCount }})
              </el-tag>
            </div>
          </template>
          <el-progress
            :percentage="batchProgress"
            :status="(batchStatus as any) === 'completed' ? 'success' : undefined"
            :stroke-width="20"
          />
          <div class="progress-details" v-if="batchStatusData">
            <div class="detail-item">
              <span>已完成: </span>
              <el-tag type="success" size="small">{{ batchStatusData.completed_sheets }}</el-tag>
            </div>
            <div class="detail-item">
              <span>分析中: </span>
              <el-tag type="warning" size="small">{{ batchStatusData.generating_sheets }}</el-tag>
            </div>
            <div class="detail-item">
              <span>待处理: </span>
              <el-tag type="info" size="small">{{ batchStatusData.pending_sheets }}</el-tag>
            </div>
            <div class="detail-item" v-if="batchStatusData.failed_sheets > 0">
              <span>失败: </span>
              <el-tag type="danger" size="small">{{ batchStatusData.failed_sheets }}</el-tag>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 报告标签页区域（AI对话模式下隐藏） -->
      <div class="reports-tabs-container" v-if="batchReports.length > 0 && !showDialogPanel">
        <ReportTabs
          :reports="batchReports"
          :current-index="currentReportIndex"
          @tab-change="handleTabChange"
        />
      </div>

      <!-- 报告显示区域 -->
      <div class="report-display-container" v-if="currentReportDetail">
        <!-- AI对话模式：左右分栏布局 -->
        <div v-if="showDialogPanel" class="dialog-mode-layout">
          <!-- 左侧：对话面板 -->
          <div class="dialog-left-panel" :style="{ width: dialogPanelWidth + 'px' }">
            <DialogPanel
              v-if="currentReportDetail"
              ref="dialogPanelRef"
              :session-id="currentReportDetail.id"
              :charts="[]"
              :conversation-id="''"
              :report-text="currentReportDetail.report_content?.text || ''"
              @dialog-response="handleDialogResponse"
              @panel-toggle="toggleDialogPanel"
              @history-cleared="handleHistoryCleared"
              @exit-edit="handleExitEdit"
            />
          </div>
          
          <!-- 拖拽分隔条 -->
          <div 
            class="resize-handle"
            @mousedown="startResize"
            :title="`拖拽调整宽度 (当前: ${dialogPanelWidth}px)`"
          >
            <div class="resize-handle-line"></div>
            <div v-if="isResizing" class="resize-tooltip">
              {{ dialogPanelWidth }}px
            </div>
          </div>
          
          <!-- 右侧：报告展示 -->
          <div class="dialog-right-panel" ref="reportDisplayRef" :style="{ width: `calc(100% - ${dialogPanelWidth}px - 8px)` }">
            <ReportDisplay
              :report="currentReportDetail"
              :loading="isLoadingReport"
              :is-dialog-mode="true"
              @edit-chart="handleEditChartFromReport"
            />
          </div>
        </div>
        
        <!-- 普通模式：只显示报告 -->
        <ReportDisplay
          v-else
          :report="currentReportDetail"
          :loading="isLoadingReport"
          :is-dialog-mode="false"
          @edit-chart="handleEditChartFromReport"
        />
      </div>

      <!-- 空状态提示（仅在没有任何会话且没有文件时显示） -->
      <div class="empty-state" v-if="batchStatus === 'idle' && !batchSessionId && fileList.length === 0 && batchReports.length === 0">
        <el-empty description="请上传包含多个Sheet的Excel文件开始批量分析" />
      </div>
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
    
    <!-- 图表编辑器（全屏模式） -->
    <ChartEditorModal
      v-model="showChartEditor"
      :chart-html="editingChartHtml"
      :chart-title="editingChartTitle"
      :session-id="currentReportDetail?.id"
      @save="handleChartEditorSave"
      @cancel="handleChartEditorCancel"
    />
    
    <!-- AI文本编辑工具栏 -->
    <TextEditToolbar :target-element="'.report-text, .report-content'" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElUpload, type UploadFile } from 'element-plus'
import {
  UploadFilled,
  Check,
  DataAnalysis,
  Promotion,
  ArrowLeft,
  ChatDotRound,
  Loading,
  CircleCheckFilled
} from '@element-plus/icons-vue'
import { useOperationStore } from '@/stores/operation'
import BatchHistorySidebar from './components/BatchHistorySidebar.vue'
import ReportTabs from './components/ReportTabs.vue'
import ReportDisplay from './components/ReportDisplay.vue'
import DialogPanel from './components/DialogPanel.vue'
import ChartEditorModal from '@/components/ChartEditorModal.vue'
import TextEditToolbar from '@/components/TextEditToolbar.vue'
import {
  uploadBatchExcel,
  startBatchAnalysis,
  getBatchAnalysisStatus,
  getSheetReport,
  getBatchSessions
} from '@/api/operation'
import type { SheetReportDetail } from '@/api/operation'
import type { ApiResponse } from '@/types'
import { 
  getFunctionWorkflow,
  bindFunctionWorkflow,
  createWorkflow,
  updateWorkflow
} from '@/api/workflow'

const router = useRouter()
const operationStore = useOperationStore()

// 工作流相关
const currentWorkflow = ref<any>(null)

// 跳转到单文件分析页面
const goToSingleAnalysis = () => {
  router.push({ name: 'operation' })
}

// 跳转到定制化批量分析页面
const goToCustomBatchAnalysis = () => {
  router.push({ name: 'operation-custom-batch' })
}

// 返回首页
const goToHome = () => {
  router.push({ name: 'home' })
}

// 文件上传相关
const uploadRef = ref<InstanceType<typeof ElUpload> | null>(null)
const fileList = ref<UploadFile[]>([])
const uploadProgress = ref(0)
const analysisRequest = ref('生成数据分析报告，包含图表和关键指标')
const enableChartCustomization = ref(false)
const chartCustomizationPrompt = ref('')

// 批量分析相关
const batchSessionId = computed(() => operationStore.batchSessionId)
const batchReports = computed(() => operationStore.batchReports)
const currentReportIndex = computed(() => operationStore.currentReportIndex)
const batchStatus = computed(() => operationStore.batchStatus)
const batchStatusData = computed(() => operationStore.batchStatusData)
const batchProgress = computed(() => operationStore.batchProgress)

// 其他状态
const isStarting = ref(false)
const isLoadingReport = ref(false)
const currentReportDetail = ref<SheetReportDetail | null>(null)
const sidebarRef = ref<InstanceType<typeof BatchHistorySidebar> | null>(null)
const showSettings = ref(false)
const saving = ref(false)

// AI对话面板状态
const showDialogPanel = ref(false)
const dialogPanelRef = ref<InstanceType<typeof DialogPanel> | null>(null)
const dialogPanelWidth = ref(450) // 默认450px
const isResizing = ref(false)
const startX = ref(0)
const startWidth = ref(0)
const reportDisplayRef = ref<HTMLElement | null>(null)

// 图表编辑器状态
const showChartEditor = ref(false)
const editingChartHtml = ref('')
const editingChartTitle = ref('')

const settingsForm = ref({
  platform: 'dify' as 'dify' | 'langchain' | 'ragflow',
  name: '',
  description: '',
  config: {
    api_key: '',
    url_file: '',
    url_work: '',
    file_param: 'excell',
    query_param: 'query',
    kb_id: '',
    chat_model: ''
  } as any
})

// 轮询定时器
let statusPollingTimer: number | null = null

// 计算属性
const completedCount = computed(() => {
  return batchStatusData.value?.completed_sheets || 0
})

const totalCount = computed(() => {
  return batchStatusData.value?.total_sheets || 0
})

// 分析需求示例
const examples = [
  '生成一份关注新手留存的周度报告',
  '分析用户活跃度趋势',
  '对比不同渠道的收入表现',
  '生成DAU和MAU的月度分析'
]

// 使用示例
const useExample = (example: string) => {
  analysisRequest.value = example
}

// 是否可以开始分析
const canStartAnalysis = computed(() => {
  return batchSessionId.value && analysisRequest.value.trim().length > 0
})

// 是否可以保存工作流配置
const canSaveWorkflow = computed(() => {
  return settingsForm.value.config.api_key.trim().length > 0 &&
         settingsForm.value.config.url_file.trim().length > 0 &&
         settingsForm.value.config.url_work.trim().length > 0
})

// 处理平台切换
const handlePlatformChange = () => {
  // 平台切换时的处理逻辑（如果需要）
}

// 方法
const handleFileChange = async (file: UploadFile) => {
  if (!file.raw) return
  
  // 验证文件格式和大小
  if (!validateFile(file.raw)) {
    uploadRef.value?.clearFiles()
    return
  }
  
  try {
    operationStore.setBatchStatus('uploading')
    uploadProgress.value = 0
    ElMessage.info('正在上传文件...')
    
    const response = await uploadBatchExcel(
      file.raw,
      analysisRequest.value,
      (progress) => {
        uploadProgress.value = progress
      }
    )
    
    const uploadResponse = response as unknown as ApiResponse<any>
    if (uploadResponse.success && uploadResponse.data) {
      const data = uploadResponse.data
      operationStore.setBatchSession(data.batch_session_id)
      operationStore.setBatchReports(data.sheets)
      uploadProgress.value = 100
      
      ElMessage.success(`文件上传成功，已拆分为 ${data.sheet_count} 个Sheet，请输入分析需求并点击"提交生成报告"`)
      
      // 刷新批量分析会话列表
      sidebarRef.value?.loadSessions()
      
      // 文件上传成功后，状态回到idle，等待用户输入分析需求并点击"提交生成报告"按钮
      operationStore.setBatchStatus('idle')
    } else {
      const uploadResponse = response as unknown as ApiResponse<any>
      ElMessage.error(uploadResponse.message || '文件上传失败')
      operationStore.setBatchStatus('idle')
      uploadProgress.value = 0
    }
  } catch (error: any) {
    console.error('文件上传错误:', error)
    const errorMsg = error.response?.data?.error?.message || error.message || '文件上传失败'
    ElMessage.error(errorMsg)
    operationStore.setBatchStatus('idle')
    uploadProgress.value = 0
    uploadRef.value?.clearFiles()
  }
}

const validateFile = (file: File): boolean => {
  const validTypes = ['.xlsx']
  const maxSize = 20 * 1024 * 1024 // 20MB
  
  const ext = file.name.substring(file.name.lastIndexOf('.'))
  if (!validTypes.includes(ext.toLowerCase())) {
    ElMessage.error('只支持 .xlsx 格式的文件')
    return false
  }
  
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过20MB')
    return false
  }
  
  return true
}

const handleFileRemove = () => {
  operationStore.resetBatch()
  uploadProgress.value = 0
  fileList.value = []
  currentReportDetail.value = null
}

const handleUploadError = (error: Error, file: UploadFile) => {
  console.error('文件上传错误:', error, file)
  ElMessage.error(`文件上传失败: ${error.message || '未知错误'}`)
  uploadRef.value?.clearFiles()
  operationStore.setBatchStatus('idle')
  uploadProgress.value = 0
}

const handleCreateNew = () => {
  // 重置所有状态
  operationStore.resetBatch()
  uploadProgress.value = 0
  fileList.value = []
  currentReportDetail.value = null
  analysisRequest.value = '生成数据分析报告，包含图表和关键指标'
  enableChartCustomization.value = false
  chartCustomizationPrompt.value = ''
  uploadRef.value?.clearFiles()
  
  // 确保显示上传界面
  operationStore.setBatchStatus('idle')
}

const startAnalysis = async () => {
  if (!batchSessionId.value) {
    ElMessage.warning('请先上传文件')
    return
  }
  
  if (!analysisRequest.value.trim()) {
    ElMessage.warning('请输入分析需求')
    return
  }
  
  isStarting.value = true
  
  try {
    const response = await startBatchAnalysis(
      batchSessionId.value,
      analysisRequest.value,
      enableChartCustomization.value ? chartCustomizationPrompt.value : undefined,
      "html"  // 使用HTML模式
    )
    
    const startResponse = response as unknown as ApiResponse<any>
    if (startResponse.success) {
      operationStore.setBatchStatus('analyzing')
      ElMessage.success('批量分析已开始')
      
      // 开始轮询状态
      startStatusPolling()
    } else {
      const startResponse = response as unknown as ApiResponse<any>
      ElMessage.error(startResponse.message || '启动批量分析失败')
    }
  } catch (error: any) {
    console.error('启动批量分析错误:', error)
    const errorMsg = error.response?.data?.error?.message || error.message || '启动批量分析失败'
    ElMessage.error(errorMsg)
  } finally {
    isStarting.value = false
  }
}

const startStatusPolling = () => {
  if (statusPollingTimer) {
    clearInterval(statusPollingTimer)
  }
  
  statusPollingTimer = window.setInterval(async () => {
    if (!batchSessionId.value) return
    
    try {
      const response = await getBatchAnalysisStatus(batchSessionId.value)
      const pollingStatusResponse = response as unknown as ApiResponse<any>
      
      if (pollingStatusResponse.success && pollingStatusResponse.data) {
        const statusData = pollingStatusResponse.data
        operationStore.setBatchStatusData(statusData)
        
        // 更新报告列表
        const reports = (statusData.reports || []).map((r: any) => ({
          id: r.id,
          sheet_name: r.sheet_name,
          sheet_index: r.sheet_index,
          split_file_path: '',
          report_status: r.report_status as any
        }))
        operationStore.setBatchReports(reports)
        
        // 更新批量状态
        if (statusData.status === 'completed' || statusData.status === 'partial_failed') {
          operationStore.setBatchStatus('completed')
          stopStatusPolling()
          
          // 如果当前选中的报告已完成，加载报告详情
          if (currentReportIndex.value >= 0 && currentReportIndex.value < reports.length) {
            const currentReport = reports[currentReportIndex.value]
            if (currentReport.report_status === 'completed') {
              loadReportDetail(currentReport.id)
            }
          }
        } else if (statusData.status === 'failed') {
          operationStore.setBatchStatus('failed')
          stopStatusPolling()
        }
      }
    } catch (error) {
      console.error('查询状态失败:', error)
    }
  }, 2000) // 每2秒轮询一次
}

const stopStatusPolling = () => {
  if (statusPollingTimer) {
    clearInterval(statusPollingTimer)
    statusPollingTimer = null
  }
}

const handleTabChange = async (index: number) => {
  operationStore.setCurrentReportIndex(index)
  
  if (index >= 0 && index < batchReports.value.length) {
    const report = batchReports.value[index]
    if (report.report_status === 'completed') {
      await loadReportDetail(report.id)
    } else {
      currentReportDetail.value = null
    }
  }
}

const loadReportDetail = async (reportId: number) => {
  isLoadingReport.value = true
  
  try {
    const response = await getSheetReport(reportId)
    
    const reportResponse = response as unknown as ApiResponse<any>
    if (reportResponse.success && reportResponse.data) {
      currentReportDetail.value = reportResponse.data
    } else {
      ElMessage.error('加载报告详情失败')
    }
  } catch (error: any) {
    console.error('加载报告详情错误:', error)
    ElMessage.error('加载报告详情失败')
  } finally {
    isLoadingReport.value = false
  }
}

const handleSessionSelected = async (sessionId: number) => {
  // 加载选中的批量分析会话
  await loadBatchSession(sessionId)
}

const loadBatchSession = async (sessionId: number) => {
  try {
    // 先尝试获取会话状态
    const response = await getBatchAnalysisStatus(sessionId)
    const statusResponse = response as unknown as ApiResponse<any>
    
    if (statusResponse.success && statusResponse.data) {
      const statusData = statusResponse.data
      operationStore.setBatchSession(sessionId)
      operationStore.setBatchStatusData(statusData)
      
      // 如果是draft状态（新建的会话），重置为空白状态
      if (statusData.status === 'draft') {
        operationStore.setBatchStatus('idle')
        operationStore.setBatchReports([])
        operationStore.setCurrentReportIndex(0)
        currentReportDetail.value = null
        fileList.value = []
        uploadProgress.value = 0
        analysisRequest.value = '生成数据分析报告，包含图表和关键指标'
        uploadRef.value?.clearFiles()
        return
      }
      
      // 更新报告列表
      const reports = (statusData.reports || []).map((r: any) => ({
        id: r.id,
        sheet_name: r.sheet_name,
        sheet_index: r.sheet_index,
        split_file_path: '',
        report_status: r.report_status as any
      }))
      operationStore.setBatchReports(reports)
      
      // 设置状态
      if (statusData.status === 'processing') {
        operationStore.setBatchStatus('analyzing')
        startStatusPolling()
      } else if (statusData.status === 'completed' || statusData.status === 'partial_failed') {
        operationStore.setBatchStatus('completed')
      } else {
        operationStore.setBatchStatus('failed')
      }
      
      // 加载第一个报告
      if (reports.length > 0) {
        operationStore.setCurrentReportIndex(0)
        if (reports[0].report_status === 'completed') {
          await loadReportDetail(reports[0].id)
        }
      }
    }
  } catch (error: any) {
    // 如果是404错误，可能是draft状态的会话，重置为空白状态
    if (error.response?.status === 404) {
      operationStore.setBatchSession(sessionId)
      operationStore.setBatchStatus('idle')
      operationStore.setBatchReports([])
      operationStore.setCurrentReportIndex(0)
      currentReportDetail.value = null
      fileList.value = []
      uploadProgress.value = 0
      analysisRequest.value = '生成数据分析报告，包含图表和关键指标'
      uploadRef.value?.clearFiles()
    } else {
      console.error('加载批量会话失败:', error)
      ElMessage.error('加载批量会话失败')
    }
  }
}

// 填充设置表单（用于编辑现有配置）
// const fillSettingsForm = () => {
//   if (currentWorkflow.value) {
//     // 已有配置，填充表单
//     const config = currentWorkflow.value.config || {}
//     settingsForm.value = {
//       platform: 'dify', // 固定为dify
//       name: currentWorkflow.value.name || '',
//       description: currentWorkflow.value.description || '',
//       config: {
//         api_key: config.api_key || '',
//         url_file: config.url_file || '',
//         url_work: config.url_work || '',
//         file_param: config.file_param || 'excell',
//         query_param: config.query_param || 'query'
//       }
//     }
//   } else {
//     // 没有配置，重置表单
//     settingsForm.value = {
//       platform: 'dify',
//       name: '',
//       description: '',
//       config: {
//         api_key: '',
//         url_file: '',
//         url_work: '',
//         file_param: 'excell',
//         query_param: 'query'
//       }
//     }
//   }
// }

// const openSettings = () => {
//   // 所有用户都可以配置工作流
//   fillSettingsForm()
//   showSettings.value = true
// }

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
      const updateRes = await updateWorkflow(currentWorkflow.value.id, workflowData) as unknown as ApiResponse<any>
      
      if (!updateRes.success || !updateRes.data) {
        throw new Error('更新工作流失败')
      }
      
      workflowId = updateRes.data.id
      ElMessage.success('工作流配置已更新')
    } else {
      // 创建新工作流
      const createRes = await createWorkflow(workflowData) as unknown as ApiResponse<any>
      
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

// 加载工作流配置
const loadFunctionWorkflow = async () => {
  try {
    const res = await getFunctionWorkflow('operation_data_analysis', true)
    const workflowRes = res as unknown as ApiResponse<any>
    if (workflowRes.success && workflowRes.data) {
      currentWorkflow.value = res.data.workflow
    } else {
      currentWorkflow.value = null
    }
  } catch (error: any) {
    // 静默处理404和其他错误，不在控制台显示
    currentWorkflow.value = null
  }
}

const getProgressTagType = () => {
  if (batchStatus.value === 'completed') return 'success'
  if (batchStatus.value === 'analyzing') return 'warning'
  return 'info'
}

// ========== AI对话功能 ==========
// 切换对话面板
const toggleDialogPanel = () => {
  showDialogPanel.value = !showDialogPanel.value
}

// 处理对话响应
const handleDialogResponse = (response: any) => {
  console.log('[BatchAnalysis] 收到对话响应:', response)
  
  if (response.action_type === 'regenerate_report' && currentReportDetail.value) {
    // 更新报告内容
    if (response.new_report_text) {
      currentReportDetail.value.report_content.text = response.new_report_text
    }
    if (response.new_html_charts) {
      currentReportDetail.value.report_content.html_charts = response.new_html_charts
    }
    ElMessage.success('报告已更新')
  }
}

// 清除对话历史
const handleHistoryCleared = () => {
  console.log('[BatchAnalysis] 对话历史已清除')
}

// 退出编辑模式
const handleExitEdit = () => {
  showDialogPanel.value = false
}

// ========== 文本选择监听（用于AI对话修改） ==========
const handleTextSelection = () => {
  // 只在对话面板打开时监听
  if (!showDialogPanel.value) return
  
  const selection = window.getSelection()
  const selectedText = selection?.toString().trim()
  
  if (!selectedText || selectedText.length < 2) {
    return
  }
  
  // 检查选中的文本是否在报告区域内
  const reportArea = document.querySelector('.dialog-right-panel')
  if (!reportArea || !selection?.anchorNode) return
  
  if (!reportArea.contains(selection.anchorNode)) {
    return
  }
  
  console.log('[BatchAnalysis] 检测到文本选择:', selectedText.substring(0, 50) + '...')
  
  // 添加高亮动画效果
  addSelectionHighlight(selection)
  
  // 提取上下文
  const context = extractTextContext(selectedText, reportArea as HTMLElement)
  
  // 传递给DialogPanel
  if (dialogPanelRef.value) {
    dialogPanelRef.value.setSelectedText(selectedText, context)
  }
}

// 添加选中文字的高亮动画
const addSelectionHighlight = (selection: Selection) => {
  try {
    const range = selection.getRangeAt(0)
    
    // 创建高亮元素
    const highlight = document.createElement('span')
    highlight.className = 'text-selection-highlight'
    highlight.style.cssText = `
      background: linear-gradient(120deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
      border-radius: 4px;
      padding: 2px 0;
      animation: highlightPulse 0.5s ease-out;
    `
    
    // 包裹选中的内容
    range.surroundContents(highlight)
    
    // 2秒后移除高亮效果
    setTimeout(() => {
      if (highlight.parentNode) {
        const parent = highlight.parentNode
        while (highlight.firstChild) {
          parent.insertBefore(highlight.firstChild, highlight)
        }
        parent.removeChild(highlight)
      }
    }, 2000)
  } catch (e) {
    // 如果无法包裹（跨元素选择），忽略错误
    console.log('[BatchAnalysis] 无法添加高亮效果（可能是跨元素选择）')
  }
}

// 提取选中文字的上下文
const extractTextContext = (selectedText: string, container: HTMLElement) => {
  const fullText = container.innerText || ''
  const startIndex = fullText.indexOf(selectedText)
  
  if (startIndex === -1) {
    return {
      beforeContext: '',
      afterContext: '',
      fullText: fullText
    }
  }
  
  const endIndex = startIndex + selectedText.length
  const CONTEXT_LENGTH = 500
  
  return {
    beforeContext: fullText.substring(Math.max(0, startIndex - CONTEXT_LENGTH), startIndex),
    afterContext: fullText.substring(endIndex, Math.min(fullText.length, endIndex + CONTEXT_LENGTH)),
    fullText: fullText
  }
}

// 对话面板宽度调整
const startResize = (event: MouseEvent) => {
  isResizing.value = true
  startX.value = event.clientX
  startWidth.value = dialogPanelWidth.value
  
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  event.preventDefault()
}

const handleResize = (event: MouseEvent) => {
  if (!isResizing.value) return
  
  const deltaX = event.clientX - startX.value
  const newWidth = startWidth.value + deltaX
  
  // 限制宽度范围：300px - 800px
  if (newWidth >= 300 && newWidth <= 800) {
    dialogPanelWidth.value = newWidth
  }
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// ========== 图表编辑功能 ==========
// 从ReportDisplay打开图表编辑器
const handleEditChartFromReport = () => {
  if (currentReportDetail.value?.report_content?.html_charts) {
    // 关闭对话面板（如果打开）
    showDialogPanel.value = false
    // 打开编辑器
    editingChartHtml.value = currentReportDetail.value.report_content.html_charts
    editingChartTitle.value = currentReportDetail.value.sheet_name || '数据分析图表'
    showChartEditor.value = true
    console.log('[BatchAnalysis] 从报告显示区进入图表编辑模式')
  } else {
    ElMessage.warning('当前没有可编辑的图表')
  }
}

// 保存图表编辑
const handleChartEditorSave = (newChartHtml: string) => {
  if (currentReportDetail.value) {
    currentReportDetail.value.report_content.html_charts = newChartHtml
    ElMessage.success('图表已更新')
  }
  showChartEditor.value = false
}

// 取消图表编辑
const handleChartEditorCancel = () => {
  showChartEditor.value = false
}


// 生命周期
onMounted(async () => {
  // 检查路由参数，判断是否需要开始新会话
  const route = useRoute()
  const startNew = route.query.new === 'true'
  
  if (startNew) {
    // 从首页点击进入，清空所有状态，开始全新分析
    console.log('[BatchAnalysis] 开始新的批量分析会话')
    batchSessionId.value = null
    fileList.value = []
    batchReports.value = []
    batchStatus.value = 'idle'
    analysisRequest.value = ''
  }
  
  // 加载工作流配置
  await loadFunctionWorkflow()
  
  // 加载历史批量会话列表
  try {
    const response = await getBatchSessions({ page: 1, page_size: 20 })
    const batchResponse = response as unknown as ApiResponse<any>
    if (batchResponse.success && batchResponse.data) {
      operationStore.setBatchSessions(batchResponse.data.sessions)
    }
  } catch (error) {
    console.error('加载批量会话列表失败:', error)
  }
  
  // 添加文本选择监听
  document.addEventListener('mouseup', handleTextSelection)
})

onBeforeUnmount(() => {
  stopStatusPolling()
  // 移除文本选择监听
  document.removeEventListener('mouseup', handleTextSelection)
})
</script>

<style scoped lang="scss">
.batch-analysis-page {
  display: flex;
  height: 100vh;
  background: var(--apple-bg-gradient);
  
  .main-content {
    flex: 1;
    padding: var(--apple-space-2xl);
    overflow-y: auto;
    background: var(--apple-bg-primary);
    position: relative; // 为绝对定位的dialog-mode-layout提供定位上下文
    
    // 对话模式时，隐藏padding和overflow，让对话布局占满整个区域
    &:has(.dialog-mode-layout) {
      padding: 0;
      overflow: hidden;
    }
    
    .content-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: var(--apple-space-2xl);
      padding-bottom: var(--apple-space-2xl);
      border-bottom: 1px solid var(--apple-border-light);
      
      .header-text {
        h1 {
          margin: 0 0 var(--apple-space-sm) 0;
          font-size: var(--apple-font-2xl);
          font-weight: 600;
          color: var(--apple-text-primary);
          letter-spacing: -0.3px;
        }
        
        p {
          margin: 0;
          color: var(--apple-text-secondary);
          font-size: var(--apple-font-sm);
        }
      }
      
      .header-actions {
        display: flex;
        gap: var(--apple-space-md);
      }
    }
    
    .workflow-status-bar {
      margin-bottom: var(--apple-space-2xl);
    }
    
    .upload-section {
      margin-bottom: var(--apple-space-2xl);
      
      .excel-uploader {
        margin-bottom: var(--apple-space-xl);
      }
      
      .upload-status-card {
        margin-top: 24px;
        margin-bottom: 24px;
        animation: fadeIn 0.3s ease-in;
        
        .status-card {
          border: 2px solid var(--el-color-primary-light-8);
          background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
          
          .status-content {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 16px;
            
            .status-icon {
              font-size: 48px;
              color: var(--el-color-primary);
              
              .rotating {
                animation: rotate 2s linear infinite;
              }
            }
            
            .status-text {
              flex: 1;
              
              h3 {
                margin: 0 0 8px 0;
                font-size: 18px;
                font-weight: 600;
                color: var(--el-text-color-primary);
              }
              
              p {
                margin: 0;
                font-size: 14px;
                color: var(--el-text-color-secondary);
              }
            }
          }
          
          .status-progress {
            margin-top: 16px;
          }
          
          .splitting-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            padding: 16px;
            background: var(--el-color-primary-light-9);
            border-radius: 8px;
            font-size: 14px;
            color: var(--el-color-primary);
            
            .rotating {
              font-size: 20px;
              animation: rotate 2s linear infinite;
            }
          }
        }
      }
      
      .upload-success-card {
        margin-top: 24px;
        margin-bottom: 24px;
        animation: fadeIn 0.3s ease-in;
        
        .success-alert {
          border: 2px solid var(--el-color-success-light-8);
          background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
          
          .success-content {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            
            .success-icon {
              font-size: 32px;
              color: var(--el-color-success);
              flex-shrink: 0;
            }
            
            .success-text {
              flex: 1;
              
              h3 {
                margin: 0 0 8px 0;
                font-size: 16px;
                font-weight: 600;
                color: var(--el-text-color-primary);
              }
              
              p {
                margin: 0;
                font-size: 14px;
                line-height: 1.6;
                color: var(--el-text-color-regular);
                
                strong {
                  color: var(--el-color-success);
                  font-weight: 600;
                }
              }
            }
          }
        }
      }
      
      .upload-progress {
        margin-top: var(--apple-space-lg);
      }
      
      .input-section {
        margin-top: var(--apple-space-xl);
        padding: var(--apple-space-2xl);
        background: var(--apple-bg-primary);
        border-radius: var(--apple-radius-lg);
        border: 1px solid var(--apple-border-light);
        box-shadow: var(--apple-shadow-sm);
        
        .input-header {
          margin-bottom: var(--apple-space-lg);
          
          h3 {
            margin: 0;
            font-size: var(--apple-font-lg);
            font-weight: 600;
            color: var(--apple-text-primary);
            letter-spacing: -0.2px;
          }
        }
        
        .input-examples {
          margin-top: var(--apple-space-lg);
          display: flex;
          flex-wrap: wrap;
          gap: var(--apple-space-sm);
        }
        
        .example-tag {
          cursor: pointer;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .example-tag:hover {
          background: var(--apple-primary);
          color: #fff;
          transform: translateY(-1px);
        }
        
        .submit-section {
          margin-top: var(--apple-space-xl);
          text-align: center;
        }
      }
    }
    
    .progress-section {
      margin-bottom: 24px;
      
      .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .progress-details {
        display: flex;
        gap: 16px;
        margin-top: 16px;
        
        .detail-item {
          display: flex;
          align-items: center;
          gap: 8px;
        }
      }
    }
    
    .reports-tabs-container {
      margin-bottom: 24px;
    }
    
    .report-display-container {
      min-height: 400px;
    }
    
    .empty-state {
      margin-top: 60px;
    }
    
    // AI对话模式布局 - 占满整个主内容区（参考单文件分析设计）
    .dialog-mode-layout {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      display: flex;
      gap: 0;
      background: #ffffff;
      overflow: hidden;
      z-index: 10;
    }
    
    .dialog-left-panel {
      height: 100%;
      background: #f8f9fa;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }
    
    .dialog-right-panel {
      height: 100%;
      overflow-y: auto;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      flex: 1;
      padding: 40px;
    }
    
    .resize-handle {
      width: 8px;
      height: 100%;
      background: #f0f0f0;
      cursor: col-resize;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      flex-shrink: 0;
      transition: background-color 0.2s;
      
      &:hover {
        background: #e0e0e0;
      }
      
      &:active {
        background: #d0d0d0;
      }
      
      &:hover .resize-handle-line {
        background: #666;
      }
    }
    
    .resize-handle-line {
      width: 2px;
      height: 40px;
      background: #999;
      border-radius: 1px;
    }
    
    .resize-tooltip {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 4px 12px;
      border-radius: 4px;
      font-size: 12px;
      white-space: nowrap;
      pointer-events: none;
      z-index: 1000;
    }
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

