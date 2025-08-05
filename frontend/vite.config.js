import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 以 /api 开头的请求会被代理到后端服务器
      '/api': {
        // 目标后端地址, 也就是我的 Flask 服务器地址
        target: 'http://127.0.0.1:8000',
        // 是否修改 请求头 中的 origin, 这样可以防止部分服务拒绝请求
        changeOrigin: true,
        // 关闭安全校验 (开发的时候用)
        secure: false,
        logLevel: 'debug',
      },
      // 以 /pdfs 开头的请求也代理到后端服务器
      '/pdfs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
      }
    }
  }
})