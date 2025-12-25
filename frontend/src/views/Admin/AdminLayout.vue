<template>
  <div class="admin-layout">
    <!-- 左侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2 class="system-title">运营数据分析系统</h2>
      </div>
      
      <div class="sidebar-content">
        <div class="nav-section">
          <div class="section-title">全局管理</div>
          <el-menu
            :default-active="activeMenu"
            router
            class="admin-menu"
          >
            <el-menu-item index="/admin/users">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/admin/functions">
              <el-icon><Setting /></el-icon>
              <span>功能管理</span>
            </el-menu-item>
          </el-menu>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <!-- 用户信息 -->
        <div class="user-info-wrapper">
          <div class="user-info" @click.stop="toggleUserMenu">
            <div class="user-avatar">{{ userInitial }}</div>
            <div class="user-details">
              <div class="username">{{ authStore.user?.username || 'admin' }}</div>
              <div class="user-role">超级管理员</div>
            </div>
            <el-icon class="more-icon" :class="{ rotated: showUserMenu }"><MoreFilled /></el-icon>
          </div>
          
          <!-- 个人设置和退出登录菜单（向上弹出，聊天气泡样式） -->
          <transition name="slide-up">
            <div v-show="showUserMenu" class="user-actions-popup" @click.stop>
              <div
                class="action-item"
                :class="{ active: activeMenu === '/admin/settings' }"
                @click="handleGoToSettings"
              >
                <el-icon><Setting /></el-icon>
                <span>个人设置</span>
              </div>
              <div class="action-item" @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </div>
              <!-- 气泡三角形 -->
              <div class="popup-arrow"></div>
            </div>
          </transition>
        </div>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Setting, SwitchButton, MoreFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { logout } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const showUserMenu = ref(false)

const userInitial = computed(() => {
  const username = authStore.user?.username || 'admin'
  return username.charAt(0).toUpperCase()
})

// 切换用户菜单显示/隐藏
const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

// 点击外部区域关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  const userInfoWrapper = document.querySelector('.user-info-wrapper')
  if (userInfoWrapper && !userInfoWrapper.contains(target)) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 跳转到个人设置
const handleGoToSettings = () => {
  showUserMenu.value = false
  router.push({ name: 'admin-settings' })
}

// 退出登录
const handleLogout = async () => {
  showUserMenu.value = false
  
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

    try {
      await logout()
    } catch (error) {
      console.warn('退出登录API调用失败:', error)
    }

    // 清除本地存储
    authStore.logout()
    ElMessage.success('已退出登录')

    // 跳转到登录页
    router.push({ name: 'login' })
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('退出登录失败:', error)
    }
  }
}
</script>

<style scoped lang="scss">
.admin-layout {
  display: flex;
  height: 100vh;
  background-color: #f5f5f5;
}

.sidebar {
  width: 240px;
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  
  .system-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #303133;
  }
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
}

.nav-section {
  .section-title {
    padding: 10px 20px;
    font-size: 12px;
    color: #909399;
    font-weight: 500;
  }
}

.admin-menu {
  border: none;
  
  :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    margin: 4px 10px;
    border-radius: 4px;
    
    &.is-active {
      background-color: #ecf5ff;
      color: #409eff;
    }
    
    &:hover {
      background-color: #f5f7fa;
    }
  }
}

.sidebar-footer {
  padding: 0;
  border-top: 1px solid #e4e7ed;
  position: relative;
  
  .user-info-wrapper {
    position: relative;
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 15px 20px;
    cursor: pointer;
    transition: background-color 0.3s;
    
    &:hover {
      background-color: #f5f7fa;
    }
  }
  
  .user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 16px;
    flex-shrink: 0;
  }
  
  .user-details {
    flex: 1;
    min-width: 0;
    
    .username {
      font-size: 14px;
      font-weight: 500;
      color: #303133;
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .user-role {
      font-size: 12px;
      color: #909399;
    }
  }
  
  .more-icon {
    color: #909399;
    font-size: 16px;
    flex-shrink: 0;
    transition: transform 0.3s;
    
    &.rotated {
      transform: rotate(180deg);
    }
  }
  
  .user-actions-popup {
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background-color: #fff;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    padding: 4px 0;
    z-index: 1000;
    min-width: 160px;
    
    .action-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 20px;
      cursor: pointer;
      color: #606266;
      font-size: 14px;
      transition: all 0.2s;
      white-space: nowrap;
      
      &:hover {
        background-color: #ecf5ff;
        color: #409eff;
        
        .el-icon {
          color: #409eff;
        }
      }
      
      &.active {
        background-color: #ecf5ff;
        color: #409eff;
      }
      
      .el-icon {
        font-size: 16px;
        color: #909399;
        transition: color 0.2s;
      }
      
      &:first-child {
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
      }
      
      &:last-child {
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
      }
    }
    
    // 气泡三角形（指向下方，聊天气泡样式）
    .popup-arrow {
      position: absolute;
      bottom: -6px;
      left: 50%;
      transform: translateX(-50%);
      width: 0;
      height: 0;
      border-left: 6px solid transparent;
      border-right: 6px solid transparent;
      border-top: 6px solid #fff;
      
      // 三角形边框（使用伪元素创建边框效果）
      &::before {
        content: '';
        position: absolute;
        bottom: 1px;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 7px solid transparent;
        border-right: 7px solid transparent;
        border-top: 7px solid #e4e7ed;
        z-index: -1;
      }
    }
  }
}

// 向上弹出动画
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.slide-up-enter-to {
  opacity: 1;
  transform: translateY(0);
}

.slide-up-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f5f5f5;
}
</style>

