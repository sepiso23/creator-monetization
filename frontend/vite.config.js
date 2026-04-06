import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
      alias: {
        '@': '/src', // Maps '@' to the '/src' directory
      },
    },
  server: {
	  allowedHosts: ['7673-45-215-251-110.ngrok-free.app'],
  }
})
