import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8080,
    proxy: {
      '/global': {
        target: 'http://127.0.0.1:4096',
        changeOrigin: true
      },
      '/session': {
        target: 'http://127.0.0.1:4096',
        changeOrigin: true
      },
      '/config': {
        target: 'http://127.0.0.1:4096',
        changeOrigin: true
      },
      '/provider': {
        target: 'http://127.0.0.1:4096',
        changeOrigin: true
      },
      '/question': {
        target: 'http://127.0.0.1:4096',
        changeOrigin: true
      },
      '/permission': {
        target: 'http://127.0.0.1:4096',
        changeOrigin: true
      }
    }
  }
})