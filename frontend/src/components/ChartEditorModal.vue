<template>
  <el-dialog
    v-model="visible"
    fullscreen
    :show-close="false"
    class="chart-editor-modal"
    :before-close="handleBeforeClose"
  >
    <!-- 顶部工具栏 -->
    <div class="editor-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="handleBack">
          返回报告
        </el-button>
        <span class="editor-title">图表编辑器 - {{ chartTitle }}</span>
      </div>
      <div class="header-right">
        <el-button @click="handleReset">重置</el-button>
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="isSaving">
          保存
        </el-button>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="editor-body">
      <!-- 左侧工具栏 -->
      <div class="editor-sidebar-left">
        <el-scrollbar>
          <el-collapse v-model="activeGroups">
            <!-- 图表类型 -->
            <el-collapse-item name="type" title="📊 图表类型">
              <el-radio-group v-model="chartType" @change="handleTypeChange" class="type-group">
                <el-radio label="bar">
                  <el-icon><Histogram /></el-icon>
                  柱状图
                </el-radio>
                <el-radio label="line">
                  <el-icon><TrendCharts /></el-icon>
                  折线图
                </el-radio>
                <el-radio label="pie">
                  <el-icon><PieChart /></el-icon>
                  饼图
                </el-radio>
              </el-radio-group>
            </el-collapse-item>

            <!-- 样式设置 -->
            <el-collapse-item name="style" title="🎨 样式设置">
              <div class="style-section">
                <el-button text @click="scrollToProperty('color')">
                  <el-icon><Brush /></el-icon>
                  颜色主题
                </el-button>
                <el-button text @click="scrollToProperty('display')">
                  <el-icon><View /></el-icon>
                  显示选项
                </el-button>
                <el-button text @click="scrollToProperty('size')">
                  <el-icon><FullScreen /></el-icon>
                  尺寸调整
                </el-button>
              </div>
            </el-collapse-item>

            <!-- AI助手 -->
            <el-collapse-item name="ai" title="🤖 AI助手">
              <div class="ai-helper">
                <p class="helper-tip">需要复杂的修改？让AI帮你！</p>
                <el-button type="primary" @click="openAIDialog" block>
                  <el-icon><ChatDotRound /></el-icon>
                  打开AI对话
                </el-button>
                <div class="ai-examples">
                  <p class="examples-title">AI可以帮你：</p>
                  <ul>
                    <li>添加渐变色效果</li>
                    <li>配置复杂动画</li>
                    <li>自定义样式</li>
                    <li>数据处理</li>
                  </ul>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-scrollbar>
      </div>

      <!-- 中间预览区 -->
      <div class="editor-preview">
        <div class="preview-toolbar">
          <el-button-group>
            <el-button :icon="ZoomIn" @click="handleZoomIn" size="small">放大</el-button>
            <el-button :icon="ZoomOut" @click="handleZoomOut" size="small">缩小</el-button>
            <el-button :icon="RefreshRight" @click="handleResetZoom" size="small">重置</el-button>
          </el-button-group>
          
          <el-tag type="info">缩放: {{ zoomLevel }}%</el-tag>
          
          <el-tag v-if="hasUnsavedChanges" type="warning">
            <el-icon><Warning /></el-icon>
            未保存
          </el-tag>
          
          <el-button 
            type="primary" 
            @click="handleApplyLocal"
            :loading="isApplying"
          >
            <el-icon><Check /></el-icon>
            应用修改 ⚡
          </el-button>
        </div>
        
        <div class="preview-container" ref="previewContainer">
          <div class="chart-wrapper" :style="{ transform: `scale(${zoomLevel / 100})` }">
            <iframe
              ref="chartPreview"
              :key="iframeKey"
              :srcdoc="currentChartHtml"
              frameborder="0"
              sandbox="allow-scripts allow-same-origin"
              class="chart-iframe"
            ></iframe>
          </div>
        </div>
      </div>

      <!-- 右侧属性面板 -->
      <div class="editor-sidebar-right">
        <el-scrollbar ref="propertyScrollbar">
          <!-- 颜色主题 -->
          <div class="property-section" data-property="color">
            <h4>🎨 颜色主题</h4>
            <div class="color-presets">
              <div
                v-for="color in colorPresets"
                :key="color.value"
                class="color-item"
                :class="{ active: selectedColor === color.value }"
                :style="{ background: color.value }"
                :title="color.name"
                @click="handleColorChange(color.value)"
              >
                <el-icon v-if="selectedColor === color.value" class="check-icon">
                  <Check />
                </el-icon>
              </div>
            </div>
            <el-input
              v-model="customColor"
              placeholder="自定义颜色 #409eff"
              @change="handleCustomColorChange"
              class="custom-color-input"
            >
              <template #prepend>自定义</template>
            </el-input>
          </div>

          <!-- 显示选项 -->
          <div class="property-section" data-property="display">
            <h4>👁️ 显示选项</h4>
            <div class="checkbox-group">
              <el-checkbox v-model="showDataLabel" @change="handleOptionChange">
                数据标签
              </el-checkbox>
              <el-checkbox v-model="showLegend" @change="handleOptionChange">
                图例
              </el-checkbox>
              <el-checkbox v-model="showGrid" @change="handleOptionChange">
                网格线
              </el-checkbox>
              <el-checkbox v-model="showTooltip" @change="handleOptionChange">
                提示框
              </el-checkbox>
            </div>
          </div>

          <!-- 尺寸调整 -->
          <div class="property-section" data-property="size">
            <h4>📏 尺寸调整</h4>
            <el-form label-width="60px" size="small">
              <el-form-item label="宽度">
                <el-input-number
                  v-model="chartWidth"
                  :min="400"
                  :max="2000"
                  :step="50"
                  @change="handleSizeChange"
                />
                <span class="unit">px</span>
              </el-form-item>
              <el-form-item label="高度">
                <el-input-number
                  v-model="chartHeight"
                  :min="300"
                  :max="1200"
                  :step="50"
                  @change="handleSizeChange"
                />
                <span class="unit">px</span>
              </el-form-item>
            </el-form>
          </div>

          <!-- 标题设置 -->
          <div class="property-section">
            <h4>📝 标题设置</h4>
            <el-input
              v-model="chartTitleText"
              placeholder="图表标题"
              @change="handleTitleChange"
              class="title-input"
            />
            <el-input
              v-model="chartSubtitle"
              placeholder="副标题（可选）"
              @change="handleTitleChange"
              class="title-input"
            />
          </div>

          <!-- AI助手快捷入口 -->
          <div class="property-section ai-section">
            <h4>🤖 AI助手</h4>
            <p class="ai-tip">需要更复杂的修改？</p>
            <el-button type="primary" block @click="openAIDialog">
              打开AI对话
            </el-button>
          </div>
        </el-scrollbar>
      </div>
    </div>

    <!-- AI对话面板（可选） -->
    <el-drawer
      v-model="showAIDialog"
      title="AI助手"
      size="500px"
      direction="rtl"
    >
      <div class="ai-dialog-content">
        <el-alert
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 16px;"
        >
          <template #title>
            <span style="font-size: 13px;">AI可以帮你完成复杂的图表修改</span>
          </template>
        </el-alert>

        <el-input
          v-model="aiInstruction"
          type="textarea"
          :rows="6"
          placeholder="描述你想要的修改，例如：&#10;• 添加从蓝色到紫色的渐变效果&#10;• 配置平滑曲线动画&#10;• 自定义tooltip样式"
          class="ai-input"
        />

        <div class="ai-actions">
          <el-button @click="showAIDialog = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleAIModify"
            :loading="isAIProcessing"
          >
            <el-icon><MagicStick /></el-icon>
            AI修改（需要10-15秒）
          </el-button>
        </div>
      </div>
    </el-drawer>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Check,
  Warning,
  ZoomIn,
  ZoomOut,
  RefreshRight,
  Histogram,
  TrendCharts,
  PieChart,
  Brush,
  View,
  FullScreen,
  ChatDotRound,
  MagicStick
} from '@element-plus/icons-vue'
import { ChartEditor } from '@/utils/chartEditor'
import { modifyChart, type ChartModificationRequest } from '@/api/chart'

interface Props {
  modelValue: boolean
  chartHtml: string
  chartTitle: string
  sessionId?: number
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  chartTitle: '图表'
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'save': [html: string]
  'cancel': []
}>()

// 编辑器实例
const editor = new ChartEditor()

// 对话框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 当前图表HTML
const currentChartHtml = ref(props.chartHtml)
const originalChartHtml = ref(props.chartHtml)
const confirmedChartHtml = ref(props.chartHtml) // 已确认的版本（点击"应用修改"后）
const iframeKey = ref(0) // 用于强制刷新iframe

// 折叠面板激活项
const activeGroups = ref(['type', 'style'])

// 图表配置
const chartType = ref('bar')
const selectedColor = ref('#409eff')
const customColor = ref('')
const showDataLabel = ref(true)
const showLegend = ref(true)
const showGrid = ref(true)
const showTooltip = ref(true)
const chartWidth = ref(800)
const chartHeight = ref(600)
const chartTitleText = ref('')
const chartSubtitle = ref('')

// 颜色预设
const colorPresets = [
  { name: '蓝色', value: '#409eff' },
  { name: '绿色', value: '#67c23a' },
  { name: '红色', value: '#f56c6c' },
  { name: '橙色', value: '#e6a23c' },
  { name: '紫色', value: '#9c27b0' },
  { name: '青色', value: '#00bcd4' },
  { name: '粉色', value: '#e91e63' },
  { name: '灰色', value: '#909399' }
]

// 缩放级别
const zoomLevel = ref(100)
const previewContainer = ref<HTMLElement | null>(null)
const chartPreview = ref<HTMLIFrameElement | null>(null)
const propertyScrollbar = ref<any>(null)

// 状态标志
const hasUnsavedChanges = ref(false)
const isSaving = ref(false)
const isApplying = ref(false)
const isAIProcessing = ref(false)

// AI对话
const showAIDialog = ref(false)
const aiInstruction = ref('')

// 初始化配置
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    // 打开时初始化
    currentChartHtml.value = props.chartHtml
    originalChartHtml.value = props.chartHtml
    confirmedChartHtml.value = props.chartHtml // 初始化已确认版本
    iframeKey.value++ // 强制iframe重新渲染
    hasUnsavedChanges.value = false
    
    // 解析当前配置
    const summary = editor.getConfigSummary(props.chartHtml)
    if (summary) {
      chartType.value = summary.type
      selectedColor.value = summary.color
      showDataLabel.value = summary.hasDataLabel
      showLegend.value = summary.hasLegend
      showGrid.value = summary.hasGrid
    }
  }
}, { immediate: true })

// 本地修改 - 改颜色 ⚡ (实时预览)
const handleColorChange = (color: string) => {
  selectedColor.value = color
  customColor.value = color
  markAsChanged()
  // 立即应用预览
  applyPreview()
}

const handleCustomColorChange = () => {
  if (customColor.value && /^#[0-9A-Fa-f]{6}$/.test(customColor.value)) {
    selectedColor.value = customColor.value
    markAsChanged()
    // 立即应用预览
    applyPreview()
  } else if (customColor.value) {
    ElMessage.warning('请输入正确的颜色代码，如 #409eff')
  }
}

// 本地修改 - 换类型 ⚡ (实时预览)
const handleTypeChange = () => {
  markAsChanged()
  // 立即应用预览
  applyPreview()
}

// 本地修改 - 显示选项 ⚡ (实时预览)
const handleOptionChange = () => {
  markAsChanged()
  // 立即应用预览
  applyPreview()
}

// 本地修改 - 尺寸调整 ⚡ (实时预览)
const handleSizeChange = () => {
  markAsChanged()
  // 立即应用预览
  applyPreview()
}

// 本地修改 - 标题修改 ⚡ (实时预览)
const handleTitleChange = () => {
  markAsChanged()
  // 立即应用预览
  applyPreview()
}

// 实时预览修改（草稿模式）
const applyPreview = () => {
  try {
    // 批量应用所有修改到预览
    currentChartHtml.value = editor.applyMultipleChanges(
      confirmedChartHtml.value, // 基于已确认的版本
      {
        color: selectedColor.value,
        type: chartType.value,
        options: {
          showDataLabel: showDataLabel.value,
          showLegend: showLegend.value,
          showGrid: showGrid.value,
          showTooltip: showTooltip.value
        },
        size: {
          width: chartWidth.value,
          height: chartHeight.value
        },
        title: chartTitleText.value,
        subtitle: chartSubtitle.value
      }
    )
    
    iframeKey.value++ // 强制iframe重新渲染
  } catch (error: any) {
    console.error('[ChartEditor] 预览失败:', error)
  }
}

// 应用本地修改 ⚡ (确认修改)
const handleApplyLocal = () => {
  isApplying.value = true
  
  try {
    console.log('[ChartEditor] 确认修改')
    
    // 将当前预览版本设为已确认版本
    confirmedChartHtml.value = currentChartHtml.value
    
    ElMessage.success('修改已确认 ⚡')
  } catch (error: any) {
    console.error('[ChartEditor] 确认修改失败:', error)
    ElMessage.error('确认修改失败，请重试')
  } finally {
    isApplying.value = false
  }
}

// AI修改 🤖
const openAIDialog = () => {
  showAIDialog.value = true
  aiInstruction.value = ''
}

const handleAIModify = async () => {
  if (!aiInstruction.value.trim()) {
    ElMessage.warning('请输入修改指令')
    return
  }

  if (!props.sessionId) {
    ElMessage.error('当前没有会话，无法使用AI修改')
    return
  }

  isAIProcessing.value = true

  try {
    const request: ChartModificationRequest = {
      session_id: props.sessionId,
      current_html: currentChartHtml.value,
      ai_instruction: aiInstruction.value
    }

    const response = await modifyChart(request)

    if (response.data && response.data.html) {
      currentChartHtml.value = response.data.html
      iframeKey.value++ // 强制iframe重新渲染
      hasUnsavedChanges.value = true
      showAIDialog.value = false
      ElMessage.success('AI修改成功')
    }
  } catch (error: any) {
    console.error('[ChartEditor] AI修改失败:', error)
    ElMessage.error(error.message || 'AI修改失败，请重试')
  } finally {
    isAIProcessing.value = false
  }
}

// 缩放控制
const handleZoomIn = () => {
  if (zoomLevel.value < 200) {
    zoomLevel.value += 10
  }
}

const handleZoomOut = () => {
  if (zoomLevel.value > 50) {
    zoomLevel.value -= 10
  }
}

const handleResetZoom = () => {
  zoomLevel.value = 100
}

// 滚动到属性
const scrollToProperty = (property: string) => {
  nextTick(() => {
    const element = document.querySelector(`[data-property="${property}"]`)
    if (element && propertyScrollbar.value) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

// 标记为已修改
const markAsChanged = () => {
  hasUnsavedChanges.value = true
}

// 重置
const handleReset = () => {
  ElMessageBox.confirm(
    '确定要重置所有修改吗？',
    '确认重置',
    {
      confirmButtonText: '重置',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    currentChartHtml.value = originalChartHtml.value
    confirmedChartHtml.value = originalChartHtml.value // 重置已确认版本
    iframeKey.value++ // 强制iframe重新渲染
    hasUnsavedChanges.value = false
    
    // 重新解析配置
    const summary = editor.getConfigSummary(originalChartHtml.value)
    if (summary) {
      chartType.value = summary.type
      selectedColor.value = summary.color
      showDataLabel.value = summary.hasDataLabel
      showLegend.value = summary.hasLegend
      showGrid.value = summary.hasGrid
    }
    
    ElMessage.success('已重置')
  }).catch(() => {
    // 取消
  })
}

// 返回/取消
const handleBack = () => {
  handleCancel()
}

const handleCancel = () => {
  if (hasUnsavedChanges.value) {
    ElMessageBox.confirm(
      '你有未保存的修改，确定要放弃吗？',
      '确认',
      {
        confirmButtonText: '放弃',
        cancelButtonText: '继续编辑',
        type: 'warning'
      }
    ).then(() => {
      emit('cancel')
      visible.value = false
    }).catch(() => {
      // 继续编辑
    })
  } else {
    emit('cancel')
    visible.value = false
  }
}

const handleBeforeClose = (done: () => void) => {
  handleCancel()
}

// 保存
const handleSave = () => {
  isSaving.value = true
  
  try {
    // 保存已确认的版本（不是当前预览版本）
    emit('save', confirmedChartHtml.value)
    hasUnsavedChanges.value = false
    visible.value = false
    ElMessage.success('图表已保存')
  } catch (error: any) {
    console.error('[ChartEditor] 保存失败:', error)
    ElMessage.error('保存失败，请重试')
  } finally {
    isSaving.value = false
  }
}
</script>


<style scoped lang="scss">
.chart-editor-modal {
  :deep(.el-dialog__body) {
    padding: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  z-index: 10;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .editor-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  .header-right {
    display: flex;
    gap: 12px;
  }
}

.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

// 左侧工具栏
.editor-sidebar-left {
  width: 240px;
  background: #f5f7fa;
  border-right: 1px solid #e0e0e0;
  overflow: hidden;

  :deep(.el-scrollbar__view) {
    padding: 16px;
  }

  .el-collapse {
    border: none;
    background: transparent;

    :deep(.el-collapse-item__header) {
      background: transparent;
      border: none;
      font-weight: 600;
      color: #303133;
      padding: 8px 0;
    }

    :deep(.el-collapse-item__wrap) {
      background: transparent;
      border: none;
    }

    :deep(.el-collapse-item__content) {
      padding: 12px 0;
    }
  }

  .type-group {
    display: flex;
    flex-direction: column;
    gap: 8px;

    .el-radio {
      margin: 0;
      padding: 8px 12px;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      transition: all 0.3s;

      &:hover {
        border-color: #409eff;
        background: #ecf5ff;
      }

      :deep(.el-radio__label) {
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .el-radio.is-checked {
      border-color: #409eff;
      background: #ecf5ff;
    }
  }

  .style-section {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .el-button {
      justify-content: flex-start;
      padding: 8px 12px;

      :deep(.el-icon) {
        margin-right: 8px;
      }
    }
  }

  .ai-helper {
    .helper-tip {
      font-size: 13px;
      color: #606266;
      margin-bottom: 12px;
    }

    .ai-examples {
      margin-top: 16px;
      padding: 12px;
      background: #fff;
      border-radius: 4px;
      border: 1px solid #e0e0e0;

      .examples-title {
        font-size: 12px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 8px;
      }

      ul {
        margin: 0;
        padding-left: 20px;

        li {
          font-size: 12px;
          color: #606266;
          line-height: 1.8;
        }
      }
    }
  }
}

// 中间预览区
.editor-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  overflow: hidden;

  .preview-toolbar {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 24px;
    background: #fff;
    border-bottom: 1px solid #e0e0e0;
  }

  .preview-container {
    flex: 1;
    overflow: auto;
    padding: 24px;
    display: flex;
    align-items: center;
    justify-content: center;

    .chart-wrapper {
      transform-origin: center center;
      transition: transform 0.3s ease;

      .chart-iframe {
        width: 100%;
        min-width: 800px;
        min-height: 600px;
        background: #fff;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      }
    }
  }

  .preview-actions {
    padding: 16px 24px;
    background: #fff;
    border-top: 1px solid #e0e0e0;
    display: flex;
    justify-content: center;
  }
}

// 右侧属性面板
.editor-sidebar-right {
  width: 320px;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  overflow: hidden;

  :deep(.el-scrollbar__view) {
    padding: 16px;
  }

  .property-section {
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    h4 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 12px 0;
    }

    .color-presets {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-bottom: 12px;

      .color-item {
        width: 100%;
        aspect-ratio: 1;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        border: 2px solid transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;

        &:hover {
          transform: scale(1.1);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }

        &.active {
          border-color: #303133;
          box-shadow: 0 0 0 2px #fff, 0 0 0 4px #409eff;

          .check-icon {
            color: #fff;
            font-size: 20px;
            filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
          }
        }
      }
    }

    .custom-color-input {
      :deep(.el-input-group__prepend) {
        background: #f5f7fa;
      }
    }

    .checkbox-group {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .el-form-item {
      margin-bottom: 16px;

      .unit {
        margin-left: 8px;
        color: #909399;
        font-size: 12px;
      }
    }

    .title-input {
      margin-bottom: 12px;
    }

    &.ai-section {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 16px;
      border-radius: 8px;
      border: none;

      h4 {
        color: #fff;
      }

      .ai-tip {
        color: rgba(255, 255, 255, 0.9);
        font-size: 13px;
        margin-bottom: 12px;
      }
    }
  }
}

// AI对话面板
.ai-dialog-content {
  .ai-input {
    margin: 16px 0;

    :deep(.el-textarea__inner) {
      font-family: inherit;
      line-height: 1.6;
    }
  }

  .ai-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}

// 动画
.chart-editor-modal {
  :deep(.el-dialog) {
    animation: modalZoomIn 0.3s ease-out;
  }
}

@keyframes modalZoomIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
