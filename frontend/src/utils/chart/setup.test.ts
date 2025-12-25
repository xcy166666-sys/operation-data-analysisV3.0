/**
 * 测试基础设施验证
 * 
 * 验证Vitest和fast-check是否正确配置
 */

import { describe, it, expect } from 'vitest'
import fc from 'fast-check'
import { createMockEChartsConfig, createMockChartHTML } from './test-utils'

describe('测试基础设施', () => {
  it('Vitest应该正常工作', () => {
    expect(true).toBe(true)
  })

  it('应该能够创建mock配置', () => {
    const config = createMockEChartsConfig()
    expect(config).toBeDefined()
    expect(config.series).toBeDefined()
    expect(config.series).toHaveLength(1)
  })

  it('应该能够创建mock HTML', () => {
    const config = createMockEChartsConfig()
    const html = createMockChartHTML(config)
    expect(html).toContain('<!DOCTYPE html>')
    expect(html).toContain('echarts')
    expect(html).toContain('setOption')
  })

  it('fast-check应该正常工作', () => {
    fc.assert(
      fc.property(fc.integer(), (n) => {
        return n + 0 === n
      })
    )
  })

  it('fast-check应该能够生成字符串', () => {
    fc.assert(
      fc.property(fc.string(), (s) => {
        return s.length >= 0
      }),
      { numRuns: 10 }
    )
  })

  it('fast-check应该能够生成数组', () => {
    fc.assert(
      fc.property(
        fc.array(fc.integer({ min: 0, max: 100 })),
        (arr) => {
          return arr.every(n => n >= 0 && n <= 100)
        }
      ),
      { numRuns: 10 }
    )
  })
})
