import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 4018,
    proxy: {
      '/api': 'http://localhost:8000',
      '/tools': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
      '/canvas': 'http://localhost:8000',
      '/onboard': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/pipelines': 'http://localhost:8000',
    },
  },
});