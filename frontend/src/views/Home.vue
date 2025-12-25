<template>
  <div class="home-page">
    <div class="home-container">
      <div class="welcome-section">
        <div class="header-with-logout">
          <div class="header-title">
            <h1>运营数据分析平台</h1>
            <p class="subtitle">选择分析方式开始使用</p>
          </div>
          <div class="header-actions">
            <el-button 
              type="danger"
              :icon="SwitchButton"
              @click="handleLogout"
            >
              退出登录
            </el-button>
          </div>
        </div>
      </div>

      <div class="options-grid">
        <el-card 
          class="option-card" 
          shadow="hover"
          @click="goToSingleAnalysis"
        >
          <div class="card-content">
            <el-icon class="card-icon" :size="48">
              <Document />
            </el-icon>
            <h2>单文件数据分析</h2>
            <p>上传单个Excel文件，快速生成数据分析报告</p>
            <ul class="feature-list">
              <li>支持 .xlsx 和 .csv 格式</li>
              <li>快速生成分析报告</li>
              <li>包含图表和关键指标</li>
            </ul>
            <el-button type="primary" size="large" class="action-button">
              开始分析
            </el-button>
          </div>
        </el-card>

        <el-card 
          class="option-card" 
          shadow="hover"
          @click="goToBatchAnalysis"
        >
          <div class="card-content">
            <el-icon class="card-icon" :size="48">
              <Files />
            </el-icon>
            <h2>批量数据分析</h2>
            <p>上传包含多个Sheet的Excel文件，批量生成分析报告</p>
            <ul class="feature-list">
              <li>自动拆分多个Sheet</li>
              <li>并发处理提高效率</li>
              <li>统一管理所有报告</li>
            </ul>
            <el-button type="primary" size="large" class="action-button">
              开始批量分析
            </el-button>
          </div>
        </el-card>

        <el-card 
          class="option-card" 
          shadow="hover"
          @click="goToCustomBatchAnalysis"
        >
          <div class="card-content">
            <el-icon class="card-icon" :size="48">
              <Files />
            </el-icon>
            <h2>黄伟斌定制款数据分析工具</h2>
            <p>上传包含多个Sheet的Excel文件，批量生成分析报告</p>
            <ul class="feature-list">
              <li>自动拆分多个Sheet</li>
              <li>并发处理提高效率</li>
              <li>统一管理所有报告</li>
            </ul>
            <el-button type="primary" size="large" class="action-button">
              开始定制化批量分析
            </el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Document, Files, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { logout } from '@/api/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const goToSingleAnalysis = () => {
  router.push({ name: 'operation', query: { new: 'true' } })
}

const goToBatchAnalysis = () => {
  router.push({ name: 'operation-batch', query: { new: 'true' } })
}

const goToCustomBatchAnalysis = () => {
  router.push({ name: 'operation-custom-batch', query: { new: 'true' } })
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用退出登录API（可选）
    try {
      await logout()
    } catch (error) {
      // 即使API调用失败，也继续清除本地认证信息
      console.warn('退出登录API调用失败:', error)
    }
    
    // 清除本地认证信息
    authStore.clearAuth()
    
    // 跳转到登录页面
    router.push({ name: 'login' })
    
    ElMessage.success('已退出登录')
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel') {
      console.error('退出登录失败:', error)
    }
  }
}
</script>

<style scoped lang="scss">
.home-page {
  min-height: 100vh;
  background: var(--apple-bg-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--apple-space-4xl) var(--apple-space-xl);
  
  .home-container {
    max-width: 1200px;
    width: 100%;
    
    .welcome-section {
      margin-bottom: var(--apple-space-4xl);
      
      .header-with-logout {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        width: 100%;
        position: relative;
        
        .header-title {
          flex: 1;
          text-align: center;
        }
        
        .header-actions {
          display: flex;
          gap: var(--apple-space-md);
          align-items: center;
          position: absolute;
          top: 0;
          right: 0;
        }
      }
      
      h1 {
        font-size: var(--apple-font-3xl);
        font-weight: 600;
        color: var(--apple-text-primary);
        margin: 0 0 var(--apple-space-md) 0;
        letter-spacing: -0.5px;
      }
      
      .subtitle {
        font-size: var(--apple-font-lg);
        color: var(--apple-text-secondary);
        margin: 0;
        font-weight: 400;
      }
    }
    
    .options-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--apple-space-xl);
      
      .option-card {
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid var(--apple-border-light);
        background: var(--apple-bg-primary);
        border-radius: var(--apple-radius-lg);
        box-shadow: var(--apple-shadow-md);
        
        &:hover {
          transform: translateY(-4px);
          box-shadow: var(--apple-shadow-lg);
          border-color: var(--apple-primary);
        }
        
        .card-content {
          text-align: center;
          padding: var(--apple-space-xl);
          display: flex;
          flex-direction: column;
          height: 100%;
          
          .card-icon {
            color: var(--apple-primary);
            margin-bottom: var(--apple-space-lg);
          }
          
          h2 {
            font-size: var(--apple-font-xl);
            font-weight: 600;
            color: var(--apple-text-primary);
            margin: 0 0 var(--apple-space-sm) 0;
            letter-spacing: -0.3px;
          }
          
          p {
            font-size: var(--apple-font-sm);
            color: var(--apple-text-secondary);
            margin: 0 0 var(--apple-space-lg) 0;
            line-height: 1.5;
          }
          
          .feature-list {
            text-align: left;
            list-style: none;
            padding: 0;
            margin: 0 0 var(--apple-space-lg) 0;
            flex: 1;
            
            li {
              padding: var(--apple-space-xs) 0;
              color: var(--apple-text-secondary);
              font-size: var(--apple-font-xs);
              position: relative;
              padding-left: var(--apple-space-lg);
              
              &::before {
                content: '✓';
                position: absolute;
                left: 0;
                color: var(--apple-success);
                font-weight: 600;
              }
            }
          }
          
          .action-button {
            width: 100%;
            margin-top: auto;
            font-size: var(--apple-font-sm);
            height: 40px;
            min-height: 40px;
            line-height: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0;
          }
        }
      }
    }
  }
}

@media (max-width: 1200px) {
  .home-page {
    .home-container {
      .options-grid {
        grid-template-columns: repeat(3, 1fr);
        gap: var(--apple-space-lg);
      }
    }
  }
}

@media (max-width: 768px) {
  .home-page {
    padding: var(--apple-space-2xl) var(--apple-space-lg);
    
    .home-container {
      .welcome-section {
        margin-bottom: var(--apple-space-3xl);
        
        h1 {
          font-size: var(--apple-font-2xl);
        }
      }
      
      .options-grid {
        grid-template-columns: 1fr;
        gap: var(--apple-space-2xl);
      }
    }
  }
}
</style>

