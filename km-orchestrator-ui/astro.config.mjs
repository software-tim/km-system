import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

export default defineConfig({
  // Add React integration
  integrations: [react()],
  
  // Build configuration for Azure deployment
  output: 'static',
  build: {
    format: 'directory'
  },
  
  // Ensure correct routing for /diagnostics path
  site: 'https://km-orchestrator.azurewebsites.net',
  base: '/diagnostics'
});
