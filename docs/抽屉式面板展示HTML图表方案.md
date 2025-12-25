# 抽屉式面板展示HTML图表技术方案

## 📋 需求分析

### 当前问题
- HTML图表在iframe中显示，受iframe尺寸限制
- 图表可能被压缩，比例不协调
- 用户无法充分利用屏幕空间查看图表

### 目标效果
- 点击"运行"或"查看图表"按钮后，右侧展开一个大的抽屉式面板
- 面板占据屏幕右侧50%或更多空间
- HTML内容直接注入到面板容器中渲染（不使用iframe）
- 支持关闭面板，返回主视图
- 流畅的动画过渡效果

## 🎯 技术方案概述

### 核心思路
1. **预先准备隐藏容器**：在页面中准备一个足够大的侧边面板容器（默认隐藏）
2. **动态注入HTML**：将生成的HTML内容直接注入到面板容器中
3. **滑入动画**：通过CSS动画将面板从右侧滑入视图
4. **安全渲染**：使用DOMPurify等工具清理HTML，确保安全

### 技术选型

#### 方案A：Element Plus Drawer组件（推荐）
- ✅ 成熟稳定，开箱即用
- ✅ 内置动画效果
- ✅ 响应式适配
- ✅ 支持遮罩层和ESC关闭
- ✅ 与现有UI框架一致

#### 方案B：自定义抽屉组件
- ✅ 完全自定义样式和动画
- ⚠️ 需要自己实现动画和交互逻辑
- ⚠️ 开发工作量大

#### 方案C：第三方抽屉库（如vue-drawer）
- ✅ 功能丰富
- ⚠️ 增加依赖
- ⚠️ 可能与Element Plus样式冲突

**推荐使用方案A：Element Plus Drawer组件**

## 🏗️ 架构设计

### 1. 页面结构设计

```
┌─────────────────────────────────────────────────────────┐
│  主内容区（报告文字 + 操作按钮）                        │
│                                                         │
│  [查看图表] 按钮                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
                              │
                              │ 点击按钮
                              ↓
┌─────────────────────────────────────────────────────────┐
│  主内容区（缩小）    │  抽屉面板（展开）                │
│                      │                                  │
│  报告文字...         │  ┌──────────────────────────┐  │
│                      │  │  图表标题                 │  │
│  [关闭面板] 按钮     │  │  [关闭] [下载] [全屏]    │  │
│                      │  ├──────────────────────────┤  │
│                      │  │                          │  │
│                      │  │    HTML图表内容           │  │
│                      │  │    （直接渲染）          │  │
│                      │  │                          │  │
│                      │  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2. 组件结构

```
DataAnalysis.vue
├── 主内容区
│   ├── 报告文字
│   └── [查看图表] 按钮
└── ChartDrawer.vue (新组件)
    ├── el-drawer (Element Plus)
    └── HTML内容渲染区
        └── v-html (使用DOMPurify清理)
```

## 📝 详细实现方案

### 阶段1：创建抽屉组件

#### 1.1 创建 ChartDrawer.vue 组件

```vue
<!-- frontend/src/views/Operation/components/ChartDrawer.vue -->
<template>
  <el-drawer
    v-model="visible"
    title="图表详情"
    :size="drawerSize"
    direction="rtl"
    :before-close="handleClose"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
    class="chart-drawer"
  >
    <template #header>
      <div class="drawer-header">
        <h3>{{ title }}</h3>
        <div class="header-actions">
          <el-button 
            :icon="Download" 
            size="small"
            @click="handleDownload"
          >
            下载图表
          </el-button>
          <el-button 
            :icon="FullScreen" 
            size="small"
            @click="handleFullscreen"
          >
            全屏
          </el-button>
        </div>
      </div>
    </template>
    
    <div class="chart-content" v-if="htmlContent">
      <!-- 直接渲染HTML内容（已清理） -->
      <div 
        v-html="sanitizedHtml" 
        class="chart-html-content"
        ref="chartContentRef"
      ></div>
    </div>
    
    <div v-else class="chart-empty">
      <el-empty description="暂无图表内容" />
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElDrawer, ElButton, ElEmpty } from 'element-plus'
import { Download, FullScreen } from '@element-plus/icons-vue'
import DOMPurify from 'dompurify'

interface Props {
  modelValue: boolean
  htmlContent?: string
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  htmlContent: '',
  title: '图表详情'
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'close': []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const drawerSize = computed(() => {
  // 响应式尺寸：桌面端50%，平板40%，移动端80%
  if (window.innerWidth < 768) {
    return '80%'
  } else if (window.innerWidth < 1024) {
    return '40%'
  } else {
    return '50%'
  }
})

// 清理HTML内容（安全处理）
const sanitizedHtml = computed(() => {
  if (!props.htmlContent) return ''
  
  // 使用DOMPurify清理HTML
  return DOMPurify.sanitize(props.htmlContent, {
    ALLOWED_TAGS: [
      'html', 'head', 'body', 'title', 'meta', 'link', 'script',
      'style', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'button', 'select', 'option', 'input', 'canvas', 'svg',
      'table', 'thead', 'tbody', 'tr', 'th', 'td', 'a', 'img', 'br', 'hr',
      'ul', 'ol', 'li', 'strong', 'em', 'pre', 'code', 'blockquote'
    ],
    ALLOWED_ATTR: [
      'class', 'id', 'style', 'title', 'data-*',
      'src', 'href', 'rel', 'type', 'charset', 'name', 'content',
      'width', 'height', 'alt', 'target'
    ],
    ALLOW_DATA_ATTR: true
  })
})

const chartContentRef = ref<HTMLElement | null>(null)

// 关闭面板
const handleClose = () => {
  visible.value = false
  emit('close')
}

// 下载图表
const handleDownload = () => {
  // 实现下载逻辑（截图或导出数据）
  console.log('下载图表')
}

// 全屏显示
const handleFullscreen = () => {
  // 实现全屏逻辑
  if (chartContentRef.value) {
    if (chartContentRef.value.requestFullscreen) {
      chartContentRef.value.requestFullscreen()
    }
  }
}

// 监听窗口大小变化，调整抽屉尺寸
watch(() => window.innerWidth, () => {
  // drawerSize是computed，会自动更新
}, { immediate: true })
</script>

<style scoped lang="scss">
.chart-drawer {
  :deep(.el-drawer__body) {
    padding: 0;
    overflow: auto;
  }
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }
  
  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.chart-content {
  width: 100%;
  height: 100%;
  overflow: auto;
  
  .chart-html-content {
    width: 100%;
    min-height: 100%;
    
    // 确保HTML内容样式正确
    :deep(*) {
      box-sizing: border-box;
    }
    
    // 确保图表容器占满空间
    :deep(canvas),
    :deep(.chart),
    :deep([id*="chart"]) {
      max-width: 100%;
      height: auto;
    }
  }
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}
</style>
```

### 阶段2：集成到主组件

#### 2.1 修改 DataAnalysis.vue

```vue
<!-- frontend/src/views/Operation/DataAnalysis.vue -->
<template>
  <div class="data-analysis-page">
    <!-- ... 现有内容 ... -->
    
    <!-- 报告显示区 -->
    <div class="report-section" v-if="reportContent">
      <!-- ... 报告文字 ... -->
      
      <!-- HTML图表显示区域（改为按钮触发抽屉） -->
      <div v-if="reportContent && reportContent.html_charts" class="chart-action-section">
        <el-button 
          type="primary" 
          :icon="View"
          size="large"
          @click="openChartDrawer"
        >
          查看图表详情
        </el-button>
        <el-button 
          type="success" 
          :icon="Download"
          size="large"
          @click="downloadChart"
        >
          下载图表
        </el-button>
      </div>
      
      <!-- 保留原有的iframe显示（可选，作为小预览） -->
      <div class="html-charts-preview" v-if="reportContent && reportContent.html_charts">
        <div class="preview-header">
          <span>图表预览</span>
          <el-button 
            type="text" 
            size="small"
            @click="openChartDrawer"
          >
            查看大图
          </el-button>
        </div>
        <iframe
          :srcdoc="reportContent.html_charts"
          class="html-charts-iframe-preview"
          frameborder="0"
          sandbox="allow-scripts allow-same-origin"
        ></iframe>
      </div>
    </div>
    
    <!-- 图表抽屉组件 -->
    <ChartDrawer
      v-model="showChartDrawer"
      :html-content="reportContent?.html_charts"
      title="图表详情"
      @close="handleChartDrawerClose"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import ChartDrawer from './components/ChartDrawer.vue'
import { View, Download } from '@element-plus/icons-vue'

// 图表抽屉状态
const showChartDrawer = ref(false)

// 打开图表抽屉
const openChartDrawer = () => {
  if (reportContent.value?.html_charts) {
    showChartDrawer.value = true
  } else {
    ElMessage.warning('暂无图表内容')
  }
}

// 关闭图表抽屉
const handleChartDrawerClose = () => {
  showChartDrawer.value = false
}

// 下载图表
const downloadChart = () => {
  // 实现下载逻辑
  console.log('下载图表')
}
</script>
```

### 阶段3：安全处理

#### 3.1 安装 DOMPurify

```bash
cd frontend
npm install dompurify
npm install --save-dev @types/dompurify
```

#### 3.2 HTML清理配置

```typescript
// frontend/src/utils/htmlSanitizer.ts
import DOMPurify from 'dompurify'

export const sanitizeHtml = (html: string): string => {
  return DOMPurify.sanitize(html, {
    // 允许的标签
    ALLOWED_TAGS: [
      'html', 'head', 'body', 'title', 'meta', 'link', 'script',
      'style', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'button', 'select', 'option', 'input', 'canvas', 'svg',
      'table', 'thead', 'tbody', 'tr', 'th', 'td', 'a', 'img', 'br', 'hr',
      'ul', 'ol', 'li', 'strong', 'em', 'pre', 'code', 'blockquote'
    ],
    // 允许的属性
    ALLOWED_ATTR: [
      'class', 'id', 'style', 'title', 'data-*',
      'src', 'href', 'rel', 'type', 'charset', 'name', 'content',
      'width', 'height', 'alt', 'target', 'onclick', 'onchange'
    ],
    // 允许data-*属性
    ALLOW_DATA_ATTR: true,
    // 允许的URL协议
    ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp|data):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
    // 保留相对URL
    KEEP_CONTENT: true
  })
}
```

### 阶段4：样式和动画优化

#### 4.1 抽屉样式定制

```scss
// frontend/src/views/Operation/components/ChartDrawer.vue
<style scoped lang="scss">
.chart-drawer {
  // 自定义抽屉样式
  :deep(.el-drawer) {
    box-shadow: -4px 0 20px rgba(0, 0, 0, 0.15);
  }
  
  :deep(.el-drawer__header) {
    padding: 20px;
    border-bottom: 1px solid var(--el-border-color-light);
    margin-bottom: 0;
  }
  
  :deep(.el-drawer__body) {
    padding: 0;
    height: calc(100% - 60px);
    overflow: auto;
  }
}

.chart-content {
  padding: 20px;
  background: #fff;
  
  // 确保HTML内容样式正确
  :deep(*) {
    box-sizing: border-box;
  }
  
  // 图表容器样式
  :deep(.container),
  :deep([class*="chart"]) {
    width: 100%;
    max-width: 100%;
  }
  
  // 确保canvas和svg正确显示
  :deep(canvas),
  :deep(svg) {
    max-width: 100%;
    height: auto;
  }
  
  // 按钮样式
  :deep(button) {
    margin: 5px;
  }
}
</style>
```

#### 4.2 响应式适配

```scss
// 响应式抽屉尺寸
@media (max-width: 768px) {
  .chart-drawer {
    :deep(.el-drawer) {
      width: 90% !important;
    }
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .chart-drawer {
    :deep(.el-drawer) {
      width: 50% !important;
    }
  }
}

@media (min-width: 1025px) {
  .chart-drawer {
    :deep(.el-drawer) {
      width: 50% !important;
    }
  }
}
```

## 🔒 安全考虑

### 1. XSS防护

- **使用DOMPurify**：清理所有HTML内容
- **白名单机制**：只允许安全的标签和属性
- **脚本执行**：允许script标签（图表需要），但限制src来源

### 2. CSP（Content Security Policy）

```html
<!-- 在index.html中添加 -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; 
               style-src 'self' 'unsafe-inline'; 
               img-src 'self' data: https:;">
```

### 3. 资源加载限制

- 只允许特定的CDN域名（如cdn.jsdelivr.net）
- 禁止加载外部数据源
- 验证所有URL

## 🎨 用户体验优化

### 1. 动画效果

- **滑入动画**：Element Plus Drawer自带平滑滑入效果
- **遮罩层**：点击遮罩层关闭面板
- **ESC键**：按ESC键关闭面板

### 2. 交互优化

- **全屏按钮**：支持全屏查看图表
- **下载按钮**：支持下载图表为图片
- **响应式尺寸**：根据屏幕大小自动调整面板宽度

### 3. 性能优化

- **懒加载**：只在打开抽屉时渲染HTML内容
- **虚拟滚动**：如果内容很长，考虑虚拟滚动
- **防抖处理**：窗口resize时防抖处理

## 📊 数据流设计

```
用户点击"查看图表"按钮
    ↓
设置 showChartDrawer = true
    ↓
ChartDrawer组件显示
    ↓
获取 reportContent.html_charts
    ↓
DOMPurify清理HTML
    ↓
注入到抽屉内容区（v-html）
    ↓
HTML内容渲染（包括图表、交互等）
    ↓
用户操作（关闭、下载、全屏等）
```

## 🔄 与现有方案对比

### 当前方案（iframe）
- ✅ 安全性高（完全隔离）
- ❌ 尺寸受限
- ❌ 比例可能不协调
- ❌ 无法充分利用屏幕空间

### 新方案（抽屉面板）
- ✅ 尺寸灵活，可占50%屏幕
- ✅ 比例协调，不受iframe限制
- ✅ 用户体验更好
- ✅ 支持全屏查看
- ⚠️ 需要安全处理（DOMPurify）

## 📝 实现步骤

### 阶段1：基础实现（2-3小时）

1. ✅ 安装DOMPurify依赖
2. ✅ 创建ChartDrawer.vue组件
3. ✅ 集成到DataAnalysis.vue
4. ✅ 添加"查看图表"按钮
5. ✅ 测试基本功能

### 阶段2：功能完善（1-2小时）

1. ✅ 添加下载功能
2. ✅ 添加全屏功能
3. ✅ 优化样式和动画
4. ✅ 响应式适配

### 阶段3：安全增强（1小时）

1. ✅ 完善DOMPurify配置
2. ✅ 添加CSP策略
3. ✅ 资源URL验证

### 阶段4：用户体验优化（1小时）

1. ✅ 添加加载状态
2. ✅ 错误处理
3. ✅ 键盘快捷键支持

## 🎯 关键实现要点

### 1. 组件通信

```typescript
// 父组件（DataAnalysis.vue）
const showChartDrawer = ref(false)
const openChartDrawer = () => {
  showChartDrawer.value = true
}

// 子组件（ChartDrawer.vue）
const props = defineProps<{
  modelValue: boolean
  htmlContent?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()
```

### 2. HTML清理

```typescript
import DOMPurify from 'dompurify'

const sanitizedHtml = computed(() => {
  if (!props.htmlContent) return ''
  return DOMPurify.sanitize(props.htmlContent, {
    // 配置...
  })
})
```

### 3. 响应式尺寸

```typescript
const drawerSize = computed(() => {
  if (window.innerWidth < 768) return '80%'
  if (window.innerWidth < 1024) return '40%'
  return '50%'
})
```

## ⚠️ 注意事项

1. **安全性**：必须使用DOMPurify清理HTML，防止XSS攻击
2. **性能**：大量HTML内容可能影响性能，考虑懒加载
3. **兼容性**：确保DOMPurify支持所有需要的HTML特性
4. **样式隔离**：HTML内容样式可能影响主页面，需要适当的CSS作用域

## ✅ 优势总结

1. **用户体验好**：大屏幕查看，不受iframe限制
2. **交互流畅**：Element Plus Drawer自带流畅动画
3. **功能丰富**：支持全屏、下载等操作
4. **响应式**：自动适配不同屏幕尺寸
5. **易于维护**：使用成熟组件，代码简洁

---

**文档版本**：v1.0  
**创建日期**：2025-12-05  
**状态**：方案设计阶段，待实现

