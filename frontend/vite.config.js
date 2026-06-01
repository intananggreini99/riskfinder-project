import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy untuk pengembangan lokal: arahkan panggilan /api ke backend FastAPI.
    // Saat deploy di Vercel, frontend memakai VITE_DS_API_URL & VITE_CA_API_URL.
    proxy: {
      '/api/ds': {
        target: 'http://localhost:8081',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/ds/, ''),
      },
      '/api/ca': {
        target: 'http://localhost:8082',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/ca/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
