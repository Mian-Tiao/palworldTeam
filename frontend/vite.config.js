import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 本地開發:/api 轉發到 FastAPI(架構文件第 1 節;正式環境同源,無此需求)
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
