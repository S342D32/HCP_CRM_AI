import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            // Any request starting with /api gets forwarded to Flask
            // The browser only sees localhost:5173 so CORS never triggers
            '/api': {
                target: 'http://localhost:5000',
                changeOrigin: true
            }
        }
    }
})
