import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./frontend', import.meta.url)) },
  },
  base: '/static/',
  server: { origin: 'http://localhost:5173' },
  build: {
    manifest: 'manifest.json',
    outDir: 'frontend/dist',
    rollupOptions: { input: 'frontend/app.tsx' },
  },
});
