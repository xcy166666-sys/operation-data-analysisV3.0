/**
 * ChartRenderer - 图表渲染器
 * 
 * 负责渲染图表并提供实时预览功能
 * 
 * 功能：
 * - 初始化ECharts实例
 * - 实时更新图表配置
 * - 处理容器大小和响应式
 * - 错误处理和恢复
 * - 性能优化
 */

import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'

export interface RenderOptions {
  width?: number
  height?: number
  renderer?: 'canvas' | 'svg'
  devicePixelRatio?: number
}

export interface RenderResult {
  success: boolean
  error?: string
}

export class ChartRenderer {
  private chart: ECharts | null = null
  private container: HTMLElement | null = null
  private lastValidConfig: EChartsOption | null = null
  private resizeObserver: ResizeObserver | null = null

  /**
   * 初始化ECharts实例
   * 
   * @param container - DOM容器元素
   * @param options - 渲染选项
   * @returns 渲染结果
   */
  init(container: HTMLElement, options: RenderOptions = {}): RenderResult {
    try {
      // 验证容器
      if (!container) {
        return {
          success: false,
          error: '容器元素不能为空'
        }
      }

      // 如果已有实例，先销毁
      if (this.chart) {
        this.dispose()
      }

      // 保存容器引用
      this.container = container

      // 创建ECharts实例
      this.chart = echarts.init(container, undefined, {
        renderer: options.renderer || 'canvas',
        width: options.width,
        height: options.height,
        devicePixelRatio: options.devicePixelRatio
      })

      // 设置响应式
      this.setupResponsive()

      return {
        success: true
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : '初始化失败'
      }
    }
  }

  /**
   * 渲染图表
   * 
   * @param config - ECharts配置
   * @param notMerge - 是否不合并配置
   * @returns 渲染结果
   */
  render(config: EChartsOption, notMerge: boolean = false): RenderResult {
    try {
      // 验证实例
      if (!this.chart) {
        return {
          success: false,
          error: '图表实例未初始化'
        }
      }

      // 验证配置
      if (!config || typeof config !== 'object') {
        return {
          success: false,
          error: '无效的图表配置'
        }
      }

      // 设置配置
      this.chart.setOption(config, notMerge)

      // 保存有效配置
      this.lastValidConfig = config

      return {
        success: true
      }
    } catch (error) {
      console.error('[ChartRenderer] 渲染失败:', error)
      
      // 尝试恢复到最后有效状态
      if (this.lastValidConfig && this.chart) {
        try {
          this.chart.setOption(this.lastValidConfig, true)
        } catch (e) {
          console.error('[ChartRenderer] 恢复失败:', e)
        }
      }

      return {
        success: false,
        error: error instanceof Error ? error.message : '渲染失败'
      }
    }
  }

  /**
   * 更新图表配置（增量更新）
   * 
   * @param config - 部分配置
   * @returns 渲染结果
   */
  update(config: Partial<EChartsOption>): RenderResult {
    return this.render(config as EChartsOption, false)
  }

  /**
   * 重新渲染图表（完全替换）
   * 
   * @param config - 完整配置
   * @returns 渲染结果
   */
  rerender(config: EChartsOption): RenderResult {
    return this.render(config, true)
  }

  /**
   * 调整图表大小
   * 
   * @param width - 宽度
   * @param height - 高度
   */
  resize(width?: number, height?: number): void {
    if (this.chart) {
      this.chart.resize({
        width,
        height
      })
    }
  }

  /**
   * 设置响应式
   */
  private setupResponsive(): void {
    if (!this.container) return

    // 使用ResizeObserver监听容器大小变化
    if (typeof ResizeObserver !== 'undefined') {
      this.resizeObserver = new ResizeObserver(() => {
        this.resize()
      })
      this.resizeObserver.observe(this.container)
    } else {
      // 降级方案：使用window resize事件
      window.addEventListener('resize', this.handleWindowResize)
    }
  }

  /**
   * 处理窗口大小变化
   */
  private handleWindowResize = (): void => {
    this.resize()
  }

  /**
   * 获取图表实例
   */
  getInstance(): ECharts | null {
    return this.chart
  }

  /**
   * 获取最后有效配置
   */
  getLastValidConfig(): EChartsOption | null {
    return this.lastValidConfig
  }

  /**
   * 导出为图片
   * 
   * @param type - 图片类型
   * @param pixelRatio - 像素比
   * @returns 图片DataURL
   */
  exportImage(type: 'png' | 'jpeg' = 'png', pixelRatio: number = 1): string | null {
    if (!this.chart) {
      return null
    }

    try {
      return this.chart.getDataURL({
        type,
        pixelRatio,
        backgroundColor: '#fff'
      })
    } catch (error) {
      console.error('[ChartRenderer] 导出图片失败:', error)
      return null
    }
  }

  /**
   * 显示加载动画
   */
  showLoading(text: string = '加载中...'): void {
    if (this.chart) {
      this.chart.showLoading('default', {
        text,
        color: '#409eff',
        textColor: '#000',
        maskColor: 'rgba(255, 255, 255, 0.8)',
        zlevel: 0
      })
    }
  }

  /**
   * 隐藏加载动画
   */
  hideLoading(): void {
    if (this.chart) {
      this.chart.hideLoading()
    }
  }

  /**
   * 清空图表
   */
  clear(): void {
    if (this.chart) {
      this.chart.clear()
      this.lastValidConfig = null
    }
  }

  /**
   * 销毁图表实例
   */
  dispose(): void {
    // 移除事件监听
    if (this.resizeObserver) {
      this.resizeObserver.disconnect()
      this.resizeObserver = null
    } else {
      window.removeEventListener('resize', this.handleWindowResize)
    }

    // 销毁图表实例
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }

    // 清空引用
    this.container = null
    this.lastValidConfig = null
  }

  /**
   * 检查是否已初始化
   */
  isInitialized(): boolean {
    return this.chart !== null
  }
}

/**
 * 创建图表渲染器实例
 */
export function createChartRenderer(): ChartRenderer {
  return new ChartRenderer()
}
