import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia'],
      dts: 'src/auto-imports.d.ts',
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,  // Vite 开发服务器端口
    host: '0.0.0.0',  // 监听所有网络接口
    strictPort: true,  // 如果端口被占用，强制使用指定端口
    proxy: {
      '/api': {
        // ==================== 重要配置说明 ====================
        // 开发环境：使用本地后端 http://localhost:8000
        // 生产环境：使用Docker后端 http://localhost:21810
        // 
        // 当前使用：Docker后端
        // 如需切换到本地，修改target为 'http://localhost:8000'
        // ====================================================
        target: 'http://localhost:21810',  // Docker后端
        changeOrigin: true,
        rewrite: (path) => path,  // 保持路径不变
        secure: false,  // 如果是 https，设置为 false
        ws: true,  // 支持WebSocket
      }
    }
  }
})

