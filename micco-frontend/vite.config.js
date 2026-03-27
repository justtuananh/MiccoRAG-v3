import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    strictPort: true,
    allowedHosts: [
      '.trycloudflare.com'
    ],
    proxy: {
      '/api': {
        target: 'https://basics-name-aid-sherman.trycloudflare.com',
        changeOrigin: true,
      },
    },
  },
})