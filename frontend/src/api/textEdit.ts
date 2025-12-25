import request from '@/utils/request'

/**
 * 发送文本编辑请求
 * @param data 请求数据
 * @returns Promise
 */
export function sendTextEditRequest(data: {
  selectedText: string
  beforeContext: string
  afterContext: string
  instruction: string
}) {
  return request.post('/api/v1/ai/text-edit', data)
}
