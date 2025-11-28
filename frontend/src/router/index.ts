import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
      meta: { requiresAuth: true, title: '运营数据分析' }
    },
    {
      path: '/operation',
      name: 'operation',
      component: () => import('@/views/Operation/DataAnalysis.vue'),
      meta: { requiresAuth: true, title: '单文件数据分析' }
    },
    {
      path: '/operation/batch',
      name: 'operation-batch',
      component: () => import('@/views/Operation/BatchAnalysis.vue'),
      meta: { requiresAuth: true, title: '批量数据分析' }
    },
    {
      path: '/operation/custom-batch',
      name: 'operation-custom-batch',
      component: () => import('@/views/Operation/CustomBatchAnalysis.vue'),
      meta: { requiresAuth: true, title: '定制化批量数据分析' }
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('@/views/Admin/UserManagement.vue'),
      meta: { 
        requiresAuth: true, 
        requiresAdmin: true,
        title: '用户管理' 
      }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    // 需要登录但未登录，跳转到登录页
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.name === 'login' && authStore.isLoggedIn) {
    // 已登录访问登录页，跳转到首页
    next({ name: 'home' })
  } else if (to.meta.requiresAdmin && !authStore.isSuperadmin) {
    // 需要管理员权限但当前用户不是管理员，跳转到首页
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router

