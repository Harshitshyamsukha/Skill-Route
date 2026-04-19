import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy /api/* requests to the FastAPI backend during development only.
      // In production the reverse proxy (nginx / Caddy) handles routing.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Strip console.* calls from production builds to avoid leaking
    // implementation details and internal values in the browser devtools.
    minify: 'esbuild',
    rollupOptions: {
      output: {
        // Content-hash filenames prevent stale caches from serving old JS
        entryFileNames:  'assets/[name]-[hash].js',
        chunkFileNames:  'assets/[name]-[hash].js',
        assetFileNames:  'assets/[name]-[hash].[ext]',
      },
    },
  },
})
