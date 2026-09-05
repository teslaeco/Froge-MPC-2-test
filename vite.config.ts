import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig(({ isSsrBuild }) => ({
  base: '/',
  ssr: { noExternal: ['zod'] },
  build: isSsrBuild ? { outDir: 'dist/server', copyPublicDir: false, rollupOptions: { output: { entryFileNames: 'index.js' } } } : { outDir: 'dist/client' },
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts'],
    coverage: {
      reporter: ['text'],
    },
  },
}))
