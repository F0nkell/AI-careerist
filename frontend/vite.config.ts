import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Разрешаем доступ по локальной сети
    host: true, 
    // Разрешаем любые внешние адреса (туннели)
    allowedHosts: true 
  }
})