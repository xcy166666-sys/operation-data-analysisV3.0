<template>
  <el-dialog
    v-model="visible"
    :title="`编辑图表 - ${chartTitle}`"
    width="500px"
    :before-close="handleClose"
  >
    <div class="quick-edit-panel">
      <!-- 颜色修改 -->
      <div class="edit-section">
        <div class="section-title">
          <el-icon><Brush /></el-icon>
          <span>颜色</span>
        </div>
        <div class="color-presets">
          <div 
            v-for="color in colorPresets" 
            :key="color.value"
            class="color-item"
            :class="{ 'is-selected': selectedColor === color.value }"
            :style="{ background: color.value }"
            :title="color.name"
            @click="selectColor(color.value)"
          >
            <el-icon v-if="selectedColor === color.value" class="check-icon">
              <Check />
            </el-icon>
          </div>
        </div>
        <el-input 
          v-model="customColor" 
          placeholder="输入颜色代码，如 #409eff"
          @change="selectColor(customColor)"
          class="custom-color-input"
        >
          <template #prepend>自定义</template>
        </el-input>
      </div>

      <!-- 图表类型 -->
      <div class="edit-section">
        <div class="section-title">
          <el-icon><TrendCharts /></el-icon>
          <span>图表类型</span>
        </div>
        <el-radio-group v-model="selectedType" class="type-group">
          <el-radio-button label="bar">
            <el-icon><Histogram /></el-icon>
            柱状图
          </el-radio-button>
          <el-radio-button label="line">
            <el-icon><TrendCharts /></el-icon>
            折线图
          </el-radio-button>
          <el-radio-button label="pie">
            <el-icon><PieChart /></el-icon>
            饼图
          </el-radio-button>
        </el-radio-group>
      </div>

      <!-- AI自由修改 -->
      <div class="edit-section">
        <div class="section-title">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI修改</span>
        </div>
        <el-input
          v-model="aiInstruction"
          type="textarea"
          :rows="3"
          placeholder="描述你想要的修改，例如：&#10;• 改成渐变色，从蓝色到绿色&#10;• 添加数据标签&#10;• 调整图表大小"
          class="ai-input"
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleApply" :loading="isApplying">
          应用修改
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElDialog, ElButton, ElInput, ElRadioGroup, ElRadioButton, ElIcon, ElMessage } from 'element-plus'
import { Brush, TrendCharts, ChatDotRound, Check, Histogram, PieChart } from '@element-plus/icons-vue'

interface Props {
  modelValue: boolean
  chartId: string
  chartTitle?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  chartTitle: '图表'
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'apply': [modifications: ChartModification]
  'close': []
}>()

interface ChartModification {
  chartId: string
  color?: string
  type?: string
  aiInstruction?: string
}

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 颜色预设
const colorPresets = [
  { name: '蓝色', value: '#409eff' },
  { name: '绿色', value: '#67c23a' },
  { name: '红色', value: '#f56c6c' },
  { name: '橙色', value: '#e6a23c' },
  { name: '紫色', value: '#9c27b0' },
  { name: '青色', value: '#00bcd4' },
  { name: '粉色', value: '#e91e63' },
  { name: '灰色', value: '#909399' }
]

const selectedColor = ref('')
const customColor = ref('')
const selectedType = ref('bar')
const aiInstruction = ref('')
const isApplying = ref(false)

const selectColor = (color: string) => {
  if (color && /^#[0-9A-Fa-f]{6}$/.test(color)) {
    selectedColor.value = color
    customColor.value = color
  } else if (color) {
    ElMessage.warning('请输入正确的颜色代码，如 #409eff')
  }
}

const handleClose = () => {
  visible.value = false
  emit('close')
}

const handleApply = () => {
  const modifications: ChartModification = {
    chartId: props.chartId
  }

  // 收集修改内容
  if (selectedColor.value) {
    modifications.color = selectedColor.value
  }
  
  if (selectedType.value) {
    modifications.type = selectedType.value
  }
  
  if (aiInstruction.value.trim()) {
    modifications.aiInstruction = aiInstruction.value.trim()
  }

  // 检查是否有修改
  if (!modifications.color && !modifications.type && !modifications.aiInstruction) {
    ElMessage.warning('请至少选择一项修改')
    return
  }

  isApplying.value = true
  emit('apply', modifications)
  
  // 模拟应用过程
  setTimeout(() => {
    isApplying.value = false
    handleClose()
  }, 1000)
}

// 重置表单
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    // 打开时重置
    selectedColor.value = ''
    customColor.value = ''
    selectedType.value = 'bar'
    aiInstruction.value = ''
  }
})
</script>

<style scoped lang="scss">
.quick-edit-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.edit-section {
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 14px;
    font-weight: 600;
    color: #303133;
  }
}

.color-presets {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.color-item {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
  
  &.is-selected {
    border-color: #303133;
    box-shadow: 0 0 0 2px #fff, 0 0 0 4px #409eff;
  }
  
  .check-icon {
    color: #fff;
    font-size: 20px;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
  }
}

.custom-color-input {
  :deep(.el-input-group__prepend) {
    background: #f5f7fa;
  }
}

.type-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  
  :deep(.el-radio-button) {
    flex: 1;
    min-width: 120px;
  }
  
  :deep(.el-radio-button__inner) {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    width: 100%;
  }
}

.ai-input {
  :deep(.el-textarea__inner) {
    font-family: inherit;
    line-height: 1.6;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
