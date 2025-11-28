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
        v-html="formatReportText(report.report_content.text || '')"
      ></div>
      
      <!-- 图表 -->
      <div 
        class="report-charts" 
        v-if="report.report_content.charts && report.report_content.charts.length > 0"
      >
        <div 
          v-for="(chart, index) in report.report_content.charts" 
          :key="index"
          class="chart-container"
        >
          <div :id="`chart-${report.id}-${index}`" class="chart"></div>
        </div>
      </div>
      
      <!-- 下载按钮 -->
      <div class="report-actions">
        <el-button 
          type="primary" 
          :icon="Download"
          @click="handleDownload"
        >
          下载报告 (PDF)
        </el-button>
      </div>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="report && report.report_status === 'failed'" class="error-container">
      <el-alert
        :title="`报告生成失败: ${report.error_message || '未知错误'}`"
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
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { SheetReportDetail } from '@/api/operation'
import { downloadBatchReportPDF, downloadCustomBatchReportPDF } from '@/api/operation'

interface Props {
  report: SheetReportDetail | null
  loading?: boolean
  isCustomBatch?: boolean  // 是否为定制化批量分析
}

const props = defineProps<Props>()

const chartInstances = ref<Map<number, echarts.ECharts>>(new Map())

const formatReportText = (text: string) => {
  if (!text) return ''
  
  try {
    marked.setOptions({
      breaks: true,
      gfm: true,
    })
    
    const html = marked.parse(text)
    const htmlWithoutTables = html.replace(/<table[\s\S]*?<\/table>/gi, '')
    return htmlWithoutTables
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return text.replace(/\n/g, '<br>')
  }
}

const renderCharts = async () => {
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
  chartInstances.value.forEach((instance, index) => {
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
      
      const chartTitle = props.report?.report_content?.charts?.[index]?.title || 
                        props.report?.report_content?.charts?.[index]?.config?.title?.text ||
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
    
    if (chartInstances.value.size === 0) {
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
    
    const chartImages = await exportChartsAsImages()
    
    // 根据isCustomBatch选择使用哪个API
    const response = props.isCustomBatch
      ? await downloadCustomBatchReportPDF(props.report.id, chartImages)
      : await downloadBatchReportPDF(props.report.id, chartImages)
    
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
