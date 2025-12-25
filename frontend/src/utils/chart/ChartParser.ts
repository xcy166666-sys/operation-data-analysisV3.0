/**
 * ChartParser - HTML图表解析器
 * 
 * 负责解析HTML图表并提取ECharts配置、主题信息和系列数据
 * 
 * 功能：
 * - 解析HTML文档并提取嵌入的JavaScript
 * - 提取ECharts配置对象
 * - 提取主题信息（背景色、文本色、网格色等）
 * - 识别所有数据系列
 * - 验证配置有效性
 * - 生成HTML文档
 */

import type { EChartsOption } from 'echarts'
import type { ParseResult, ThemeInfo, SeriesInfo, ValidationResult } from '@/types/chart'

export class ChartParser {
  /**
   * 解析HTML并提取ECharts配置
   * 
   * @param html - 包含ECharts图表的HTML文档
   * @returns 解析结果，包含配置、主题和错误信息
   */
  parseHTML(html: string): ParseResult {
    try {
      // 验证输入
      if (!html || typeof html !== 'string') {
        return {
          success: false,
          config: null,
          theme: null,
          error: '无效的HTML输入'
        }
      }

      // 提取script标签内容
      const scriptContent = this.extractScriptContent(html)
      if (!scriptContent) {
        return {
          success: false,
          config: null,
          theme: null,
          error: '未找到script标签或ECharts配置'
        }
      }

      // 提取ECharts配置
      const config = this.extractEChartsConfig(scriptContent)
      if (!config) {
        return {
          success: false,
          config: null,
          theme: null,
          error: '无法解析ECharts配置'
        }
      }

      // 提取主题信息
      const theme = this.extractTheme(html, config)

      return {
        success: true,
        config,
        theme
      }
    } catch (error) {
      return {
        success: false,
        config: null,
        theme: null,
        error: error instanceof Error ? error.message : '解析失败'
      }
    }
  }

  /**
   * 从HTML中提取script标签内容
   * 
   * @param html - HTML文档
   * @returns script标签内容，如果没有则返回原始HTML
   */
  private extractScriptContent(html: string): string {
    // 匹配所有script标签
    const scriptMatches = html.match(/<script[^>]*>([\s\S]*?)<\/script>/gi)
    
    if (!scriptMatches || scriptMatches.length === 0) {
      // 如果没有script标签，可能直接是JavaScript代码
      return html
    }

    // 获取最后一个script标签（通常是图表配置）
    const lastScript = scriptMatches[scriptMatches.length - 1]
    
    // 移除script标签，只保留内容
    return lastScript.replace(/<script[^>]*>|<\/script>/gi, '')
  }

  /**
   * 从JavaScript代码中提取ECharts配置
   * 
   * @param scriptContent - JavaScript代码
   * @returns ECharts配置对象
   */
  private extractEChartsConfig(scriptContent: string): EChartsOption | null {
    try {
      // 方法1: 提取 option = {...} 格式
      const optionMatch = scriptContent.match(/(?:var|let|const)?\s*option\s*=\s*({[\s\S]*?});/)
      if (optionMatch) {
        const optionStr = optionMatch[1]
        return this.parseJavaScriptObject(optionStr)
      }

      // 方法2: 提取 setOption({...}) 格式
      const setOptionMatch = scriptContent.match(/setOption\s*\(\s*({[\s\S]*?})\s*\)/)
      if (setOptionMatch) {
        const optionStr = setOptionMatch[1]
        return this.parseJavaScriptObject(optionStr)
      }

      // 方法3: 提取 chart.setOption({...}) 格式
      const chartSetOptionMatch = scriptContent.match(/chart\.setOption\s*\(\s*({[\s\S]*?})\s*\)/)
      if (chartSetOptionMatch) {
        const optionStr = chartSetOptionMatch[1]
        return this.parseJavaScriptObject(optionStr)
      }

      return null
    } catch (error) {
      console.error('[ChartParser] 提取ECharts配置失败:', error)
      return null
    }
  }

  /**
   * 解析JavaScript对象字符串
   * 
   * @param objStr - JavaScript对象字符串
   * @returns 解析后的对象
   */
  private parseJavaScriptObject(objStr: string): any {
    try {
      // 使用Function构造器安全地解析JavaScript对象
      // 注意：这里假设输入是可信的，因为来自用户自己的图表
      const func = new Function(`return ${objStr}`)
      return func()
    } catch (error) {
      console.error('[ChartParser] 解析JavaScript对象失败:', error)
      throw error
    }
  }

  /**
   * 从HTML/配置中提取主题信息
   * 
   * @param html - HTML文档
   * @param config - ECharts配置
   * @returns 主题信息
   */
  extractTheme(html: string, config: EChartsOption): ThemeInfo {
    const theme: ThemeInfo = {
      backgroundColor: '#ffffff',
      textColor: '#333333',
      gridColor: '#e0e0e0',
      colorPalette: []
    }

    // 从配置中提取背景色
    if (config.backgroundColor) {
      theme.backgroundColor = String(config.backgroundColor)
    }

    // 从配置中提取文本颜色
    if (config.textStyle && typeof config.textStyle === 'object' && 'color' in config.textStyle) {
      theme.textColor = String(config.textStyle.color)
    }

    // 从配置中提取网格颜色
    if (config.grid && typeof config.grid === 'object' && 'borderColor' in config.grid) {
      theme.gridColor = String(config.grid.borderColor)
    }

    // 从配置中提取调色板
    if (config.color && Array.isArray(config.color)) {
      theme.colorPalette = config.color.map(c => String(c))
    } else if (config.series && Array.isArray(config.series) && config.series.length > 0) {
      // 从系列中提取颜色
      theme.colorPalette = config.series
        .map(s => {
          if (typeof s === 'object' && s !== null) {
            if ('itemStyle' in s && s.itemStyle && typeof s.itemStyle === 'object' && 'color' in s.itemStyle) {
              return String(s.itemStyle.color)
            }
            if ('lineStyle' in s && s.lineStyle && typeof s.lineStyle === 'object' && 'color' in s.lineStyle) {
              return String(s.lineStyle.color)
            }
          }
          return null
        })
        .filter((c): c is string => c !== null)
    }

    // 从HTML中提取自定义CSS
    const styleMatch = html.match(/<style[^>]*>([\s\S]*?)<\/style>/i)
    if (styleMatch) {
      theme.customCSS = styleMatch[1].trim()
    }

    return theme
  }

  /**
   * 识别图表中的所有数据系列
   * 
   * @param config - ECharts配置
   * @returns 系列信息数组
   */
  extractSeries(config: EChartsOption): SeriesInfo[] {
    if (!config.series || !Array.isArray(config.series)) {
      return []
    }

    return config.series.map((series, index) => {
      if (typeof series !== 'object' || series === null) {
        return null
      }

      // 提取系列基本信息
      const seriesInfo: SeriesInfo = {
        id: `series-${index}`,
        name: 'name' in series && typeof series.name === 'string' ? series.name : `系列${index + 1}`,
        type: 'type' in series && typeof series.type === 'string' ? series.type : 'line',
        color: '#409eff',
        visible: true,
        data: []
      }

      // 提取颜色
      if ('itemStyle' in series && series.itemStyle && typeof series.itemStyle === 'object' && 'color' in series.itemStyle) {
        seriesInfo.color = series.itemStyle.color
      } else if ('lineStyle' in series && series.lineStyle && typeof series.lineStyle === 'object' && 'color' in series.lineStyle) {
        seriesInfo.color = series.lineStyle.color
      }

      // 提取数据
      if ('data' in series && Array.isArray(series.data)) {
        seriesInfo.data = series.data
      }

      return seriesInfo
    }).filter((s): s is SeriesInfo => s !== null)
  }

  /**
   * 验证图表配置
   * 
   * @param config - ECharts配置
   * @returns 验证结果
   */
  validate(config: EChartsOption): ValidationResult {
    const errors: string[] = []

    // 检查配置是否为对象
    if (!config || typeof config !== 'object') {
      errors.push('配置必须是一个对象')
      return { valid: false, errors }
    }

    // 检查是否有系列数据
    if (!config.series || !Array.isArray(config.series) || config.series.length === 0) {
      errors.push('配置必须包含至少一个系列')
    }

    // 检查系列数据格式
    if (config.series && Array.isArray(config.series)) {
      config.series.forEach((series, index) => {
        if (typeof series !== 'object' || series === null) {
          errors.push(`系列${index}必须是一个对象`)
        } else {
          if (!('type' in series)) {
            errors.push(`系列${index}缺少type属性`)
          }
          if (!('data' in series) || !Array.isArray(series.data)) {
            errors.push(`系列${index}缺少data数组`)
          }
        }
      })
    }

    return {
      valid: errors.length === 0,
      errors
    }
  }

  /**
   * 从配置生成HTML
   * 
   * @param config - ECharts配置
   * @param theme - 主题信息
   * @returns HTML文档
   */
  generateHTML(config: EChartsOption, theme: ThemeInfo): string {
    const configStr = JSON.stringify(config, null, 2)
    
    const customStyle = theme.customCSS || `
    body {
      margin: 0;
      padding: 20px;
      background-color: ${theme.backgroundColor};
    }
    #chart {
      width: 800px;
      height: 600px;
      background-color: ${theme.backgroundColor};
    }
    `.trim()

    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>ECharts图表</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
  <style>
${customStyle}
  </style>
</head>
<body>
  <div id="chart"></div>
  <script>
    const chart = echarts.init(document.getElementById('chart'));
    const option = ${configStr};
    chart.setOption(option);
  </script>
</body>
</html>`
  }
}
