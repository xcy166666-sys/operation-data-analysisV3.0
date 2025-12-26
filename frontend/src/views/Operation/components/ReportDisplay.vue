<template>
  <div class="report-display">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>
    
    <!-- 报告内容 -->
    <div v-else-if="report && report.report_status === 'completed' && report.report_content" class="report-content">
      <!-- 报告文本（Markdown渲染） -->
      <div 
        class="report-text" 
        v-html="formattedReportText"
      ></div>
      
      <!-- HTML图表操作按钮（触发抽屉面板） -->
      <div class="chart-action-section" v-if="report.report_content.html_charts && report.report_content.html_charts.length > 0">
        <el-button 
          type="primary" 
          :icon="View"
          size="large"
          @click="openChartDrawer"
        >
          查看图表详情
        </el-button>
        <el-button 
          type="primary" 
          :icon="Download"
          size="large"
          @click="downloadChart"
        >
          下载图表
        </el-button>
        <el-button 
          type="primary" 
          :icon="Download"
          size="large"
          @click="handleDownload"
        >
          下载报告 (PDF)
        </el-button>
      </div>
      
      <!-- JSON图表显示（向后兼容，如果没有html_charts则使用旧方式） -->
      <div 
        class="report-charts" 
        v-else-if="report.report_content.charts && report.report_content.charts.length > 0"
      >
        <div 
          v-for="(_chart, index) in report.report_content.charts" 
          :key="index"
          class="chart-container"
        >
          <div :id="`chart-${report.id}-${index}`" class="chart"></div>
        </div>
      </div>
      
      <!-- 下载按钮（当没有HTML图表时显示） -->
      <div class="report-actions" v-if="!report.report_content.html_charts || report.report_content.html_charts.length === 0">
        <el-button 
          type="primary" 
          :icon="Download"
          size="large"
          @click="handleDownload"
        >
          下载报告 (PDF)
        </el-button>
      </div>
    </div>
    
    <!-- 图表抽屉组件 -->
    <ChartDrawer
      v-if="report"
      v-model="showChartDrawer"
      :html-content="report.report_content?.html_charts"
      :title="report.sheet_name || '图表详情'"
      :show-edit-button="isDialogMode"
      @close="handleChartDrawerClose"
      @edit-chart="handleEditChart"
    />
    
    <!-- 错误状态 -->
    <div v-else-if="report && (report as any).report_status === 'failed'" class="error-container">
      <el-alert
        :title="`报告生成失败: ${(report as any).error_message || '未知错误'}`"
        type="error"
        :closable="false"
        show-icon
      />
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-container">
      <el-empty description="暂无报告内容" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { marked } from 'marked'
import * as echarts from 'echarts'
import { Download, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { SheetReportDetail } from '@/api/operation'
import type { AxiosResponse } from 'axios'
import { downloadBatchReportPDF, downloadCustomBatchReportPDF } from '@/api/operation'
import ChartDrawer from './ChartDrawer.vue'

interface Props {
  report: SheetReportDetail | null
  loading?: boolean
  isCustomBatch?: boolean  // 是否为定制化批量分析
  isDialogMode?: boolean  // 是否在AI对话模式下
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'edit-chart': []
}>()

const chartInstances = ref<Map<number, echarts.ECharts>>(new Map())

// 图表抽屉状态
const showChartDrawer = ref(false)

// 格式化后的文本（响应式）
const formattedReportText = ref<string>('')

// 打开图表抽屉
const openChartDrawer = () => {
  if (props.report?.report_content?.html_charts) {
    showChartDrawer.value = true
  } else {
    ElMessage.warning('暂无图表内容')
  }
}

// 关闭图表抽屉
const handleChartDrawerClose = () => {
  showChartDrawer.value = false
}

// 编辑图表
const handleEditChart = () => {
  emit('edit-chart')
}

// 下载图表
const downloadChart = async () => {
  if (!props.report?.report_content?.html_charts) {
    ElMessage.warning('暂无图表内容')
    return
  }

  try {
    // 导出HTML文件
    const htmlContent = props.report.report_content.html_charts
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名（包含时间戳）
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    link.download = `图表_${timestamp}.html`
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success('图表已保存为HTML文件')
  } catch (error) {
    console.error('下载图表失败:', error)
    ElMessage.error('下载图表失败，请稍候再试')
  }
}

const formatReportText = async (text: string): Promise<string> => {
  if (!text) return ''
  
  try {
    marked.setOptions({
      breaks: true,
      gfm: true,
      async: false  // 强制同步模式
    })
    
    const result = marked.parse(text)
    // 处理可能的 Promise 返回值
    const html = (typeof result === 'object' && result !== null && 'then' in result) 
      ? await result 
      : String(result)
    const htmlWithoutTables = html.replace(/<table[\s\S]*?<\/table>/gi, '')
    return htmlWithoutTables
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return text.replace(/\n/g, '<br>')
  }
}

const renderCharts = async () => {
  // 如果已经有html_charts，不渲染ECharts
  if (props.report?.report_content?.html_charts) {
    console.log('[ReportDisplay] 使用HTML模式，跳过ECharts渲染')
    return
  }
  
  if (!props.report || !props.report.report_content?.charts || props.report.report_content.charts.length === 0) {
    return
  }
  
  await nextTick()
  
  props.report.report_content.charts.forEach((chart: any, index: number) => {
    const chartId = `chart-${props.report!.id}-${index}`
    const chartElement = document.getElementById(chartId)
    if (!chartElement) return
    
    const existingInstance = chartInstances.value.get(index)
    if (existingInstance) {
      existingInstance.dispose()
    }
    
    const chartInstance = echarts.init(chartElement)
    chartInstances.value.set(index, chartInstance)
    
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
    
    const resizeHandler = () => {
      chartInstance.resize()
    }
    window.addEventListener('resize', resizeHandler)
    ;(chartInstance as any)._resizeHandler = resizeHandler
  })
}

const cleanupCharts = () => {
  chartInstances.value.forEach((instance) => {
    const resizeHandler = (instance as any)._resizeHandler
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
    }
    instance.dispose()
  })
  chartInstances.value.clear()
}

watch(() => props.report, async (newReport) => {
  if (newReport && newReport.report_status === 'completed') {
    // 格式化文本
    if (newReport.report_content?.text) {
      formattedReportText.value = await formatReportText(newReport.report_content.text)
    } else {
      formattedReportText.value = ''
    }
    // 渲染图表
    cleanupCharts()
    await renderCharts()
  }
}, { immediate: true })

onMounted(() => {
  if (props.report && props.report.report_status === 'completed') {
    renderCharts()
  }
})

onBeforeUnmount(() => {
  cleanupCharts()
})

const exportChartsAsImages = async (): Promise<Array<{index: number, title: string, image: string}>> => {
  const chartImages: Array<{index: number, title: string, image: string}> = []
  
  for (const [index, chartInstance] of chartInstances.value.entries()) {
    try {
      const imageDataUrl = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff'
      })
      
      const chartData = props.report?.report_content?.charts?.[index] as any
      const chartTitle = chartData?.title || 
                        chartData?.config?.title?.text ||
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

const handleDownload = async () => {
  if (!props.report || !props.report.report_content) {
    ElMessage.warning('报告内容不存在')
    return
  }
  
  if (props.report.report_status !== 'completed') {
    ElMessage.warning('报告尚未完成，无法下载')
    return
  }
  
  try {
    ElMessage.info('正在准备下载，请稍候...')
    
    let chartImages: Array<{index: number, title: string, image: string}> = []
    
    // 1. 导出图表为图片
    if (props.report.report_content?.html_charts) {
      // 如果有 HTML 图表，使用 html2canvas 截图
      try {
        ElMessage.info('正在截图HTML图表，请稍候...')
        const html2canvas = (await import('html2canvas')).default
        
        // 创建一个iframe来渲染HTML图表（确保脚本正确执行）
        const tempIframe = document.createElement('iframe')
        tempIframe.style.position = 'absolute'
        tempIframe.style.left = '-9999px'
        tempIframe.style.top = '0'
        tempIframe.style.width = '1200px'
        tempIframe.style.height = '800px'
        tempIframe.style.border = 'none'
        tempIframe.sandbox.add('allow-scripts', 'allow-same-origin')
        document.body.appendChild(tempIframe)
        
        // 等待iframe加载
        await new Promise<void>((resolve) => {
          tempIframe.onload = () => resolve()
          tempIframe.srcdoc = props.report!.report_content!.html_charts!
        })
        
        // 等待iframe内容完全加载
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 获取iframe内容
        let targetElement: HTMLElement | null = null
        try {
          const iframeDoc = tempIframe.contentDocument || tempIframe.contentWindow?.document
          if (iframeDoc && iframeDoc.body) {
            targetElement = iframeDoc.body
            
            // 等待图表渲染完成（检查canvas元素或图表容器）
            let attempts = 0
            const maxAttempts = 20 // 最多等待10秒
            
            while (attempts < maxAttempts) {
              // 检查是否有canvas元素（ECharts等图表库会创建canvas）
              const canvases = targetElement.querySelectorAll('canvas')
              
              // 如果找到canvas或者等待时间足够长，认为图表已渲染
              if (canvases.length > 0 || attempts >= 10) {
                // 再等待一下确保图表完全绘制
                await new Promise(resolve => setTimeout(resolve, 1000))
                break
              }
              
              await new Promise(resolve => setTimeout(resolve, 500))
              attempts++
            }
            
            // 等待所有图片加载完成
            const images = targetElement.querySelectorAll('img')
            if (images.length > 0) {
              await Promise.all(
                Array.from(images).map((img: HTMLImageElement) => {
                  if (img.complete) {
                    return Promise.resolve(undefined)
                  }
                  return new Promise<void>((resolve) => {
                    img.onload = () => resolve()
                    img.onerror = () => resolve() // 即使失败也继续
                    setTimeout(() => resolve(), 3000) // 超时也继续
                  })
                })
              )
            }
            
            // 最后等待一下，确保所有内容都渲染完成
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        } catch (e) {
          console.warn('无法访问iframe内容，尝试截图iframe本身:', e)
          targetElement = tempIframe
        }
        
        if (!targetElement) {
          throw new Error('无法获取图表内容')
        }
        
        // 截图
        const canvas = await html2canvas(targetElement, {
          backgroundColor: '#ffffff',
          scale: 2,
          useCORS: true,
          logging: false,
          allowTaint: true,
          width: targetElement.scrollWidth || 1200,
          height: targetElement.scrollHeight || 800,
          windowWidth: targetElement.scrollWidth || 1200,
          windowHeight: targetElement.scrollHeight || 800
        })
        
        // 转换为 base64
        const imageDataUrl = canvas.toDataURL('image/png', 1.0)
        
        if (!imageDataUrl || imageDataUrl === 'data:,') {
          throw new Error('截图生成失败：图片数据为空')
        }
        
        chartImages.push({
          index: 0,
          title: '数据可视化图表',
          image: imageDataUrl
        })
        
        // 清理临时元素
        document.body.removeChild(tempIframe)
        ElMessage.success('图表截图成功')
      } catch (error) {
        console.error('HTML图表截图失败:', error)
        ElMessage.warning(`图表截图失败: ${error instanceof Error ? error.message : '未知错误'}，将生成不含图表的PDF`)
      }
    } else if (chartInstances.value.size > 0) {
      // 如果有 ECharts 实例，使用原有方法
      await new Promise(resolve => setTimeout(resolve, 1000))
      chartImages = await exportChartsAsImages()
    }
    
    // 2. 调用后端API，传递图表图片
    const response = props.isCustomBatch
      ? await downloadCustomBatchReportPDF(props.report.id, chartImages)
      : await downloadBatchReportPDF(props.report.id, chartImages)
    
    if (response.data instanceof Blob) {
      const axiosResponse = response as any as AxiosResponse
      const contentType = axiosResponse.headers?.['content-type'] || ''
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
      
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const reportTitle = props.report?.sheet_name || '数据分析报告'
      link.download = `${reportTitle}_${new Date().getTime()}.pdf`
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
</script>

<style scoped lang="scss">
.report-display {
  min-height: 400px;
  
  .loading-container {
    padding: 20px;
  }
  
  .report-content {
    .report-text {
      color: var(--notion-text-primary);
      line-height: 1.8;
      margin-bottom: 20px;
      
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
    
    /* 图表操作按钮区域 */
    .chart-action-section {
      margin-top: 20px;
      margin-bottom: 20px;
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
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
    
    .report-actions {
      margin-top: 24px;
      padding-top: 24px;
      border-top: 1px solid var(--notion-border);
    }
  }
  
  .error-container {
    padding: 20px;
  }
  
  .empty-container {
    padding: 40px;
    text-align: center;
  }
}
</style>
