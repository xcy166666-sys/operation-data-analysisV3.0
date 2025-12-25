/**
 * AI对话API
 */
import request from '@/utils/request'

export interface DialogMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  modified_charts?: any[]
  quoted_text?: string  // 引用的文字
}

export interface DialogRequest {
  session_id: number
  message: string
  conversation_id?: string
  current_charts?: any[]  // 当前图表数据
  current_report_text?: string  // 当前报告文字
  current_html_charts?: string  // 当前HTML图表
  selected_text?: string  // 选中的文字
  selected_text_context?: {  // 选中文字的上下文
    beforeContext: string
    afterContext: string
    fullText: string
  }
}

export interface DialogResponse {
  response: string
  modified_charts: any[]
  conversation_id: string
  action_type: 'modify_chart' | 'chat' | 'analysis' | 'error' | 'regenerate_report' | 'modify_text'
  new_report_text?: string  // 修改后的报告文字
  new_html_charts?: string  // 修改后的HTML图表
  modified_text?: string  // 修改后的选中文字
}

// 流式响应数据块类型
export interface StreamChunk {
  type: 'thinking' | 'content' | 'done' | 'error'
  content: string
  data?: DialogResponse
}

/**
 * 发送对话消息（流式响应，支持思考过程可视化）
 */
export async function sendDialogMessageStream(
  data: DialogRequest,
  onThinking: (text: string) => void,
  onContent: (text: string) => void,
  onDone: (result: DialogResponse) => void,
  onError: (error: string) => void
): Promise<void> {
  const formData = new FormData()
  formData.append('session_id', data.session_id.toString())
  formData.append('user_message', data.message)
  if (data.conversation_id) {
    formData.append('conversation_id', data.conversation_id)
  }
  formData.append('current_charts', JSON.stringify(data.current_charts || []))
  formData.append('current_report_text', data.current_report_text || '')
  formData.append('current_html_charts', data.current_html_charts || '')
  
  if (data.selected_text) {
    formData.append('selected_text', data.selected_text)
    if (data.selected_text_context) {
      formData.append('selected_text_context', JSON.stringify(data.selected_text_context))
    }
  }
  
  try {
    const response = await fetch('/api/v1/operation/dialog/stream', {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法获取响应流')
    }
    
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      // 按行解析SSE数据
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const chunk: StreamChunk = JSON.parse(line.slice(6))
            
            switch (chunk.type) {
              case 'thinking':
                onThinking(chunk.content)
                break
              case 'content':
                onContent(chunk.content)
                break
              case 'done':
                if (chunk.data) {
                  onDone(chunk.data)
                }
                break
              case 'error':
                onError(chunk.content)
                break
            }
          } catch (e) {
            console.warn('[Dialog Stream] 解析数据块失败:', line)
          }
        }
      }
    }
  } catch (error: any) {
    onError(error.message || '请求失败')
  }
}

/**
 * 发送对话消息（非流式，兼容旧版本）
 */
export function sendDialogMessage(data: DialogRequest) {
  const formData = new FormData()
  formData.append('session_id', data.session_id.toString())
  formData.append('user_message', data.message)
  if (data.conversation_id) {
    formData.append('conversation_id', data.conversation_id)
  }
  // 传递完整的报告内容，让AI重新生成
  formData.append('current_charts', JSON.stringify(data.current_charts || []))
  formData.append('current_report_text', data.current_report_text || '')
  formData.append('current_html_charts', data.current_html_charts || '')
  
  // 传递选中的文字和上下文
  if (data.selected_text) {
    formData.append('selected_text', data.selected_text)
    if (data.selected_text_context) {
      formData.append('selected_text_context', JSON.stringify(data.selected_text_context))
    }
  }
  
  return request.post<DialogResponse>(
    '/operation/dialog',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
}

/**
 * 获取对话历史
 */
export function getDialogHistory(sessionId: number, limit: number = 20) {
  return request.get<{ messages: DialogMessage[] }>(
    '/operation/dialog/history',
    {
      params: {
        session_id: sessionId,
        limit
      }
    }
  )
}

/**
 * 清除对话历史
 */
export function clearDialogHistory(sessionId: number) {
  return request.delete<{ session_id: number }>(
    '/operation/dialog/history',
    {
      params: {
        session_id: sessionId
      }
    }
  )
}
