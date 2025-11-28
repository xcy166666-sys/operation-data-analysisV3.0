<template>
  <div class="report-tabs">
    <el-tabs
      v-model="activeTab"
      type="card"
      @tab-change="handleTabChange"
      class="batch-tabs"
    >
      <el-tab-pane
        v-for="(report, index) in reports"
        :key="report.id"
        :label="getTabLabel(report, index)"
        :name="String(index)"
      >
        <template #label>
          <span class="tab-label">
            <el-icon v-if="report.report_status === 'completed'" class="status-icon success">
              <Check />
            </el-icon>
            <el-icon v-else-if="report.report_status === 'generating'" class="status-icon loading">
              <Loading />
            </el-icon>
            <el-icon v-else-if="report.report_status === 'failed'" class="status-icon error">
              <Close />
            </el-icon>
            <el-icon v-else class="status-icon pending">
              <Clock />
            </el-icon>
            <span class="tab-name">{{ report.sheet_name }}</span>
            <el-tag 
              size="small" 
              :type="getStatusType(report.report_status)"
              class="status-tag"
            >
              {{ getStatusText(report.report_status) }}
            </el-tag>
          </span>
        </template>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Check, Loading, Close, Clock } from '@element-plus/icons-vue'
import type { BatchSheet } from '@/api/operation'

interface Props {
  reports: BatchSheet[]
  currentIndex: number
}

interface Emits {
  (e: 'tab-change', index: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const activeTab = ref(String(props.currentIndex))

watch(() => props.currentIndex, (newIndex) => {
  activeTab.value = String(newIndex)
})

const handleTabChange = (name: string) => {
  const index = parseInt(name)
  emit('tab-change', index)
}

const getTabLabel = (report: BatchSheet, index: number) => {
  return report.sheet_name || `Sheet${index + 1}`
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    'completed': 'success',
    'generating': 'warning',
    'failed': 'danger',
    'pending': 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'completed': '已完成',
    'generating': '分析中',
    'failed': '失败',
    'pending': '待处理'
  }
  return statusMap[status] || status
}
</script>

<style scoped lang="scss">
.report-tabs {
  margin-bottom: 20px;
  
  .batch-tabs {
    :deep(.el-tabs__header) {
      margin: 0;
    }
    
    :deep(.el-tabs__item) {
      padding: 12px 20px;
      height: auto;
    }
    
    .tab-label {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .status-icon {
        font-size: 16px;
        
        &.success {
          color: var(--el-color-success);
        }
        
        &.loading {
          color: var(--el-color-warning);
          animation: rotating 2s linear infinite;
        }
        
        &.error {
          color: var(--el-color-danger);
        }
        
        &.pending {
          color: var(--el-color-info);
        }
      }
      
      .tab-name {
        font-weight: 500;
      }
      
      .status-tag {
        margin-left: 4px;
      }
    }
  }
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
