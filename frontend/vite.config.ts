import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
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
    proxy: {
      // Proxy all API requests to backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Configure proxy logging for debugging
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('❌ Proxy error:', err.message);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('🔄 Proxy:', req.method, req.url, '->', proxyReq.path);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            // Warn about redirects - should be handled by axios now
            if ([301, 302, 307, 308].includes(proxyRes.statusCode)) {
              console.warn('⚠️  Redirect detected:', proxyRes.statusCode, proxyRes.headers.location);
            }
          });
        },
      },
    },
  },
});
