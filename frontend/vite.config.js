import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 关键配置！
      '/api': 'http://localhost:8000'
    }
  }
});
