import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import process from 'node:process'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    strictPort: true,
    allowedHosts: [
      '.trycloudflare.com'
    ],
    port: 5174,
    proxy: {
      '/api': {
        target: process.env.MICCO_BACKEND_TARGET || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
