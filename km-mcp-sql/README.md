# KM-MCP-SQL Server

Knowledge Management SQL Database Interface - A FastAPI-based service for Azure SQL Database operations.

## Overview

This is a FastAPI implementation of the MCP SQL Server, redesigned for the Knowledge Management system with:
- ✅ FastAPI framework (converted from Flask)
- ✅ SQLAlchemy ORM integration
- ✅ Azure SQL Database connection
- ✅ No Docker required - Azure Web App native deployment
- ✅ Python 3.10 compatibility

## Features

- **8 SQL Tools**: Query execution, schema exploration, data analysis
- **Interactive Visualizations**: Plotly-based charts and graphs
- **Jupyter Notebook Generation**: Automated analysis code creation
- **Security Controls**: Granular permissions for write operations
- **RESTful API**: OpenAPI/Swagger documentation included
- **Azure-Ready**: Optimized for Azure Web App deployment

## Project Structure

```
km-mcp-sql/
├── app.py                    # Main FastAPI application
├── km_sql_operations.py      # SQL operations with SQLAlchemy
├── km_sql_schemas.py         # Pydantic models for validation
├── km_config.py              # Configuration management
├── km_sql_interface.html     # Web UI (optional)
├── requirements.txt          # Python dependencies
├── startup.txt               # Azure startup command
├── .env.example             # Environment template
├── .deployment              # Azure deployment config
└── README.md                # This file
```

## Installation

### Local Development

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/km-system.git
cd km-system/km-mcp-sql
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your Azure SQL credentials
```

5. **Run the server**:
```bash
uvicorn app:app --reload --port 8000
```

6. **Access the application**:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## Configuration

### Required Environment Variables

```bash
# Azure SQL Database
KM_SQL_SERVER=knowledge-base-sql-server.database.windows.net
KM_SQL_DATABASE=km-database
KM_SQL_USERNAME=your-username
KM_SQL_PASSWORD=your-password

# Security (optional)
ALLOW_WRITE_OPERATIONS=false
API_KEY=your-secret-key
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web interface |
| GET | `/api/status` | Service status |
| GET | `/api/tools` | List available tools |
| POST | `/api/tools/{tool_name}` | Execute a tool |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API docs |

### Tool Execution

Execute SQL query:
```bash
curl -X POST http://localhost:8000/api/tools/sql_query \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "query": "SELECT TOP 10 * FROM Customers"
    }
  }'
```

Get database info:
```bash
curl -X POST http://localhost:8000/api/tools/get_database_info \
  -H "Content-Type: application/json" \
  -d '{"arguments": {}}'
```

## Available Tools

1. **sql_query** - Execute SQL queries
2. **get_database_info** - Get server and database information
3. **show_tables** - List all tables
4. **describe_table** - Get table structure
5. **show_indexes** - Display indexes
6. **get_schema** - Complete database schema
7. **generate_visualization** - Create charts from data
8. **generate_analysis_notebook** - Generate Jupyter notebooks

## Azure Deployment

### Prerequisites

- Azure subscription
- Azure SQL Database provisioned
- Azure Web App created (Python 3.10)

### Deployment Steps

1. **Configure Azure Web App**:
   - Runtime Stack: Python 3.10
   - Startup Command: `python -m uvicorn app:app --host 0.0.0.0 --port 8000`

2. **Set Application Settings** in Azure Portal:
```
KM_SQL_SERVER=your-server.database.windows.net
KM_SQL_DATABASE=your-database
KM_SQL_USERNAME=your-username
KM_SQL_PASSWORD=your-password
WEBSITES_PORT=8000
```

3. **Deploy via GitHub Actions**:
```bash
# Get publish profile from Azure Portal
# Add as GitHub secret: KM_MCP_SQL_PUBLISH_PROFILE
git push origin main
```

4. **Manual deployment**:
```bash
az webapp up --name km-mcp-sql --resource-group km --runtime "PYTHON:3.10"
```

## Testing

Run tests locally:
```bash
pytest tests/ --verbose
```

Test API endpoints:
```python
import httpx

# Test status endpoint
response = httpx.get("http://localhost:8000/api/status")
print(response.json())

# Test SQL query
response = httpx.post(
    "http://localhost:8000/api/tools/sql_query",
    json={"arguments": {"query": "SELECT 1 as test"}}
)
print(response.json())
```

## Security

- Write operations disabled by default
- Optional API key authentication
- CORS configuration for specific origins
- SQL injection protection via parameterized queries
- Azure SQL encryption enabled

## Monitoring

- Health check: `/health`
- Status endpoint: `/api/status`
- Azure Application Insights (when configured)
- Structured logging throughout

## Troubleshooting

### Connection Issues

Check Azure SQL firewall rules:
```sql
-- Allow Azure services
EXEC sp_set_firewall_rule @name = N'AllowAzure',
    @start_ip_address = '0.0.0.0',
    @end_ip_address = '0.0.0.0';
```

### Module Import Errors

Ensure ODBC driver is installed:
```bash
# On Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### Performance Issues

- Adjust `QUERY_TIMEOUT` in environment variables
- Check Azure SQL DTU usage
- Enable connection pooling in SQLAlchemy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- Create an issue in GitHub
- Check Azure Web App logs
- Review API documentation at `/docs`

---

**Version**: 1.0.0  
**Author**: KM Team  
**Last Updated**: August 2025