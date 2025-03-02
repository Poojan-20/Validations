import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from "tailwindcss";

// https://vitejs.dev/config/
export default defineConfig({
  css: {
    postcss: {
      plugins: [tailwindcss()],
    },
  },
  plugins: [react()],
  server: {
    proxy: {
      // Proxy all API requests to the Flask backend
      '/get_headers': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/upload': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/progress': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/get_processed_files': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/download_processed': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/get_summary_stats': {
        target: 'http://localhost:5000', // Use your Flask server port here
        changeOrigin: true,
      },
    }
  }
}) 