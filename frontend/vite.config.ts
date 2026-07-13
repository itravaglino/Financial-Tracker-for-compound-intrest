import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const repoBase = '/Financial-Tracker-for-compound-intrest/'

export default defineConfig({
  plugins: [react()],
  base: process.env.GITHUB_PAGES === 'true' ? repoBase : '/',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
})
