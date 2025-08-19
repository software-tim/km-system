# KM Orchestrator UI

## Deployment

This project deploys to Azure Static Web Apps via GitHub Actions.

### Important Notes

- `package.json` and `astro.config.mjs` are created by the GitHub workflow
- These files are not stored in the repo to avoid BOM encoding issues
- The workflow creates clean UTF-8 files without BOM during deployment

### Local Development

To run locally:

1. Create a temporary `package.json`:
```json
{
  "name": "km-orchestrator-ui",
  "type": "module", 
  "version": "1.0.0",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build"
  },
  "dependencies": {
    "astro": "^4.16.18"
  }
}
```

2. Run: `npm install && npm run dev`

### Deployment URL

After deployment: https://km-orchestrator.azurewebsites.net/diagnostics
