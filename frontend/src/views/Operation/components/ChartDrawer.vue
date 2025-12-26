<!-- frontend/src/views/Operation/components/ChartDrawer.vue -->
<template>
  <el-drawer
    v-model="visible"
    title="图表详情"
    :size="drawerSize"
    direction="rtl"
    :before-close="handleClose"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
    class="chart-drawer"
  >
    <template #header>
      <div class="drawer-header">
        <h3>{{ title }}</h3>
        <div class="header-actions">
          <el-dropdown 
            trigger="click" 
            @command="handleDownloadCommand"
            :disabled="!htmlContent || isLoading"
          >
            <el-button 
              :icon="Download" 
              size="small"
              :loading="isDownloading"
            >
              下载图表
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="screenshot">截图保存 (PNG)</el-dropdown-item>
                <el-dropdown-item command="html">导出HTML文件</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button 
            :icon="FullScreen" 
            size="small"
            @click="handleFullscreen"
            :disabled="!htmlContent || isLoading"
          >
            全屏
          </el-button>
        </div>
      </div>
    </template>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="chart-loading">
      <el-skeleton :rows="5" animated />
      <div class="loading-text">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在加载图表内容...</span>
      </div>
    </div>
    
    <!-- 图表内容 -->
    <div class="chart-content" v-else-if="htmlContent">
      <!-- HTML错误提示 -->
      <div v-if="htmlError" class="html-error-banner">
        <el-alert
          type="warning"
          :closable="false"
          show-icon
        >
          <template #title>
            <div style="display: flex; flex-direction: column; gap: 8px;">
              <span>图表HTML代码存在错误，可能无法正常显示</span>
              <span style="font-size: 12px; color: #909399;">错误信息: {{ htmlError }}</span>
              <el-button 
                size="small" 
                type="primary" 
                text
                @click="showHtmlSource = !showHtmlSource"
              >
                {{ showHtmlSource ? '隐藏' : '查看' }}HTML源代码
              </el-button>
            </div>
          </template>
        </el-alert>
        <div v-if="showHtmlSource" class="html-source-viewer">
          <pre>{{ htmlContent }}</pre>
        </div>
      </div>
      
      <!-- 图表容器，带悬浮式编辑按钮 -->
      <div class="chart-iframe-container">
        <!-- 使用iframe渲染HTML内容（更安全，确保script执行） -->
        <iframe
          :srcdoc="htmlContent"
          class="chart-html-iframe"
          frameborder="0"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
          allow="fullscreen"
          ref="chartContentRef"
          @load="handleIframeLoad"
          @error="handleIframeError"
        ></iframe>
        
        <!-- 悬浮式编辑按钮 - 只在AI编辑模式下显示 -->
        <div v-if="showEditButton" class="chart-edit-overlay" @click="handleEditChart">
          <div class="edit-button">
            <el-icon><Edit /></el-icon>
            <span>编辑图表</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="chart-empty">
      <el-empty description="暂无图表内容" />
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElDrawer, ElButton, ElEmpty, ElDropdown, ElDropdownMenu, ElDropdownItem, ElSkeleton, ElIcon, ElMessage } from 'element-plus'
import { Download, FullScreen, Loading, Edit } from '@element-plus/icons-vue'

interface Props {
  modelValue: boolean
  htmlContent?: string
  title?: string
  showEditButton?: boolean  // 是否显示编辑按钮，默认false
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  htmlContent: '',
  title: '图表详情',
  showEditButton: false  // 默认不显示编辑按钮
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'close': []
  'edit-chart': []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const drawerSize = computed(() => {
  // 响应式尺寸：桌面端50%，平板40%，移动端80%
  if (typeof window !== 'undefined') {
    if (window.innerWidth < 768) {
      return '80%'
    } else if (window.innerWidth < 1024) {
      return '40%'
    } else {
      return '50%'
    }
  }
  return '50%' // 默认值
})

const chartContentRef = ref<HTMLIFrameElement | null>(null)
const isLoading = ref(false)
const isDownloading = ref(false)
const htmlError = ref<string>('')
const showHtmlSource = ref(false)
let loadTimeout: NodeJS.Timeout | null = null

// iframe加载错误处理
const handleIframeError = (event: Event) => {
  console.error('[ChartDrawer] iframe加载错误:', event)
  
  // 清除超时定时器
  if (loadTimeout) {
    clearTimeout(loadTimeout)
    loadTimeout = null
  }
  
  // 隐藏加载状态
  isLoading.value = false
  ElMessage.error('图表加载失败，请稍候再试')
}

// iframe加载完成处理
const handleIframeLoad = () => {
  console.log('[ChartDrawer] iframe加载完成')
  
  // 清除超时定时器
  if (loadTimeout) {
    clearTimeout(loadTimeout)
    loadTimeout = null
  }
  
  // 延迟一点时间确保内容渲染完成
  setTimeout(() => {
    isLoading.value = false
    console.log('[ChartDrawer] 加载状态已设置为false')
  }, 200)
  
  // 检查iframe中的JavaScript错误
  if (chartContentRef.value) {
    try {
      const iframe = chartContentRef.value
      const iframeWindow = iframe.contentWindow
      
      if (iframeWindow) {
        // 监听iframe中的错误
        iframeWindow.addEventListener('error', (event: ErrorEvent) => {
          console.error('[ChartDrawer] iframe中的JavaScript错误:', event.message)
          htmlError.value = event.message || '图表代码执行错误'
        })
        
        // 监听未捕获的Promise错误
        iframeWindow.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
          console.error('[ChartDrawer] iframe中的Promise错误:', event.reason)
          htmlError.value = String(event.reason) || '图表代码执行错误'
        })
      }
      
      // 尝试调整iframe高度
      const iframeDoc = iframe.contentDocument || iframeWindow?.document
      if (iframeDoc && iframeDoc.body) {
        setTimeout(() => {
          const height = Math.max(
            iframeDoc.body.scrollHeight,
            iframeDoc.documentElement.scrollHeight,
            600
          )
          iframe.style.height = `${height}px`
          console.log('[ChartDrawer] iframe高度已调整:', height)
        }, 300)
      }
    } catch (e) {
      console.warn('[ChartDrawer] 无法访问iframe内容（可能跨域）:', e)
      // 使用固定高度
      if (chartContentRef.value) {
        chartContentRef.value.style.height = '800px'
      }
    }
  }
}

// 监听HTML内容变化，显示加载状态
watch(() => props.htmlContent, async (newContent) => {
  console.log('[ChartDrawer] HTML内容变化:', {
    hasContent: !!newContent,
    contentLength: newContent?.length || 0,
    contentPreview: newContent?.substring(0, 200) || '空'
  })
  
  // 重置错误状态
  htmlError.value = ''
  showHtmlSource.value = false
  
  // 清除之前的超时定时器
  if (loadTimeout) {
    clearTimeout(loadTimeout)
    loadTimeout = null
  }
  
  if (newContent && newContent.length > 0) {
    isLoading.value = true
    console.log('[ChartDrawer] HTML内容存在，显示加载状态，长度:', newContent.length)
    
    // 等待DOM更新
    await nextTick()
    
    // 设置超时机制：如果3秒内iframe没有触发load事件，自动隐藏加载状态
    loadTimeout = setTimeout(() => {
      console.warn('[ChartDrawer] iframe加载超时，自动隐藏加载状态')
      isLoading.value = false
      loadTimeout = null
      
      // 如果iframe存在，设置固定高度
      if (chartContentRef.value) {
        chartContentRef.value.style.height = '800px'
      }
    }, 3000)
  } else {
    isLoading.value = false
    console.warn('[ChartDrawer] HTML内容为空或不存在')
  }
}, { immediate: true })

// 监听抽屉打开状态，重置加载状态
watch(() => props.modelValue, (isOpen) => {
  if (isOpen && props.htmlContent) {
    console.log('[ChartDrawer] 抽屉打开，HTML内容存在，长度:', props.htmlContent.length)
    // 不在这里设置 isLoading，让 watch htmlContent 来处理
  } else if (!isOpen) {
    // 抽屉关闭时，清除超时定时器
    if (loadTimeout) {
      clearTimeout(loadTimeout)
      loadTimeout = null
    }
  }
})

// 关闭面板
const handleClose = () => {
  visible.value = false
  emit('close')
}

// 下载命令处理
const handleDownloadCommand = async (command: string) => {
  if (command === 'screenshot') {
    await downloadScreenshot()
  } else if (command === 'html') {
    downloadHTML()
  }
}

// 截图下载
const downloadScreenshot = async () => {
  if (!chartContentRef.value) {
    ElMessage.warning('图表内容未加载完成，请稍候再试')
    return
  }

  // 动态导入 html2canvas
  let html2canvas: any
  try {
    const module = await import('html2canvas')
    html2canvas = module.default
  } catch (error) {
    console.error('加载 html2canvas 失败:', error)
    ElMessage.error('截图功能暂不可用，请刷新页面重试')
    return
  }

  isDownloading.value = true
  try {
    ElMessage.info('正在生成截图，请稍候...')
    
    // 从iframe中获取内容进行截图
    const iframe = chartContentRef.value
    let targetElement: HTMLElement | null = null
    
    try {
      const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
      if (iframeDoc && iframeDoc.body) {
        targetElement = iframeDoc.body
      }
    } catch (e) {
      console.warn('无法访问iframe内容，尝试截图iframe本身:', e)
      targetElement = iframe
    }
    
    if (!targetElement) {
      ElMessage.error('无法获取图表内容')
      isDownloading.value = false
      return
    }
    
    // 使用html2canvas截图
    const canvas = await html2canvas(targetElement, {
      backgroundColor: '#ffffff',
      scale: 2, // 提高清晰度
      useCORS: true,
      logging: false,
      allowTaint: true,
      width: targetElement.scrollWidth,
      height: targetElement.scrollHeight
    })
    
    // 转换为Blob并下载
    canvas.toBlob((blob: Blob | null) => {
      if (!blob) {
        ElMessage.error('截图生成失败')
        isDownloading.value = false
        return
      }
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `图表截图_${new Date().getTime()}.png`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      ElMessage.success('截图已保存')
      isDownloading.value = false
    }, 'image/png', 1.0)
  } catch (error) {
    console.error('截图失败:', error)
    ElMessage.error('截图生成失败，请稍候再试')
    isDownloading.value = false
  }
}

// 导出HTML文件
const downloadHTML = () => {
  if (!props.htmlContent) {
    ElMessage.warning('没有可导出的HTML内容')
    return
  }

  try {
    const blob = new Blob([props.htmlContent], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `图表_${new Date().getTime()}.html`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success('HTML文件已保存')
  } catch (error) {
    console.error('导出HTML失败:', error)
    ElMessage.error('导出HTML文件失败')
  }
}

// 全屏显示
const handleFullscreen = () => {
  // 实现全屏逻辑
  if (chartContentRef.value) {
    if (chartContentRef.value.requestFullscreen) {
      chartContentRef.value.requestFullscreen()
    } else if ((chartContentRef.value as any).webkitRequestFullscreen) {
      (chartContentRef.value as any).webkitRequestFullscreen()
    } else if ((chartContentRef.value as any).mozRequestFullScreen) {
      (chartContentRef.value as any).mozRequestFullScreen()
    } else if ((chartContentRef.value as any).msRequestFullscreen) {
      (chartContentRef.value as any).msRequestFullscreen()
    }
  }
}

// 编辑图表
const handleEditChart = () => {
  emit('edit-chart')
}

// 监听窗口大小变化，调整抽屉尺寸
if (typeof window !== 'undefined') {
  watch(() => window.innerWidth, () => {
    // drawerSize是computed，会自动更新
  }, { immediate: true })
}
</script>

<style scoped lang="scss">
.chart-drawer {
  :deep(.el-drawer__body) {
    padding: 0;
    overflow: auto;
  }
  
  :deep(.el-drawer) {
    box-shadow: -4px 0 20px rgba(0, 0, 0, 0.15);
  }
  
  :deep(.el-drawer__header) {
    padding: 20px;
    border-bottom: 1px solid var(--el-border-color-light);
    margin-bottom: 0;
  }
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }
  
  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.chart-content {
  width: 100%;
  height: 100%;
  overflow: auto;
  padding: 0;
  background: #fff;
  
  .chart-iframe-container {
    position: relative;
    width: 100%;
    cursor: pointer;
  }
  
  .chart-iframe-container:hover .chart-edit-overlay {
    opacity: 1;
  }
  
  .chart-html-iframe {
    width: 100%;
    min-height: 800px;
    height: auto;
    border: none;
    display: block;
    background: white;
  }
  
  /* 悬浮式编辑遮罩 */
  .chart-edit-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
    backdrop-filter: blur(2px);
    z-index: 10;
  }
  
  .edit-button {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 16px 32px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 50px;
    font-size: 16px;
    font-weight: 600;
    color: #667eea;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
    cursor: pointer;
  }
  
  .edit-button:hover {
    background: #ffffff;
    transform: scale(1.05);
    box-shadow: 0 6px 30px rgba(102, 126, 234, 0.4);
  }
  
  .edit-button .el-icon {
    font-size: 20px;
  }
}

.chart-loading {
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  
  .loading-text {
    margin-top: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--el-text-color-secondary);
    font-size: 14px;
    
    .el-icon {
      font-size: 18px;
      animation: rotating 2s linear infinite;
    }
  }
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

.html-error-banner {
  padding: 16px;
  background: #fff6f0;
  border-bottom: 1px solid #ffd4a3;
}

.html-source-viewer {
  margin-top: 12px;
  max-height: 300px;
  overflow: auto;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  
  pre {
    margin: 0;
    padding: 12px;
    font-size: 12px;
    font-family: 'Courier New', monospace;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
}

// 响应式适配
@media (max-width: 768px) {
  .chart-drawer {
    :deep(.el-drawer) {
      width: 90% !important;
    }
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .chart-drawer {
    :deep(.el-drawer) {
      width: 50% !important;
    }
  }
}

@media (min-width: 1025px) {
  .chart-drawer {
    :deep(.el-drawer) {
      width: 50% !important;
    }
  }
}
</style>

