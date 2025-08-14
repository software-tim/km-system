# KM-System - Knowledge Management System

[![km-mcp-sql](https://github.com/software-tim/km-system/actions/workflows/deploy-km-sql.yml/badge.svg)](https://github.com/software-tim/km-system/actions/workflows/deploy-km-sql.yml)
[![km-mcp-sql-docs](https://github.com/software-tim/km-system/actions/workflows/deploy-km-docs.yml/badge.svg)](https://github.com/software-tim/km-system/actions/workflows/deploy-km-docs.yml)

## 🚀 Automated Deployment Active

All services are automatically deployed via GitHub Actions when changes are pushed to the master branch.

## 📦 Services

### km-mcp-sql
- **URL**: https://km-mcp-sql.azurewebsites.net
- **Purpose**: SQL database operations and analytics
- **Status Endpoint**: `/api/status`
- **API Docs**: `/docs`

### km-mcp-sql-docs
- **URL**: https://km-mcp-sql-docs.azurewebsites.net
- **Purpose**: Document storage and management
- **Health Check**: `/health`
- **API Docs**: `/docs`

## 🔧 Development Workflow

1. Make changes locally
2. Test locally: `python app.py`
3. Commit changes: `git commit -m "your message"`
4. Push to GitHub: `git push origin master`
5. ✨ Automatic deployment via GitHub Actions!

## 📊 Monitoring

- **GitHub Actions**: [View Deployments](https://github.com/software-tim/km-system/actions)
- **Azure Portal**: [Azure Dashboard](https://portal.azure.com)

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI
- **Database**: Azure SQL Database
- **Hosting**: Azure Web Apps
- **CI/CD**: GitHub Actions
- **Protocol**: MCP (Model Context Protocol)

## 📝 Last Updated
2025-08-14 14:19:05

---
*Automated deployment configured and operational*
