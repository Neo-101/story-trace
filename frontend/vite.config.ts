import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  // IMPORTANT: Point to the root directory where .env is located (../)
  const envDir = path.resolve(__dirname, '..')
  const env = loadEnv(mode, envDir, '')
  
  // Default to 8000 if not specified
  const API_PORT = env.API_PORT || '8000'
  const API_HOST = env.API_HOST || 'localhost'
  
  console.log(`[Vite Config] Proxying /api to http://${API_HOST}:${API_PORT}`)

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      proxy: {
        '/api': {
          target: `http://${API_HOST}:${API_PORT}`,
          changeOrigin: true,
          secure: false,
          ws: false,
          configure: (proxy, options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('❌ Proxy Error:', err);
            });
            proxy.on('proxyRes', (proxyRes, req, _res) => {
               // Only log errors or non-200 to reduce noise
               if (proxyRes.statusCode !== 200 && proxyRes.statusCode !== 304) {
                 console.log('⬅️ Received Response:', proxyRes.statusCode, req.url);
               }
            });
          },
        },
      },
    },
  }
})
