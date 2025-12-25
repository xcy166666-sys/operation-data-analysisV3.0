/**
 * 图表编辑器 - 本地即时修改工具
 * 
 * 功能：
 * - 解析ECharts和Chart.js配置
 * - 即时修改颜色、类型、样式
 * - 生成新的HTML
 * 
 * 性能：所有操作 < 100ms
 */

export interface ChartConfig {
  // ECharts配置
  title?: {
    text?: string
    subtext?: string
  }
  color?: string[]
  series?: Array<{
    type?: string
    data?: any[]
    itemStyle?: any
    label?: any
  }>
  legend?: {
    show?: boolean
  }
  grid?: {
    show?: boolean
  }
  tooltip?: {
    show?: boolean
  }
  xAxis?: any
  yAxis?: any
  
  // Chart.js配置
  type?: string
  data?: {
    labels?: string[]
    datasets?: Array<{
      label?: string
      data?: any[]
      backgroundColor?: string | string[]
      borderColor?: string | string[]
      fill?: boolean
      tension?: number
      [key: string]: any
    }>
  }
  options?: any
  
  [key: string]: any
}

export interface StyleOptions {
  showDataLabel?: boolean
  showLegend?: boolean
  showGrid?: boolean
  showTooltip?: boolean
}

export interface SizeOptions {
  width?: number
  height?: number
}

type ChartLibrary = 'echarts' | 'chartjs' | 'unknown'

export class ChartEditor {
  private chartLibrary: ChartLibrary = 'unknown'
  
  /**
   * 检测图表库类型
   */
  detectChartLibrary(html: string): ChartLibrary {
    if (html.includes('chart.js') || html.includes('Chart(')) {
      return 'chartjs'
    }
    if (html.includes('echarts') || html.includes('setOption')) {
      return 'echarts'
    }
    return 'unknown'
  }

  /**
   * 解析HTML中的图表配置
   */
  parseChartConfig(html: string): ChartConfig | null {
    try {
      console.log('[ChartEditor] 开始解析HTML，长度:', html.length)
      
      // 检测图表库
      this.chartLibrary = this.detectChartLibrary(html)
      console.log('[ChartEditor] 检测到图表库:', this.chartLibrary)
      
      // 先提取script标签内容（如果是完整HTML文档）
      let scriptContent = html
      const scriptMatch = html.match(/<script[^>]*>([\s\S]*?)<\/script>/gi)
      if (scriptMatch && scriptMatch.length > 0) {
        console.log('[ChartEditor] 检测到完整HTML文档，提取script内容')
        // 获取最后一个script标签（通常是图表配置）
        const lastScript = scriptMatch[scriptMatch.length - 1]
        scriptContent = lastScript.replace(/<script[^>]*>|<\/script>/gi, '')
        console.log('[ChartEditor] Script内容长度:', scriptContent.length)
      }
      
      if (this.chartLibrary === 'chartjs') {
        return this.parseChartJsConfig(scriptContent)
      } else if (this.chartLibrary === 'echarts') {
        return this.parseEChartsConfig(scriptContent)
      }
      
      console.warn('[ChartEditor] 无法识别图表库类型')
      return null
    } catch (e) {
      console.error('[ChartEditor] 解析配置失败:', e)
      return null
    }
  }
  
  /**
   * 解析Chart.js配置
   */
  parseChartJsConfig(scriptContent: string): ChartConfig | null {
    try {
      // 先提取data对象
      const dataMatch = scriptContent.match(/const\s+data\s*=\s*({[\s\S]*?});/)
      let dataObj = null
      if (dataMatch) {
        const dataStr = dataMatch[1]
        dataObj = new Function(`return ${dataStr}`)()
        console.log('[ChartEditor] 找到Chart.js data对象')
      }
      
      // 提取config对象
      const configMatch = scriptContent.match(/const\s+config\s*=\s*({[\s\S]*?});/)
      if (configMatch) {
        console.log('[ChartEditor] 找到Chart.js config配置')
        const configStr = configMatch[1]
        
        // 如果config中引用了data变量，需要在解析时提供
        let config
        if (dataObj) {
          config = new Function('data', `return ${configStr}`)(dataObj)
        } else {
          config = new Function(`return ${configStr}`)()
        }
        
        console.log('[ChartEditor] Chart.js解析成功:', {
          type: config.type,
          hasData: !!config.data,
          datasetCount: config.data?.datasets?.length
        })
        return config
      }
      
      console.warn('[ChartEditor] 无法解析Chart.js配置')
      return null
    } catch (e) {
      console.error('[ChartEditor] 解析Chart.js失败:', e)
      return null
    }
  }
  
  /**
   * 解析ECharts配置
   */
  parseEChartsConfig(scriptContent: string): ChartConfig | null {
    try {
      // 方法1: 提取option配置
      const optionMatch = scriptContent.match(/(?:var|let|const)?\s*option\s*=\s*({[\s\S]*?});/)
      if (optionMatch) {
        console.log('[ChartEditor] 找到ECharts option配置')
        const optionStr = optionMatch[1]
        const option = new Function(`return ${optionStr}`)()
        console.log('[ChartEditor] ECharts解析成功')
        return option
      }

      // 方法2: 提取setOption参数
      const setOptionMatch = scriptContent.match(/setOption\(({[\s\S]*?})\)/)
      if (setOptionMatch) {
        console.log('[ChartEditor] 找到ECharts setOption配置')
        const optionStr = setOptionMatch[1]
        const option = new Function(`return ${optionStr}`)()
        return option
      }

      console.warn('[ChartEditor] 无法解析ECharts配置')
      return null
    } catch (e) {
      console.error('[ChartEditor] 解析ECharts失败:', e)
      return null
    }
  }

  /**
   * 修改颜色 - 即时生效 ⚡
   */
  changeColor(html: string, color: string): string {
    const option = this.parseChartConfig(html)
    if (!option) return html

    if (this.chartLibrary === 'chartjs') {
      // Chart.js: 修改datasets的颜色
      if (option.data?.datasets && Array.isArray(option.data.datasets)) {
        option.data.datasets.forEach((dataset: any) => {
          dataset.borderColor = color
          dataset.backgroundColor = color.replace(')', ', 0.2)').replace('rgb', 'rgba')
          if (dataset.pointBackgroundColor) {
            dataset.pointBackgroundColor = color
          }
        })
      }
    } else if (this.chartLibrary === 'echarts') {
      // ECharts: 修改主色调
      option.color = [color]
      if (option.series && Array.isArray(option.series)) {
        option.series.forEach((series: any) => {
          if (!series.itemStyle) series.itemStyle = {}
          series.itemStyle.color = color
        })
      }
    }

    return this.generateHTML(option, html)
  }

  /**
   * 修改图表类型 - 即时生效 ⚡
   */
  changeType(html: string, type: string): string {
    const option = this.parseChartConfig(html)
    if (!option) return html

    // 修改系列类型
    if (option.series && Array.isArray(option.series)) {
      option.series.forEach((series: any) => {
        series.type = type

        // 根据类型调整特定配置
        if (type === 'line') {
          // 折线图：添加平滑曲线
          series.smooth = true
        } else if (type === 'pie') {
          // 饼图：添加半径配置
          series.radius = ['40%', '70%']
          series.center = ['50%', '50%']
        } else if (type === 'bar') {
          // 柱状图：移除饼图特有配置
          delete series.radius
          delete series.center
        }
      })
    }

    return this.generateHTML(option, html)
  }

  /**
   * 修改显示选项 - 即时生效 ⚡
   */
  changeOptions(html: string, options: StyleOptions): string {
    const option = this.parseChartConfig(html)
    if (!option) return html

    // 数据标签
    if (options.showDataLabel !== undefined) {
      if (option.series && Array.isArray(option.series)) {
        option.series.forEach((series: any) => {
          if (!series.label) {
            series.label = {}
          }
          series.label.show = options.showDataLabel
        })
      }
    }

    // 图例
    if (options.showLegend !== undefined) {
      if (!option.legend) {
        option.legend = {}
      }
      option.legend.show = options.showLegend
    }

    // 网格线
    if (options.showGrid !== undefined) {
      if (!option.grid) {
        option.grid = {}
      }
      option.grid.show = options.showGrid
    }

    // 提示框
    if (options.showTooltip !== undefined) {
      if (!option.tooltip) {
        option.tooltip = {}
      }
      option.tooltip.show = options.showTooltip
    }

    return this.generateHTML(option, html)
  }

  /**
   * 修改尺寸 - 即时生效 ⚡
   */
  changeSize(html: string, size: SizeOptions): string {
    let newHtml = html

    // 修改容器尺寸
    if (size.width) {
      newHtml = newHtml.replace(
        /width:\s*\d+px/g,
        `width: ${size.width}px`
      )
    }

    if (size.height) {
      newHtml = newHtml.replace(
        /height:\s*\d+px/g,
        `height: ${size.height}px`
      )
    }

    return newHtml
  }

  /**
   * 修改标题 - 即时生效 ⚡
   */
  changeTitle(html: string, title: string, subtitle?: string): string {
    let newHtml = html
    
    // 修改HTML中的<h1>标题
    if (title) {
      newHtml = newHtml.replace(
        /<h1[^>]*>.*?<\/h1>/i,
        `<h1>${title}</h1>`
      )
    }
    
    // 如果是ECharts，也修改config中的title
    const option = this.parseChartConfig(newHtml)
    if (option && this.chartLibrary === 'echarts') {
      if (!option.title) {
        option.title = {}
      }
      option.title.text = title
      if (subtitle !== undefined) {
        option.title.subtext = subtitle
      }
      newHtml = this.generateHTML(option, newHtml)
    }

    return newHtml
  }

  /**
   * 生成新的HTML
   */
  generateHTML(option: ChartConfig, originalHtml: string): string {
    try {
      console.log('[ChartEditor] 生成HTML，图表库:', this.chartLibrary)
      
      // 将配置转换为字符串（格式化）
      const optionStr = JSON.stringify(option, null, 2)
      console.log('[ChartEditor] 配置JSON长度:', optionStr.length)

      let newHtml = originalHtml

      if (this.chartLibrary === 'chartjs') {
        // Chart.js: 需要同时替换data和config
        console.log('[ChartEditor] 替换Chart.js config')
        console.log('[ChartEditor] option.data:', JSON.stringify(option.data, null, 2))
        
        // 提取data对象并更新
        if (option.data) {
          const dataStr = JSON.stringify(option.data, null, 2)
          console.log('[ChartEditor] 替换data对象，新内容:', dataStr.substring(0, 200))
          const beforeReplace = newHtml
          newHtml = newHtml.replace(
            /const\s+data\s*=\s*{[\s\S]*?};/,
            `const data = ${dataStr};`
          )
          console.log('[ChartEditor] data替换是否成功:', beforeReplace !== newHtml)
        }
        
        // 替换config对象
        console.log('[ChartEditor] 替换config对象')
        const beforeReplace2 = newHtml
        newHtml = newHtml.replace(
          /const\s+config\s*=\s*{[\s\S]*?};/,
          `const config = ${optionStr};`
        )
        console.log('[ChartEditor] config替换是否成功:', beforeReplace2 !== newHtml)
      } else if (this.chartLibrary === 'echarts') {
        // ECharts: 替换option对象
        console.log('[ChartEditor] 替换ECharts option')
        const optionPattern = /(?:var|let|const)?\s*option\s*=\s*{[\s\S]*?};/
        if (optionPattern.test(newHtml)) {
          newHtml = newHtml.replace(optionPattern, `const option = ${optionStr};`)
        }
        
        const setOptionPattern = /setOption\({[\s\S]*?}\)/
        if (setOptionPattern.test(newHtml)) {
          newHtml = newHtml.replace(setOptionPattern, `setOption(${optionStr})`)
        }
      }

      console.log('[ChartEditor] HTML生成完成，长度:', newHtml.length, '改变:', newHtml !== originalHtml)
      return newHtml
    } catch (e) {
      console.error('[ChartEditor] 生成HTML失败:', e)
      return originalHtml
    }
  }

  /**
   * 获取图表配置摘要（用于显示）
   */
  getConfigSummary(html: string): {
    type: string
    color: string
    hasDataLabel: boolean
    hasLegend: boolean
    hasGrid: boolean
  } | null {
    const option = this.parseChartConfig(html)
    if (!option) return null

    if (this.chartLibrary === 'chartjs') {
      const dataset = option.data?.datasets?.[0]
      const borderColor = Array.isArray(dataset?.borderColor) ? dataset.borderColor[0] : dataset?.borderColor
      const bgColor = Array.isArray(dataset?.backgroundColor) ? dataset.backgroundColor[0] : dataset?.backgroundColor
      return {
        type: option.type || 'unknown',
        color: borderColor || bgColor || '#409eff',
        hasDataLabel: true,
        hasLegend: option.options?.plugins?.legend?.display !== false,
        hasGrid: option.options?.scales?.x?.grid?.display !== false
      }
    } else {
      // ECharts
      return {
        type: option.series?.[0]?.type || 'unknown',
        color: option.color?.[0] || option.series?.[0]?.itemStyle?.color || '#409eff',
        hasDataLabel: option.series?.[0]?.label?.show !== false,
        hasLegend: option.legend?.show !== false,
        hasGrid: option.grid?.show !== false
      }
    }
  }

  /**
   * 验证HTML是否包含有效的ECharts配置
   */
  isValidChartHTML(html: string): boolean {
    return this.parseChartConfig(html) !== null
  }

  /**
   * 批量应用修改
   */
  applyMultipleChanges(
    html: string,
    changes: {
      color?: string
      type?: string
      options?: StyleOptions
      size?: SizeOptions
      title?: string
      subtitle?: string
    }
  ): string {
    console.log('[ChartEditor] 开始批量应用修改:', changes)
    console.log('[ChartEditor] 原始HTML长度:', html.length)
    
    // 先解析配置
    const option = this.parseChartConfig(html)
    if (!option) {
      console.error('[ChartEditor] 无法解析图表配置，返回原HTML')
      return html
    }
    
    console.log('[ChartEditor] 解析成功，图表库:', this.chartLibrary)

    if (this.chartLibrary === 'chartjs') {
      // Chart.js修改
      if (changes.color && option.data?.datasets) {
        console.log('[ChartEditor] 应用Chart.js颜色修改:', changes.color)
        option.data.datasets.forEach((dataset: any) => {
          dataset.borderColor = changes.color
          // 转换为半透明背景色
          const rgba = changes.color!.startsWith('#') 
            ? this.hexToRgba(changes.color!, 0.2)
            : changes.color!.replace(')', ', 0.2)').replace('rgb', 'rgba')
          dataset.backgroundColor = rgba
          if (dataset.pointBackgroundColor) {
            dataset.pointBackgroundColor = changes.color
          }
        })
      }

      if (changes.type) {
        console.log('[ChartEditor] 应用Chart.js类型修改:', changes.type)
        // Chart.js类型映射
        const typeMap: Record<string, string> = {
          'bar': 'bar',
          'line': 'line',
          'pie': 'pie'
        }
        option.type = typeMap[changes.type] || changes.type
      }

      if (changes.options) {
        console.log('[ChartEditor] 应用Chart.js显示选项:', changes.options)
        if (!option.options) option.options = {}
        if (!option.options.plugins) option.options.plugins = {}
        
        if (changes.options.showLegend !== undefined) {
          if (!option.options.plugins.legend) option.options.plugins.legend = {}
          option.options.plugins.legend.display = changes.options.showLegend
        }
        
        if (changes.options.showGrid !== undefined) {
          if (!option.options.scales) option.options.scales = {}
          if (!option.options.scales.x) option.options.scales.x = {}
          if (!option.options.scales.y) option.options.scales.y = {}
          if (!option.options.scales.x.grid) option.options.scales.x.grid = {}
          if (!option.options.scales.y.grid) option.options.scales.y.grid = {}
          option.options.scales.x.grid.display = changes.options.showGrid
          option.options.scales.y.grid.display = changes.options.showGrid
        }
      }
    } else if (this.chartLibrary === 'echarts') {
      // ECharts修改（原有逻辑）
      if (changes.color) {
        console.log('[ChartEditor] 应用ECharts颜色修改:', changes.color)
        option.color = [changes.color]
        if (option.series && Array.isArray(option.series)) {
          option.series.forEach((series: any) => {
            if (!series.itemStyle) series.itemStyle = {}
            series.itemStyle.color = changes.color
          })
        }
      }

      if (changes.type) {
        console.log('[ChartEditor] 应用ECharts类型修改:', changes.type)
        if (option.series && Array.isArray(option.series)) {
          option.series.forEach((series: any) => {
            series.type = changes.type
            if (changes.type === 'line') {
              series.smooth = true
            } else if (changes.type === 'pie') {
              series.radius = ['40%', '70%']
              series.center = ['50%', '50%']
            } else if (changes.type === 'bar') {
              delete series.radius
              delete series.center
            }
          })
        }
      }

      if (changes.options) {
        console.log('[ChartEditor] 应用ECharts显示选项:', changes.options)
        if (changes.options.showDataLabel !== undefined) {
          if (option.series && Array.isArray(option.series)) {
            option.series.forEach((series: any) => {
              if (!series.label) series.label = {}
              series.label.show = changes.options!.showDataLabel
            })
          }
        }
        if (changes.options.showLegend !== undefined) {
          if (!option.legend) option.legend = {}
          option.legend.show = changes.options.showLegend
        }
        if (changes.options.showGrid !== undefined) {
          if (!option.grid) option.grid = {}
          option.grid.show = changes.options.showGrid
        }
        if (changes.options.showTooltip !== undefined) {
          if (!option.tooltip) option.tooltip = {}
          option.tooltip.show = changes.options.showTooltip
        }
      }

      if (changes.title !== undefined) {
        console.log('[ChartEditor] 应用ECharts标题修改:', changes.title)
        if (!option.title) option.title = {}
        option.title.text = changes.title
        if (changes.subtitle !== undefined) {
          option.title.subtext = changes.subtitle
        }
      }
    }

    // 生成新HTML
    let result = this.generateHTML(option, html)
    
    // 应用标题修改（直接替换HTML中的<h1>标签）
    if (changes.title !== undefined && changes.title) {
      console.log('[ChartEditor] 应用HTML标题修改:', changes.title)
      result = result.replace(
        /<h1[^>]*>.*?<\/h1>/i,
        `<h1>${changes.title}</h1>`
      )
    }
    
    // 应用尺寸修改（直接替换HTML）
    if (changes.size) {
      console.log('[ChartEditor] 应用尺寸修改:', changes.size)
      if (changes.size.width) {
        result = result.replace(/width:\s*\d+px/g, `width: ${changes.size.width}px`)
      }
      if (changes.size.height) {
        result = result.replace(/height:\s*\d+px/g, `height: ${changes.size.height}px`)
      }
    }

    console.log('[ChartEditor] 修改完成，新HTML长度:', result.length)
    console.log('[ChartEditor] HTML是否改变:', result !== html)
    
    return result
  }
  
  /**
   * 辅助方法：hex颜色转rgba
   */
  private hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }
}

// 导出单例
export const chartEditor = new ChartEditor()
