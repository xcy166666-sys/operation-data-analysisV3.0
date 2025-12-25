# 增强图表编辑器 - 工具模块

本目录包含增强图表编辑器的核心工具类和函数。

## 目录结构

```
chart/
├── README.md                 # 本文件
├── index.ts                  # 模块入口，导出所有公共API
├── test-utils.ts             # 测试工具函数
├── setup.test.ts             # 测试基础设施验证
├── ChartParser.ts            # HTML图表解析器（待实现）
├── ChartParser.test.ts       # 解析器测试（待实现）
├── ChartRenderer.ts          # 图表渲染器（待实现）
├── ChartRenderer.test.ts     # 渲染器测试（待实现）
├── ModificationEngine.ts     # 修改引擎（待实现）
└── ModificationEngine.test.ts # 修改引擎测试（待实现）
```

## 核心模块

### ChartParser
负责解析HTML图表并提取ECharts配置、主题信息和系列数据。

主要功能：
- 解析HTML文档并提取嵌入的JavaScript
- 提取ECharts配置对象
- 提取主题信息（背景色、文本色、网格色等）
- 识别所有数据系列
- 验证配置有效性

### ChartRenderer
负责渲染图表并提供实时预览功能。

主要功能：
- 初始化ECharts实例
- 实时更新图表配置
- 处理容器大小和响应式
- 错误处理和恢复

### ModificationEngine
负责处理图表修改并管理撤销/重做历史。

主要功能：
- 应用本地修改（颜色、样式、系列等）
- 路由复杂修改到AI服务
- 管理撤销/重做堆栈
- 批量应用修改

## 测试策略

本项目采用双重测试方法：

### 单元测试
- 使用Vitest作为测试框架
- 测试特定示例和边缘情况
- 测试错误处理
- 测试组件集成

### 基于属性的测试
- 使用fast-check进行属性测试
- 每个属性测试至少100次迭代
- 验证通用正确性属性
- 测试随机生成的输入

## 运行测试

```bash
# 运行所有测试
npm test

# 运行测试并显示UI
npm run test:ui

# 运行测试一次（CI模式）
npm run test:run

# 运行测试并生成覆盖率报告
npm run test:coverage
```

## 开发指南

### 添加新功能
1. 在相应的类文件中实现功能
2. 在对应的测试文件中添加单元测试
3. 如果适用，添加基于属性的测试
4. 更新类型定义（`src/types/chart.ts`）
5. 在`index.ts`中导出新的API

### 测试命名规范
- 单元测试：`*.test.ts`
- 属性测试：在测试描述中标注 `Feature: enhanced-chart-editor, Property N: [描述]`

### 代码风格
- 使用TypeScript严格模式
- 遵循ESLint规则
- 添加JSDoc注释
- 保持函数简洁（单一职责）

## 依赖

- **echarts**: ECharts图表库
- **vitest**: 测试框架
- **fast-check**: 基于属性的测试库
- **@vue/test-utils**: Vue组件测试工具
- **happy-dom**: 轻量级DOM实现
