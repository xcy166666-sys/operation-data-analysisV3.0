/**
 * 图表相关API
 */
import request from '@/utils/request'

export interface ChartModificationRequest {
  session_id: number
  current_html: string
  color?: string
  chart_type?: string
  ai_instruction?: string
}

export interface ChartModificationResponse {
  html: string
}

/**
 * 修改图表
 */
export function modifyChart(data: ChartModificationRequest) {
  const formData = new FormData()
  formData.append('session_id', data.session_id.toString())
  formData.append('current_html', data.current_html)
  
  if (data.color) {
    formData.append('color', data.color)
  }
  
  if (data.chart_type) {
    formData.append('chart_type', data.chart_type)
  }
  
  if (data.ai_instruction) {
    formData.append('ai_instruction', data.ai_instruction)
  }
  
  return request.post<ChartModificationResponse>(
    '/operation/charts/modify',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000 // 60秒超时
    }
  )
}
