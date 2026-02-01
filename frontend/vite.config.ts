import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // 將 sl-* 視為 Shoelace Web Components
          isCustomElement: (tag) => tag.startsWith('sl-')
        }
      }
    })
  ],
  server: {
    port: 5171,
    strictPort: true
  }
})
