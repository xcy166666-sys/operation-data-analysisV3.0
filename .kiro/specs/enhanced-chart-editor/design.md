# 设计文档

## 概述

增强图表编辑器是一个用于修改复杂AI生成HTML图表的综合解决方案。它为常见修改提供可视化界面，并为高级定制提供AI驱动的自然语言处理。编辑器解析包含ECharts可视化的完整HTML文档，提取配置对象，并支持实时编辑和即时视觉反馈。

设计采用混合方法：简单修改（颜色、可见性、基本样式）在浏览器中本地处理以获得即时反馈（<100ms），而复杂修改（渐变、自定义动画、数据转换）在需要时利用AI辅助。

## 架构

### 系统组件

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 (Vue 3)                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ ChartEditorModal │  │ PropertyPanels   │               │
│  │ - 全屏UI         │  │ - 系列编辑器      │               │
│  │ - 布局管理器      │  │ - 主题编辑器      │               │
│  │ - 状态管理器      │  │ - 样式编辑器      │               │
│  └──────────────────┘  └──────────────────┘               │
│           │                      │                          │
│           └──────────┬───────────┘                          │
│                      │                                      │
│           ┌──────────▼──────────┐                          │
│           │  ChartParser        │                          │
│           │  - HTML解析         │                          │
│           │  - 配置提取          │                          │
│           │  - 验证             │                          │
│           └──────────┬──────────┘                          │
│                      │                                      │
│           ┌──────────▼──────────┐                          │
│           │  ChartRenderer      │                          │
│           │  - ECharts实例      │                          │
│           │  - 实时更新          │                          │
│           │  - 动画             │                          │
│           └──────────┬──────────┘                          │
│                      │                                      │
│           ┌──────────▼──────────┐                          │
│           │  ModificationEngine │                          │
│           │  - 本地修改          │                          │
│           │  - AI路由           │                          │
│           │  - 撤销/重做         │                          │
│           └─────────────────────┘                          │
│                      │                                      │
└──────────────────────┼──────────────────────────────────────┘
                       │
                       │ HTTP/WebSocket
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  后端 (FastAPI)                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ ChartModService  │  │ AIService        │               │
│  │ - 修改验证        │  │ - Prompt构建     │               │
│  │ - 配置合并        │  │ - LLM接口        │               │
│  └──────────────────┘  └──────────────────┘               │
│           │                      │                          │
│           └──────────┬───────────┘                          │
│                      │                                      │
│           ┌──────────▼──────────┐                          │
│           │  Storage Service    │                          │
│           │  - 图表配置          │                          │
│           │  - 修改日志          │                          │
│           │  - 主题库            │                          │
│           └─────────────────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

#### 本地修改流程（快速路径）
```
用户操作（颜色更改）
    ↓
PropertyPanel发出事件
    ↓
ModificationEngine验证
    ↓
ChartParser应用到配置
    ↓
ChartRenderer更新（<100ms）
    ↓
撤销堆栈更新
```

#### AI修改流程（复杂路径）
```
用户输入自然语言
    ↓
ModificationEngine路由到AI
    ↓
后端AIService处理
    ↓
LLM生成配置更改
    ↓
后端验证更改
    ↓
前端接收更新
    ↓
ChartRenderer应用（带预览）
    ↓
用户确认或拒绝
```

## 组件和接口

### 前端组件

#### 1. ChartEditorModal

提供全屏编辑体验的主容器组件。

**接口：**
```typescript
interface ChartEditorModalProps {
  visible: boolean
  chartHtml: string
  chartId: string
  sessionId?: number
}

interface ChartEditorModalEmits {
  'update:visible': (value: boolean) => void
  'save': (html: string, config: ChartConfig) => void
  'cancel': () => void
}
```

**职责：**
- 管理编辑器生命周期（打开/关闭）
- 协调子组件之间的交互
- 处理保存/取消操作
- 管理加载状态

#### 2. ChartParser

用于解析HTML图表和提取配置的工具类。

**接口：**
```typescript
class ChartParser {
  /**
   * 解析HTML并提取ECharts配置
   */
  parseHTML(html: string): ParseResult
  
  /**
   * 从HTML/配置中提取主题信息
   */
  extractTheme(html: string, config: EChartsOption): ThemeInfo
  
  /**
   * 识别图表中的所有数据系列
   */
  extractSeries(config: EChartsOption): SeriesInfo[]
  
  /**
   * 验证图表配置
   */
  validate(config: EChartsOption): ValidationResult
  
  /**
   * 从配置生成HTML
   */
  generateHTML(config: EChartsOption, theme: ThemeInfo): string
}

interface ParseResult {
  success: boolean
  config: EChartsOption | null
  theme: ThemeInfo | null
  error?: string
}

interface ThemeInfo {
  backgroundColor: string
  textColor: string
  gridColor: string
  colorPalette: string[]
  customCSS?: string
}

interface SeriesInfo {
  id: string
  name: string
  type: 'line' | 'bar' | 'pie' | 'scatter' | string
  color: string | object
  visible: boolean
  data: any[]
}
```

#### 3. ModificationEngine

处理和应用修改的核心逻辑。

**接口：**
```typescript
class ModificationEngine {
  /**
   * 确定修改是否应使用AI
   */
  shouldUseAI(modification: Modification): boolean
  
  /**
   * 应用本地修改
   */
  applyLocal(config: EChartsOption, modification: Modification): EChartsOption
  
  /**
   * 将修改发送到AI服务
   */
  async applyAI(
    config: EChartsOption,
    instruction: string,
    sessionId: number
  ): Promise<AIModificationResult>
  
  /**
   * 将修改添加到撤销堆栈
   */
  pushUndo(state: EditorState): void
  
  /**
   * 撤销上次修改
   */
  undo(): EditorState | null
  
  /**
   * 重做上次撤销的修改
   */
  redo(): EditorState | null
}

interface Modification {
  type: 'color' | 'series' | 'theme' | 'style' | 'data' | 'ai'
  target: string  // 配置属性的路径
  value: any
  metadata?: Record<string, any>
}

interface EditorState {
  config: EChartsOption
  theme: ThemeInfo
  timestamp: number
}
```

### 后端服务

#### 1. ChartModificationService

处理图表修改请求和AI集成。

**接口：**
```python
class ChartModificationService:
    async def modify_chart(
        self,
        chart_id: str,
        current_config: dict,
        modification: dict,
        use_ai: bool = False
    ) -> ModificationResult:
        """
        应用图表配置修改
        
        Args:
            chart_id: 唯一图表标识符
            current_config: 当前ECharts配置
            modification: 要应用的修改
            use_ai: 是否使用AI进行复杂修改
            
        Returns:
            包含更新配置的ModificationResult
        """
        pass
    
    async def ai_modify(
        self,
        current_config: dict,
        instruction: str,
        context: dict
    ) -> AIModificationResult:
        """
        使用AI理解和应用复杂修改
        
        Args:
            current_config: 当前图表配置
            instruction: 自然语言指令
            context: 附加上下文（主题、系列信息等）
            
        Returns:
            包含更改的AIModificationResult
        """
        pass
```

## 数据模型

### 图表配置存储

```typescript
interface StoredChart {
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

interface ModificationRecord {
  id: string
  timestamp: Date
  type: 'local' | 'ai'
  instruction?: string
  changes: Record<string, any>
  appliedBy: string
}
```

## 正确性属性

*属性是在系统的所有有效执行中应该成立的特征或行为——本质上是关于系统应该做什么的正式陈述。属性充当人类可读规范和机器可验证正确性保证之间的桥梁。*

### 正确性属性

基于验收标准分析，以下属性必须对所有有效输入成立：

**属性1：HTML解析往返**
*对于任何*带有嵌入式ECharts配置的有效HTML图表，解析HTML然后从提取的配置生成新HTML应产生功能等效的图表。
**验证：需求1.1, 9.1**

**属性2：主题保留**
*对于任何*具有自定义CSS主题属性（背景颜色、文本颜色、网格颜色、字体）的HTML图表，解析图表应提取所有主题属性，并将这些属性应用于新图表应产生相同的视觉主题。
**验证：需求1.2, 3.1**

**属性3：系列识别完整性**
*对于任何*具有N个数据系列（其中N ≥ 1）的图表配置，解析器应准确识别N个系列，并且每个识别的系列应包含原始配置中的所有属性（名称、类型、颜色、数据）。
**验证：需求1.3, 2.1**

**属性4：颜色调色板提取**
*对于任何*具有自定义颜色调色板数组的图表，解析图表应提取完整的颜色数组，并且提取的颜色应在顺序和值上与原始调色板匹配。
**验证：需求1.4**

**属性5：无效输入的错误处理**
*对于任何*无效的HTML输入（格式错误的结构、缺少必需元素、无效JSON），解析器应返回带有描述性消息的错误结果，并且不应抛出未处理的异常。
**验证：需求1.5**

**属性6：系列隔离**
*对于任何*具有多个系列的图表，修改一个系列的属性（颜色、线条样式、可见性）不应更改配置中任何其他系列的属性。
**验证：需求2.3**

**属性7：切换幂等性**
*对于任何*布尔图表属性（系列可见性、数据标签、工具提示、图例），切换属性两次应恢复原始状态。
**验证：需求2.4, 5.1**

**属性8：系列顺序一致性**
*对于任何*具有多个系列的图表，重新排序系列数组应导致图表图例和视觉显示顺序与新数组顺序匹配。
**验证：需求2.5**

**属性9：主题应用完整性**
*对于任何*主题修改（背景颜色、文本颜色、网格颜色），应用主题应更新所有与主题相关的元素（背景、坐标轴、标签、工具提示、网格线）以使用新的主题颜色。
**验证：需求3.2**

**属性10：预设主题应用**
*对于任何*预设主题和任何图表配置，应用预设主题应导致所有主题属性与预设定义匹配。
**验证：需求3.3**

**属性11：深色模式对比度**
*对于任何*深色模式主题（背景亮度< 50%），所有文本和网格线颜色应与背景颜色具有至少4.5:1的对比度。
**验证：需求3.4**

**属性12：主题持久性**
*对于任何*自定义主题，保存主题然后在不同图表上加载它应导致新图表具有与原始图表相同的主题属性。
**验证：需求3.5**

**属性13：线条样式应用**
*对于任何*线系列和任何有效的线条样式配置（实线/虚线/点线，宽度），应用样式应导致系列配置包含指定的确切样式属性。
**验证：需求4.4**

**属性14：实时更新性能**
*对于任何*简单属性修改（颜色、可见性、基本样式），预览应在修改后的100毫秒内更新。
**验证：需求4.5, 7.1**

**属性15：标签格式应用**
*对于任何*数据系列和任何有效的标签格式（小数位数、百分比、自定义格式），应用格式应导致所有数据标签根据指定格式显示。
**验证：需求5.2**

**属性16：坐标轴配置应用**
*对于任何*坐标轴和任何有效的坐标轴属性（最小值、最大值、间隔、标签旋转），应用属性应导致坐标轴配置包含指定的确切值。
**验证：需求5.3**

**属性17：图例配置应用**
*对于任何*图表和任何有效的图例属性（位置、方向、项目样式），应用属性应导致图例配置包含指定的确切值。
**验证：需求5.5**

**属性18：AI指令理解**
*对于任何*清晰、明确的描述图表修改的自然语言指令，AI服务应以至少85%的准确率识别目标元素和修改类型。
**验证：需求6.1**

**属性19：AI错误处理**
*对于任何*模糊或不清楚的自然语言指令，AI服务应请求澄清或提供建议的替代方案，而不是应用不正确的修改。
**验证：需求6.4**

**属性20：修改历史保留**
*对于任何*修改（本地或AI），修改应添加到历史堆栈，并且历史应包含足够的信息来撤销修改。
**验证：需求6.5, 8.1**

**属性21：撤销-重做往返**
*对于任何*修改序列，执行N次撤销然后N次重做应恢复撤销之前的确切配置状态。
**验证：需求8.2, 8.3**

**属性22：重做堆栈清除**
*对于任何*具有非空重做堆栈的编辑器状态，进行新修改应完全清除重做堆栈。
**验证：需求8.4**

**属性23：撤销历史容量**
*对于任何*超过20次修改的序列，撤销堆栈应恰好包含最近的20个状态，较旧的状态按FIFO顺序删除。
**验证：需求8.5**

**属性24：渲染失败恢复**
*对于任何*导致渲染错误的配置更改，编辑器应显示最后成功渲染的状态，并且不应进入不可恢复的错误状态。
**验证：需求7.5**

**属性25：导出格式正确性**
*对于任何*图表配置，以分辨率R导出为PNG应生成尺寸与R匹配的图像，导出为SVG应生成与预览渲染相同的有效SVG标记。
**验证：需求9.2, 9.3**

**属性26：配置导出往返**
*对于任何*图表配置，将配置导出为JSON然后导入它应产生相同的配置对象。
**验证：需求9.4**

**属性27：复杂图表性能**
*对于任何*具有N个系列（其中N > 10）或M个数据点（其中M > 1000）的图表，初始渲染时间应少于2秒，后续修改应保持至少30帧每秒。
**验证：需求10.1, 10.2, 10.3**

**属性28：资源管理**
*对于任何*编辑器会话，当内存使用超过500MB时，编辑器应清除未使用的预览状态，当浏览器标签页变为非活动状态时，编辑器应暂停预览更新。
**验证：需求10.4, 10.5**

## 错误处理

### 错误类别

**1. 解析错误**
- 无效的HTML结构
- 格式错误的ECharts配置
- 缺少必需元素
- 不支持的图表类型

**策略：** 返回描述性错误并提供修复HTML的建议。

**2. 验证错误**
- 无效的属性值
- 超出范围的数字
- 不兼容的配置
- 缺少必需属性

**策略：** 突出显示无效字段，显示有效范围，在修复之前阻止保存。

**3. 渲染错误**
- ECharts初始化失败
- 浏览器兼容性问题
- 资源加载失败
- 内存耗尽

**策略：** 显示最后有效状态，提供简化渲染模式，记录详细错误以供调试。

**4. AI服务错误**
- API超时
- 速率限制
- 模糊指令
- 服务不可用

**策略：** 显示清晰的错误消息，提供指数退避重试，提供手动编辑的后备方案。

**5. 导出错误**
- 文件系统访问被拒绝
- 不支持的格式
- 超出导出大小限制
- 渲染到图像失败

**策略：** 显示具体错误，建议替代方案（例如降低分辨率），提供重试。

## 测试策略

### 双重测试方法

测试策略结合了针对特定场景的单元测试和全面覆盖的基于属性的测试：

**单元测试：**
- 图表配置的特定示例
- 边缘情况（空系列、单个数据点、极值）
- 错误条件（无效HTML、格式错误的JSON）
- 组件之间的集成点
- UI交互和状态管理

**基于属性的测试：**
- 所有有效输入的通用属性
- 随机图表配置
- 大数据集的压力测试
- 性能验证
- 往返属性（解析-修改-保存-解析）

### 基于属性的测试配置

**测试库：** fast-check（JavaScript/TypeScript基于属性的测试库）

**配置：**
- 每个属性测试最少100次迭代
- 每个测试标记功能名称和属性编号
- 标记格式：`Feature: enhanced-chart-editor, Property N: [属性描述]`

**示例测试结构：**
```typescript
import fc from 'fast-check'
import { describe, it, expect } from 'vitest'
import { ChartParser } from '@/utils/chartParser'

describe('ChartParser属性', () => {
  // Feature: enhanced-chart-editor, Property 1: HTML解析往返
  it('应通过解析-生成循环保留图表功能', () => {
    fc.assert(
      fc.property(
        fc.record({
          series: fc.array(fc.record({
            type: fc.constantFrom('line', 'bar', 'pie'),
            data: fc.array(fc.integer({ min: 0, max: 1000 }), { minLength: 1, maxLength: 100 }),
            name: fc.string(),
            color: fc.hexaColor()
          }), { minLength: 1, maxLength: 10 }),
          title: fc.string(),
          backgroundColor: fc.hexaColor()
        }),
        (config) => {
          const parser = new ChartParser()
          const html = parser.generateHTML(config, {})
          const parsed = parser.parseHTML(html)
          
          expect(parsed.success).toBe(true)
          expect(parsed.config.series.length).toBe(config.series.length)
          // 验证功能等效性
        }
      ),
      { numRuns: 100 }
    )
  })
})
```

### 测试覆盖率目标

- **单元测试覆盖率：** > 80%的代码行
- **属性测试覆盖率：** 100%的正确性属性
- **集成测试覆盖率：** 所有主要用户工作流
- **性能测试覆盖率：** 所有性能关键操作
- **错误处理覆盖率：** 所有错误类别和恢复路径
