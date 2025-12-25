<template>
  <div 
    class="chart-container"
    :class="{ 'is-hovered': isHovered, 'is-selected': isSelected }"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @click="handleClick"
  >
    <!-- 图表内容插槽 -->
    <div class="chart-content-wrapper">
      <slot></slot>
    </div>

    <!-- 选中标记 -->
    <div v-if="isSelected" class="selected-badge">
      <el-icon><Select /></el-icon>
      <span>已选中</span>
    </div>

    <!-- 悬停工具栏 -->
    <transition name="slide-up">
      <div v-show="isHovered || isSelected" class="chart-toolbar">
        <el-button-group size="small">
          <el-button @click.stop="handleQuickEdit('color')">
            <el-icon><Brush /></el-icon>
            改颜色
          </el-button>
          <el-button @click.stop="handleQuickEdit('type')">
            <el-icon><TrendCharts /></el-icon>
            换类型
          </el-button>
          <el-button @click.stop="handleAIEdit" type="primary">
            <el-icon><ChatDotRound /></el-icon>
            AI修改
          </el-button>
        </el-button-group>
      </div>
    </transition>

    <!-- 新手提示 -->
    <transition name="fade">
      <div v-if="showHint && isHovered && !hasInteracted" class="hover-hint">
        💡 点击可以编辑这个图表
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElButton, ElButtonGroup, ElIcon } from 'element-plus'
import { Brush, TrendCharts, ChatDotRound, Select } from '@element-plus/icons-vue'

interface Props {
  chartId: string
  selected?: boolean
  showHint?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selected: false,
  showHint: true
})

const emit = defineEmits<{
  'select': [chartId: string]
  'quick-edit': [chartId: string, type: string]
  'ai-edit': [chartId: string]
}>()

const isHovered = ref(false)
const hasInteracted = ref(false)

const isSelected = computed(() => props.selected)

const handleMouseEnter = () => {
  isHovered.value = true
}

const handleMouseLeave = () => {
  isHovered.value = false
}

const handleClick = () => {
  hasInteracted.value = true
  emit('select', props.chartId)
}

const handleQuickEdit = (type: string) => {
  hasInteracted.value = true
  emit('quick-edit', props.chartId, type)
}

const handleAIEdit = () => {
  hasInteracted.value = true
  emit('ai-edit', props.chartId)
}
</script>

<style scoped lang="scss">
.chart-container {
  position: relative;
  border: 2px solid transparent;
  border-radius: 8px;
  transition: all 0.3s ease;
  margin: 16px 0;
  background: #fff;
  
  &.is-hovered {
    border-color: #409eff;
    box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
  }
  
  &.is-selected {
    border-color: #409eff;
    box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
    background: #f0f7ff;
  }
}

.chart-content-wrapper {
  position: relative;
  min-height: 300px;
}

.selected-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: #409eff;
  color: #fff;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  z-index: 10;
  animation: fadeIn 0.3s ease;
}

.chart-toolbar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: rgba(255, 255, 255, 0.98);
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: center;
  backdrop-filter: blur(8px);
  z-index: 10;
}

.hover-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 9;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
