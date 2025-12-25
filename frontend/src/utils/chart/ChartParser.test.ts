/**
 * ChartParser单元测试
 */

import { describe, it, expect } from 'vitest'
import { ChartParser } from './ChartParser'
import { createMockEChartsConfig, createMockChartHTML, createDarkThemeConfig } from './test-utils'

describe('ChartParser', () => {
  const parser = new ChartParser()

  describe('parseHTML', () => {
    it('应该成功解析有效的HTML图表', () => {
      const config = createMockEChartsConfig()
      const html = createMockChartHTML(config)
      
      const result = parser.parseHTML(html)
      
      expect(result.success).toBe(true)
      expect(result.config).toBeDefined()
      expect(result.theme).toBeDefined()
      expect(result.error).toBeUndefined()
    })

    it('应该拒绝空HTML', () => {
      const result = parser.parseHTML('')
      
      expect(result.success).toBe(false)
      expect(result.config).toBeNull()
      expect(result.error).toBeDefined()
    })

    it('应该拒绝无效的HTML', () => {
      const result = parser.parseHTML('<html><body>没有图表配置</body></html>')
      
      expect(result.success).toBe(false)
      expect(result.config).toBeNull()
      expect(result.error).toBeDefined()
    })

    it('应该处理格式错误的JavaScript', () => {
      const html = `
        <script>
          const option = { invalid javascript
        </script>
      `
      
      const result = parser.parseHTML(html)
      
      expect(result.success).toBe(false)
    })
  })

  describe('extractTheme', () => {
    it('应该提取背景颜色', () => {
      const config = createMockEChartsConfig({
        backgroundColor: '#0f0f1c'
      })
      const html = createMockChartHTML(config)
      
      const result = parser.parseHTML(html)
      
      expect(result.theme?.backgroundColor).toBe('#0f0f1c')
    })

    it('应该提取文本颜色', () => {
      const config = createMockEChartsConfig({
        textStyle: {
          color: '#ffffff'
        }
      })
      const html = createMockChartHTML(config)
      
      const result = parser.parseHTML(html)
      
      expect(result.theme?.textColor).toBe('#ffffff')
    })

    it('应该提取调色板', () => {
      const colors = ['#409eff', '#67c23a', '#e6a23c']
      const config = createMockEChartsConfig({
        color: colors
      })
      const html = createMockChartHTML(config)
      
      const result = parser.parseHTML(html)
      
      expect(result.theme?.colorPalette).toEqual(colors)
    })

    it('应该从系列中提取颜色', () => {
      const config = createMockEChartsConfig({
        series: [
          {
            type: 'line',
            data: [1, 2, 3],
            itemStyle: {
              color: '#ff0000'
            }
          }
        ]
      })
      const html = createMockChartHTML(config)
      
      const result = parser.parseHTML(html)
      
      expect(result.theme?.colorPalette).toContain('#ff0000')
    })
  })

  describe('extractSeries', () => {
    it('应该识别所有系列', () => {
      const config = createMockEChartsConfig({
        series: [
          { type: 'line', name: '系列1', data: [1, 2, 3] },
          { type: 'bar', name: '系列2', data: [4, 5, 6] }
        ]
      })
      
      const series = parser.extractSeries(config)
      
      expect(series).toHaveLength(2)
      expect(series[0].name).toBe('系列1')
      expect(series[0].type).toBe('line')
      expect(series[1].name).toBe('系列2')
      expect(series[1].type).toBe('bar')
    })

    it('应该处理没有系列的配置', () => {
      const config = createMockEChartsConfig({
        series: []
      })
      
      const series = parser.extractSeries(config)
      
      expect(series).toHaveLength(0)
    })

    it('应该为没有名称的系列生成默认名称', () => {
      const config = createMockEChartsConfig({
        series: [
          { type: 'line', data: [1, 2, 3] }
        ]
      })
      
      const series = parser.extractSeries(config)
      
      expect(series[0].name).toBe('系列1')
    })
  })

  describe('validate', () => {
    it('应该验证有效的配置', () => {
      const config = createMockEChartsConfig()
      
      const result = parser.validate(config)
      
      expect(result.valid).toBe(true)
      expect(result.errors).toHaveLength(0)
    })

    it('应该拒绝空配置', () => {
      const result = parser.validate(null as any)
      
      expect(result.valid).toBe(false)
      expect(result.errors.length).toBeGreaterThan(0)
    })

    it('应该拒绝没有系列的配置', () => {
      const config = createMockEChartsConfig({
        series: []
      })
      
      const result = parser.validate(config)
      
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('配置必须包含至少一个系列')
    })

    it('应该检测缺少type的系列', () => {
      const config = createMockEChartsConfig({
        series: [
          { data: [1, 2, 3] } as any
        ]
      })
      
      const result = parser.validate(config)
      
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.includes('type'))).toBe(true)
    })
  })

  describe('generateHTML', () => {
    it('应该生成有效的HTML', () => {
      const config = createMockEChartsConfig()
      const theme = {
        backgroundColor: '#ffffff',
        textColor: '#333333',
        gridColor: '#e0e0e0',
        colorPalette: ['#409eff']
      }
      
      const html = parser.generateHTML(config, theme)
      
      expect(html).toContain('<!DOCTYPE html>')
      expect(html).toContain('echarts')
      expect(html).toContain('setOption')
      expect(html).toContain(theme.backgroundColor)
    })

    it('应该包含配置数据', () => {
      const config = createMockEChartsConfig({
        title: {
          text: '测试标题'
        }
      })
      const theme = {
        backgroundColor: '#ffffff',
        textColor: '#333333',
        gridColor: '#e0e0e0',
        colorPalette: []
      }
      
      const html = parser.generateHTML(config, theme)
      
      expect(html).toContain('测试标题')
    })
  })

  describe('往返测试', () => {
    it('应该通过解析-生成循环保留配置', () => {
      const originalConfig = createMockEChartsConfig()
      const originalHtml = createMockChartHTML(originalConfig)
      
      // 解析
      const parseResult = parser.parseHTML(originalHtml)
      expect(parseResult.success).toBe(true)
      
      // 生成
      const newHtml = parser.generateHTML(parseResult.config!, parseResult.theme!)
      
      // 再次解析
      const secondParseResult = parser.parseHTML(newHtml)
      expect(secondParseResult.success).toBe(true)
      
      // 验证关键属性保留
      expect(secondParseResult.config?.series).toHaveLength(originalConfig.series!.length)
    })
  })
})
