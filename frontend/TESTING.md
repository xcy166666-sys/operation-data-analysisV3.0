# 测试指南

本文档说明如何设置和运行增强图表编辑器的测试。

## 安装依赖

首先，确保安装所有测试相关的依赖：

```bash
cd frontend
npm install
```

新增的测试依赖包括：
- `vitest`: 快速的单元测试框架
- `@vitest/ui`: Vitest的UI界面
- `fast-check`: 基于属性的测试库
- `@vue/test-utils`: Vue组件测试工具
- `happy-dom`: 轻量级DOM实现

## 运行测试

### 开发模式（监听文件变化）
```bash
npm test
```

### UI模式（可视化界面）
```bash
npm run test:ui
```
然后在浏览器中打开 http://localhost:51204/__vitest__/

### CI模式（运行一次）
```bash
npm run test:run
```

### 生成覆盖率报告
```bash
npm run test:coverage
```
覆盖率报告将生成在 `coverage/` 目录中。

## 测试结构

### 单元测试
位置：`src/**/*.test.ts`

示例：
```typescript
import { describe, it, expect } from 'vitest'
import { ChartParser } from './ChartParser'

describe('ChartParser', () => {
  it('应该解析有效的HTML', () => {
    const parser = new ChartParser()
    const result = parser.parseHTML('<html>...</html>')
    expect(result.success).toBe(true)
  })
})
```

### 基于属性的测试
使用fast-check进行属性测试：

```typescript
import fc from 'fast-check'

describe('ChartParser属性', () => {
  // Feature: enhanced-chart-editor, Property 1: HTML解析往返
  it('应通过解析-生成循环保留图表功能', () => {
    fc.assert(
      fc.property(
        fc.record({
          series: fc.array(fc.record({
            type: fc.constantFrom('line', 'bar', 'pie'),
            data: fc.array(fc.integer({ min: 0, max: 1000 }))
          }))
        }),
        (config) => {
          const parser = new ChartParser()
          const html = parser.generateHTML(config, {})
          const parsed = parser.parseHTML(html)
          
          expect(parsed.success).toBe(true)
          // 验证功能等效性
        }
      ),
      { numRuns: 100 }
    )
  })
})
```

## 测试覆盖率目标

- 单元测试覆盖率：> 80%
- 属性测试覆盖率：100%的正确性属性
- 集成测试覆盖率：所有主要用户工作流

## 调试测试

### 使用VS Code调试
1. 在测试文件中设置断点
2. 按F5或使用调试面板
3. 选择"Vitest"配置

### 使用console.log
```typescript
it('调试测试', () => {
  const result = someFunction()
  console.log('结果:', result)
  expect(result).toBe(expected)
})
```

### 只运行特定测试
```typescript
it.only('只运行这个测试', () => {
  // ...
})
```

### 跳过测试
```typescript
it.skip('跳过这个测试', () => {
  // ...
})
```

## 常见问题

### Q: 测试运行很慢
A: 尝试使用 `--no-coverage` 选项，或减少属性测试的迭代次数（开发时）。

### Q: 测试在CI中失败但本地通过
A: 检查是否有依赖于时间或随机性的测试。使用固定的种子或mock。

### Q: 如何测试异步代码
A: 使用 `async/await` 或返回Promise：
```typescript
it('异步测试', async () => {
  const result = await asyncFunction()
  expect(result).toBe(expected)
})
```

## 最佳实践

1. **保持测试独立**：每个测试应该能够独立运行
2. **使用描述性名称**：测试名称应该清楚说明测试内容
3. **遵循AAA模式**：Arrange（准备）、Act（执行）、Assert（断言）
4. **避免测试实现细节**：测试行为而不是实现
5. **使用测试工具函数**：复用测试设置代码
6. **保持测试简单**：一个测试只测试一件事

## 参考资源

- [Vitest文档](https://vitest.dev/)
- [fast-check文档](https://fast-check.dev/)
- [Vue Test Utils文档](https://test-utils.vuejs.org/)
