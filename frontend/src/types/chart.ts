/**
 * 增强图表编辑器 - TypeScript类型定义
 * 
 * 定义ECharts配置、主题信息、系列信息等核心类型
 */

import type { EChartsOption } from 'echarts'

// ==================== 核心类型 ====================

/**
 * 解析结果
 */
export interface ParseResult {
  success: boolean
  config: EChartsOption | null
  theme: ThemeInfo | null
  error?: string
}

/**
 * 主题信息
 */
export interface ThemeInfo {
  backgroundColor: string
  textColor: string
  gridColor: string
  colorPalette: string[]
  customCSS?: string
}

/**
 * 系列信息
 */
export interface SeriesInfo {
  id: string
  name: string
  type: 'line' | 'bar' | 'pie' | 'scatter' | string
  color: string | object
  visible: boolean
  data: any[]
}

/**
 * 验证结果
 */
export interface ValidationResult {
  valid: boolean
  errors: string[]
}

// ==================== 修改引擎类型 ====================

/**
 * 修改类型
 */
export type ModificationType = 'color' | 'series' | 'theme' | 'style' | 'data' | 'ai'

/**
 * 修改对象
 */
export interface Modification {
  type: ModificationType
  target: string  // 配置属性的路径
  value: any
  metadata?: Record<string, any>
}

/**
 * 编辑器状态
 */
export interface EditorState {
  config: EChartsOption
  theme: ThemeInfo
  timestamp: number
}

/**
 * AI修改结果
 */
export interface AIModificationResult {
  success: boolean
  config?: EChartsOption
  error?: string
  message?: string
}

// ==================== 导出类型 ====================

/**
 * 导出格式
 */
export type ExportFormat = 'html' | 'png' | 'svg' | 'json'

/**
 * 导出选项
 */
export interface ExportOptions {
  format: ExportFormat
  width?: number
  height?: number
  quality?: number
}

// ==================== 图表编辑器Props ====================

/**
 * ChartEditorModal组件Props
 */
export interface ChartEditorModalProps {
  visible: boolean
  chartHtml: string
  chartId: string
  sessionId?: number
}

/**
 * ChartEditorModal组件Emits
 */
export interface ChartEditorModalEmits {
  'update:visible': (value: boolean) => void
  'save': (html: string, config: EChartsOption) => void
  'cancel': () => void
}

// ==================== 存储类型 ====================

/**
 * 存储的图表
 */
export interface StoredChart {
  id: string
  sessionId: number
  originalHtml: string
  currentHtml: string
  config: EChartsOption
  theme: ThemeInfo
  modificationHistory: ModificationRecord[]
  createdAt: Date
  updatedAt: Date
}

/**
 * 修改记录
 */
export interface ModificationRecord {
  id: string
  timestamp: Date
  type: 'local' | 'ai'
  instruction?: string
  changes: Record<string, any>
  appliedBy: string
}
