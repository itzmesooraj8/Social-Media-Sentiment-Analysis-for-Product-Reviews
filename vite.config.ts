import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true, // Listen on all addresses
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        // CRITICAL: This rewrite prevents the /api/api/dashboard double prefix
        // If the backend expects /api/..., we don't assume we need to rewrite it away unless verified.
        // But typically FastAPI mounts at root. So /api/dashboard -> /api/dashboard.
        // Wait, current backend routes ARE /api/.... 
        // So no rewrite needed if target is root.
        // If frontend calls /api/dashboard, backend gets /api/dashboard. Perfect.
        // BUT if frontend code does api.get('/dashboard') with baseURL='/api', request is /api/dashboard.
        // The issue was likely axios baseURL='/api' PLUS vite proxy '/api'.
        // This config keeps it simple.
      },
    },
  },
});
