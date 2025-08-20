# 🚀 KM Orchestrator Astro UI - Professional Setup

# Create the project
npm create astro@latest km-orchestrator-ui -- --template minimal --typescript

cd km-orchestrator-ui

# Install core dependencies
npm install @astrojs/tailwind @astrojs/react @astrojs/node
npm install tailwindcss @tailwindcss/typography @tailwindcss/forms
npm install react react-dom
npm install lucide-react framer-motion
npm install @tanstack/react-query axios
npm install zustand
npm install @headlessui/react

# Install dev dependencies
npm install -D @types/react @types/react-dom

# Configure Astro
echo 'import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import react from "@astrojs/react";
import node from "@astrojs/node";

export default defineConfig({
  integrations: [tailwind(), react()],
  output: "server",
  adapter: node({
    mode: "standalone"
  }),
  server: {
    port: 3000,
    host: true
  }
});' > astro.config.mjs

# Create directory structure
mkdir -p src/components/ui
mkdir -p src/components/orchestrator
mkdir -p src/components/dashboard
mkdir -p src/components/chat
mkdir -p src/layouts
mkdir -p src/utils
mkdir -p src/stores
mkdir -p src/types
mkdir -p public/api

echo "📦 Project structure created!"
echo "🎯 Next: Run the component generation scripts"