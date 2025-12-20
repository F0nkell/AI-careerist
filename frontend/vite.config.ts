import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: true,
    // Проксирование для локальной разработки
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Бэкенд
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '') // Убираем /api при пересылке
      }
    }
  }
})