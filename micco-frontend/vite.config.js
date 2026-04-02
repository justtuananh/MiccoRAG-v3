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
        target: 'https://propose-montana-refuse-rubber.trycloudflare.com',
        changeOrigin: true,
      },
    },
  },
})
