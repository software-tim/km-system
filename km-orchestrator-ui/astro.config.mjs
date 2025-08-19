import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  build: {
    format: 'directory'
  },
  site: 'https://km-orchestrator.azurewebsites.net',
  base: '/diagnostics'
});
