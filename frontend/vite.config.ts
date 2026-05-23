import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  define: {
    global: 'globalThis',
  },
  server: {
    port: 5173,
    proxy: {
      '/ws': { 
        target: `wss://${process.env.VITE_API_URL}` || 'ws://localhost:8000',
        ws: true, 
        changeOrigin: true 
      },
      '/api': { 
        target: `https://${process.env.VITE_API_URL}` || 'http://localhost:8000', 
        changeOrigin: true 
      },
    },
  },
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
})