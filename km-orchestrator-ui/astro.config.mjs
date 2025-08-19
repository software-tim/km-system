import { defineConfig } from 'astro/config';
import node from '@astrojs/node';

export default defineConfig({
  // SSR configuration for Azure App Service
  output: 'server',
  adapter: node({
    mode: 'standalone'
  }),
  
  // Base configuration for your Azure domain
  site: 'https://km-orchestrator.azurewebsites.net',
  
  // Server configuration
  server: {
    port: process.env.PORT || 4321,
    host: true
  },
  
  // Vite configuration for Azure
  vite: {
    define: {
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'production')
    }
  }
});
