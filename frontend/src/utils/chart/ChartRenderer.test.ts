/**
 * ChartRenderer单元测试
 * 
 * 测试图表渲染器的核心功能
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ChartRenderer } from './ChartRenderer'
import { createMockEChartsConfig, createMultiSeriesConfig } from './test-utils'
import * as echarts from 'echarts'

describe('ChartRenderer', () => {
  let renderer: ChartRenderer
  let container: HTMLDivElement

  beforeEach(() => {
    // 创建测试容器
    container = document.createElement('div')
    container.style.width = '800px'
    container.style.height = '600px'
    document.body.appendChild(container)

    // 创建渲染器实例
    renderer = new ChartRenderer()
  })

  afterEach(() => {
    // 清理
    renderer.dispose()
    document.body.removeChild(container)
  })

  describe('初始化', () => {
    it('应该成功初始化ECharts实例', () => {
      const result = renderer.init(container)
      
      expect(result.success).toBe(true)
      expect(result.error).toBeUndefined()
      expect(renderer.isInitialized()).toBe(true)
    })

    it('应该在容器为空时返回错误', () => {
      const result = renderer.init(null as any)
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('容器元素不能为空')
      expect(renderer.isInitialized()).toBe(false)
    })

    it('应该支持自定义渲染选项', () => {
      const result = renderer.init(container, {
        renderer: 'svg',
        width: 1000,
        height: 800
      })
      
      expect(result.success).toBe(true)
      expect(renderer.isInitialized()).toBe(true)
    })

    it('应该在重新初始化时销毁旧实例', () => {
      // 第一次初始化
      renderer.init(container)
      const firstInstance = renderer.getInstance()
      
      // 第二次初始化
      renderer.init(container)
      const secondInstance = renderer.getInstance()
      
      expect(firstInstance).not.toBe(secondInstance)
      expect(renderer.isInitialized()).toBe(true)
    })
  })

  describe('渲染', () => {
    beforeEach(() => {
      renderer.init(container)
    })

    it('应该成功渲染图表配置', () => {
      const config = createMockEChartsConfig()
      const result = renderer.render(config)
      
      expect(result.success).toBe(true)
      expect(result.error).toBeUndefined()
      expect(renderer.getLastValidConfig()).toEqual(config)
    })

    it('应该在未初始化时返回错误', () => {
      const uninitializedRenderer = new ChartRenderer()
      const config = createMockEChartsConfig()
      const result = uninitializedRenderer.render(config)
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('图表实例未初始化')
    })

    it('应该在配置无效时返回错误', () => {
      const result = renderer.render(null as any)
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('无效的图表配置')
    })

    it('应该支持增量更新', () => {
      const config = createMockEChartsConfig()
      renderer.render(config)
      
      const updateResult = renderer.update({
        title: { text: '更新后的标题' }
      })
      
      expect(updateResult.success).toBe(true)
    })

    it('应该支持完全替换', () => {
      const config1 = createMockEChartsConfig()
      renderer.render(config1)
      
      const config2 = createMockEChartsConfig({
        title: { text: '新图表' }
      })
      const result = renderer.rerender(config2)
      
      expect(result.success).toBe(true)
    })
  })

  describe('错误恢复', () => {
    beforeEach(() => {
      renderer.init(container)
    })

    it('应该在渲染失败时保留最后有效配置', () => {
      const validConfig = createMockEChartsConfig()
      renderer.render(validConfig)
      
      // 尝试渲染无效配置
      const invalidResult = renderer.render(null as any)
      
      expect(invalidResult.success).toBe(false)
      expect(renderer.getLastValidConfig()).toEqual(validConfig)
    })
  })

  describe('响应式', () => {
    beforeEach(() => {
      renderer.init(container)
    })

    it('应该支持手动调整大小', () => {
      const config = createMockEChartsConfig()
      renderer.render(config)
      
      // 调整大小不应抛出错误
      expect(() => {
        renderer.resize(1000, 800)
      }).not.toThrow()
    })

    it('应该在容器大小变化时自动调整', async () => {
      const config = createMockEChartsConfig()
      renderer.render(config)
      
      // 改变容器大小
      container.style.width = '1000px'
      container.style.height = '800px'
      
      // 等待ResizeObserver触发
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 验证没有错误
      expect(renderer.isInitialized()).toBe(true)
    })
  })

  describe('导出', () => {
    beforeEach(() => {
      renderer.init(container)
      const config = createMockEChartsConfig()
      renderer.render(config)
    })

    it('应该导出PNG图片', () => {
      const dataUrl = renderer.exportImage('png')
      
      expect(dataUrl).toBeTruthy()
      expect(dataUrl).toContain('data:image/png')
    })

    it('应该导出JPEG图片', () => {
      const dataUrl = renderer.exportImage('jpeg')
      
      expect(dataUrl).toBeTruthy()
      expect(dataUrl).toContain('data:image/jpeg')
    })

    it('应该支持自定义像素比', () => {
      const dataUrl = renderer.exportImage('png', 2)
      
      expect(dataUrl).toBeTruthy()
    })

    it('应该在未初始化时返回null', () => {
      const uninitializedRenderer = new ChartRenderer()
      const dataUrl = uninitializedRenderer.exportImage('png')
      
      expect(dataUrl).toBeNull()
    })
  })

  describe('加载状态', () => {
    beforeEach(() => {
      renderer.init(container)
    })

    it('应该显示加载动画', () => {
      expect(() => {
        renderer.showLoading('加载中...')
      }).not.toThrow()
    })

    it('应该隐藏加载动画', () => {
      renderer.showLoading()
      
      expect(() => {
        renderer.hideLoading()
      }).not.toThrow()
    })
  })

  describe('清理', () => {
    beforeEach(() => {
      renderer.init(container)
      const config = createMockEChartsConfig()
      renderer.render(config)
    })

    it('应该清空图表', () => {
      renderer.clear()
      
      expect(renderer.getLastValidConfig()).toBeNull()
      expect(renderer.isInitialized()).toBe(true)
    })

    it('应该销毁图表实例', () => {
      renderer.dispose()
      
      expect(renderer.isInitialized()).toBe(false)
      expect(renderer.getInstance()).toBeNull()
    })
  })

  describe('性能', () => {
    beforeEach(() => {
      renderer.init(container)
    })

    it('应该快速渲染简单图表', () => {
      const config = createMockEChartsConfig()
      const startTime = performance.now()
      
      renderer.render(config)
      
      const endTime = performance.now()
      const duration = endTime - startTime
      
      // 应该在100ms内完成
      expect(duration).toBeLessThan(100)
    })

    it('应该处理多系列图表', () => {
      const config = createMultiSeriesConfig(10)
      const result = renderer.render(config)
      
      expect(result.success).toBe(true)
    })
  })

  describe('实例管理', () => {
    it('应该返回ECharts实例', () => {
      renderer.init(container)
      const instance = renderer.getInstance()
      
      expect(instance).toBeTruthy()
      expect(typeof instance?.setOption).toBe('function')
    })

    it('应该在未初始化时返回null', () => {
      const instance = renderer.getInstance()
      
      expect(instance).toBeNull()
    })
  })
})
