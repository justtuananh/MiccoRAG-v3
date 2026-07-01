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
    port: 5174,
    proxy: {
      '/api': {
        target: 'https://henry-semi-again-dsl.trycloudflare.com',
        changeOrigin: true,
      },
    },
  },
})
