/**
 * 测试工具函数
 * 
 * 提供用于测试的辅助函数和mock数据生成器
 */

import type { EChartsOption } from 'echarts'
import type { ThemeInfo, SeriesInfo } from '@/types/chart'

/**
 * 生成简单的ECharts配置用于测试
 */
export function createMockEChartsConfig(overrides?: Partial<EChartsOption>): EChartsOption {
  return {
    title: {
      text: '测试图表'
    },
    tooltip: {
      show: true
    },
    legend: {
      show: true
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '系列1',
        type: 'line',
        data: [120, 200, 150, 80, 70],
        itemStyle: {
          color: '#409eff'
        }
      }
    ],
    ...overrides
  }
}

/**
 * 生成包含ECharts配置的HTML
 */
export function createMockChartHTML(config: EChartsOption): string {
  const configStr = JSON.stringify(config, null, 2)
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>测试图表</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
  <style>
    body {
      margin: 0;
      padding: 20px;
      background-color: #f5f5f5;
    }
    #chart {
      width: 800px;
      height: 600px;
      background-color: white;
    }
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
</html>
  `.trim()
}

/**
 * 生成mock主题信息
 */
export function createMockTheme(overrides?: Partial<ThemeInfo>): ThemeInfo {
  return {
    backgroundColor: '#ffffff',
    textColor: '#333333',
    gridColor: '#e0e0e0',
    colorPalette: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399'],
    ...overrides
  }
}

/**
 * 生成mock系列信息
 */
export function createMockSeries(overrides?: Partial<SeriesInfo>): SeriesInfo {
  return {
    id: 'series-1',
    name: '系列1',
    type: 'line',
    color: '#409eff',
    visible: true,
    data: [120, 200, 150, 80, 70],
    ...overrides
  }
}

/**
 * 生成多系列图表配置
 */
export function createMultiSeriesConfig(seriesCount: number): EChartsOption {
  const series = Array.from({ length: seriesCount }, (_, i) => ({
    name: `系列${i + 1}`,
    type: 'line' as const,
    data: Array.from({ length: 5 }, () => Math.floor(Math.random() * 200)),
    itemStyle: {
      color: `hsl(${(i * 360) / seriesCount}, 70%, 50%)`
    }
  }))

  return createMockEChartsConfig({ series })
}

/**
 * 生成深色主题配置
 */
export function createDarkThemeConfig(): EChartsOption {
  return createMockEChartsConfig({
    backgroundColor: '#0f0f1c',
    textStyle: {
      color: '#ffffff'
    },
    title: {
      text: '深色主题图表',
      textStyle: {
        color: '#ffffff'
      }
    }
  })
}

/**
 * 比较两个ECharts配置是否相等（忽略函数）
 */
export function compareConfigs(config1: EChartsOption, config2: EChartsOption): boolean {
  const str1 = JSON.stringify(config1, (key, value) => 
    typeof value === 'function' ? undefined : value
  )
  const str2 = JSON.stringify(config2, (key, value) => 
    typeof value === 'function' ? undefined : value
  )
  return str1 === str2
}
