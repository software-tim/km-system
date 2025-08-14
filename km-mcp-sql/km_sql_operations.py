#!/usr/bin/env python3
"""
SQL Operations module using SQLAlchemy for Azure SQL Database
"""

from typing import Any, Dict, List, Optional
import logging
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import nbformat as nbf
import json
from datetime import datetime

from km_config import Settings

logger = logging.getLogger(__name__)


class SQLOperations:
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Build connection string for Azure SQL
        # Using pyodbc driver for Azure SQL
        connection_string = (
            f"mssql+pyodbc://{settings.km_sql_username}:{settings.km_sql_password}"
            f"@{settings.km_sql_server}/{settings.km_sql_database}"
            f"?driver=ODBC+Driver+18+for+SQL+Server"
            f"&encrypt=yes&trust_server_certificate=no"
        )
        
        # Create synchronous engine for operations that don't support async
        self.sync_engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=settings.debug
        )
        
        logger.info(f"Connected to Azure SQL Database: {settings.km_sql_database}")
    
    def is_write_query(self, query: str) -> bool:
        """Check if query is a write operation"""
        query_upper = query.upper().strip()
        write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
        return any(query_upper.startswith(keyword) for keyword in write_keywords)
    
    def check_permissions(self, query: str) -> bool:
        """Check if query is allowed based on settings"""
        if not self.is_write_query(query):
            return True
        
        if not self.settings.allow_write_operations:
            return False
        
        query_upper = query.upper().strip()
        
        if query_upper.startswith('INSERT') and not self.settings.allow_insert:
            return False
        elif query_upper.startswith('UPDATE') and not self.settings.allow_update:
            return False
        elif query_upper.startswith('DELETE') and not self.settings.allow_delete:
            return False
        
        return True
    
    async def sql_query(self, query: str) -> Dict[str, Any]:
        """Execute a SQL query on the Azure SQL Database"""
        if not self.check_permissions(query):
            return {
                "success": False,
                "error": "Permission denied for this operation"
            }
        
        try:
            # Run in thread pool since we're using sync engine
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._execute_query, query)
            return result
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_query(self, query: str) -> Dict[str, Any]:
        """Execute query synchronously"""
        with self.sync_engine.connect() as conn:
            result = conn.execute(text(query))
            
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())
                
                # Convert rows to list of dicts
                row_dicts = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "success": True,
                    "columns": columns,
                    "rows": row_dicts,
                    "row_count": len(row_dicts)
                }
            else:
                conn.commit()
                return {
                    "success": True,
                    "rows_affected": result.rowcount
                }
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Get information about the Azure SQL database"""
        query = """
        SELECT
            @@VERSION AS version,
            @@SERVERNAME AS server_name,
            DB_NAME() AS current_database,
            SYSTEM_USER AS  [current_user]
        """
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._get_database_info, query)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_database_info(self, query: str) -> Dict[str, Any]:
        """Get database info synchronously"""
        with self.sync_engine.connect() as conn:
            result = conn.execute(text(query))
            info = dict(result.fetchone())
            
            # Get databases (might fail due to permissions in Azure SQL)
            try:
                db_result = conn.execute(text("SELECT name FROM sys.databases WHERE state_desc = 'ONLINE' ORDER BY name"))
                databases = [row[0] for row in db_result]
            except:
                databases = [self.settings.km_sql_database]
            
            # Get tables
            tables_query = """
                SELECT
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            tables_result = conn.execute(text(tables_query))
            tables = [dict(row) for row in tables_result]
            
            return {
                "success": True,
                "server_info": info,
                "databases": databases,
                "tables": tables,
                "table_count": len(tables)
            }
    
    async def show_tables(self, schema_name: Optional[str] = None) -> Dict[str, Any]:
        """Show all tables in the current database"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._show_tables, schema_name)
            return result
            
        except Exception as e:
            logger.error(f"Failed to show tables: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _show_tables(self, schema_name: Optional[str]) -> Dict[str, Any]:
        """Show tables synchronously"""
        with self.sync_engine.connect() as conn:
            if schema_name:
                query = """
                SELECT
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = :schema
                ORDER BY TABLE_SCHEMA, TABLE_NAME
                """
                result = conn.execute(text(query), {"schema": schema_name})
            else:
                query = """
                SELECT
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                ORDER BY TABLE_SCHEMA, TABLE_NAME
                """
                result = conn.execute(text(query))
            
            tables = [dict(row) for row in result]
            
            return {
                "success": True,
                "tables": tables,
                "count": len(tables)
            }
    
    async def describe_table(self, table_name: str, schema_name: str = 'dbo') -> Dict[str, Any]:
        """Show detailed information about a specific table's structure"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._describe_table, table_name, schema_name)
            return result
            
        except Exception as e:
            logger.error(f"Failed to describe table: {e}")
            return {
                "success": False,
                "error": str(e),
                "table_name": table_name,
                "schema": schema_name
            }
    
    def _describe_table(self, table_name: str, schema_name: str) -> Dict[str, Any]:
        """Describe table synchronously"""
        with self.sync_engine.connect() as conn:
            # Check if table exists
            check_query = """
                SELECT COUNT(*) as table_exists 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = :table AND TABLE_SCHEMA = :schema
            """
            result = conn.execute(text(check_query), {"table": table_name, "schema": schema_name})
            table_exists = result.scalar()
            
            if not table_exists:
                # Try to find in other schemas
                find_query = """
                    SELECT TABLE_SCHEMA
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = :table
                    ORDER BY TABLE_SCHEMA
                """
                result = conn.execute(text(find_query), {"table": table_name})
                other_schemas = [row[0] for row in result]
                
                if other_schemas:
                    schema_name = other_schemas[0]
                    info_message = f"Table found in '{schema_name}' schema"
                else:
                    return {
                        "success": False,
                        "error": f"Table '{table_name}' not found",
                        "suggestion": "Use 'show_tables' to see available tables"
                    }
            
            # Get column information
            columns_query = """
            SELECT
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.CHARACTER_MAXIMUM_LENGTH,
                c.NUMERIC_PRECISION,
                c.NUMERIC_SCALE,
                c.IS_NULLABLE,
                c.COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS c
            WHERE c.TABLE_NAME = :table AND c.TABLE_SCHEMA = :schema
            ORDER BY c.ORDINAL_POSITION
            """
            
            result = conn.execute(text(columns_query), {"table": table_name, "schema": schema_name})
            columns = [dict(row) for row in result]
            
            # Get row count
            try:
                count_query = f"SELECT COUNT(*) FROM [{schema_name}].[{table_name}]"
                row_count = conn.execute(text(count_query)).scalar()
            except:
                row_count = "Unable to determine"
            
            response = {
                "success": True,
                "table_name": table_name,
                "schema": schema_name,
                "columns": columns,
                "row_count": row_count
            }
            
            if 'info_message' in locals():
                response["info"] = info_message
            
            return response
    
    async def show_indexes(self, table_name: Optional[str] = None, schema_name: str = 'dbo') -> Dict[str, Any]:
        """Show indexes for a table or all tables"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._show_indexes, table_name, schema_name)
            return result
            
        except Exception as e:
            logger.error(f"Failed to show indexes: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _show_indexes(self, table_name: Optional[str], schema_name: str) -> Dict[str, Any]:
        """Show indexes synchronously"""
        with self.sync_engine.connect() as conn:
            if table_name:
                query = """
                SELECT
                    t.name AS table_name,
                    i.name AS index_name,
                    i.type_desc AS index_type,
                    i.is_unique,
                    i.is_primary_key
                FROM sys.indexes i
                INNER JOIN sys.tables t ON i.object_id = t.object_id
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE t.name = :table AND s.name = :schema AND i.type > 0
                ORDER BY t.name, i.name
                """
                result = conn.execute(text(query), {"table": table_name, "schema": schema_name})
            else:
                query = """
                SELECT
                    t.name AS table_name,
                    i.name AS index_name,
                    i.type_desc AS index_type,
                    i.is_unique,
                    i.is_primary_key
                FROM sys.indexes i
                INNER JOIN sys.tables t ON i.object_id = t.object_id
                WHERE i.type > 0
                ORDER BY t.name, i.name
                """
                result = conn.execute(text(query))
            
            indexes = [dict(row) for row in result]
            
            return {
                "success": True,
                "indexes": indexes,
                "count": len(indexes)
            }
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get the database schema information"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._get_schema)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_schema(self) -> Dict[str, Any]:
        """Get schema synchronously"""
        with self.sync_engine.connect() as conn:
            query = """
            SELECT 
                t.TABLE_SCHEMA,
                t.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.IS_NULLABLE,
                c.COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.TABLES t
            JOIN INFORMATION_SCHEMA.COLUMNS c 
                ON t.TABLE_SCHEMA = c.TABLE_SCHEMA 
                AND t.TABLE_NAME = c.TABLE_NAME
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION
            """
            
            result = conn.execute(text(query))
            
            # Organize schema by table
            schema = {}
            for row in result:
                table_key = f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}"
                if table_key not in schema:
                    schema[table_key] = {
                        'schema': row.TABLE_SCHEMA,
                        'table': row.TABLE_NAME,
                        'columns': []
                    }
                
                schema[table_key]['columns'].append({
                    'name': row.COLUMN_NAME,
                    'type': row.DATA_TYPE,
                    'nullable': row.IS_NULLABLE == 'YES',
                    'default': row.COLUMN_DEFAULT
                })
            
            return {
                "success": True,
                "schema": schema,
                "table_count": len(schema)
            }
    
    async def generate_visualization(self, query: str, viz_type: str = "auto", title: Optional[str] = None) -> Dict[str, Any]:
        """Generate visualizations from query results"""
        try:
            # Execute the query first
            result = await self.sql_query(query)
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"SQL query failed: {result.get('error', 'Unknown error')}"
                }
            
            if not result.get('rows'):
                return {
                    "success": False,
                    "error": "Query returned no data"
                }
            
            # Create DataFrame
            df = pd.DataFrame(result['rows'])
            
            # Auto-detect column types
            numeric_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
            
            # Auto-select visualization type
            if viz_type == "auto":
                if len(numeric_cols) >= 2:
                    viz_type = "scatter"
                elif len(numeric_cols) == 1 and len(categorical_cols) >= 1:
                    viz_type = "bar"
                else:
                    viz_type = "table"
            
            # Create visualization
            fig = None
            
            if viz_type == "bar" and len(categorical_cols) > 0 and len(numeric_cols) > 0:
                fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0], title=title or 'Bar Chart')
            elif viz_type == "pie" and len(categorical_cols) > 0 and len(numeric_cols) > 0:
                fig = px.pie(df, names=categorical_cols[0], values=numeric_cols[0], title=title or 'Pie Chart')
            elif viz_type == "line" and len(numeric_cols) >= 1:
                fig = px.line(df, x=df.columns[0], y=numeric_cols[0], title=title or 'Line Chart')
            elif viz_type == "scatter" and len(numeric_cols) >= 2:
                fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title=title or 'Scatter Plot')
            else:
                # Default to table
                fig = go.Figure(data=[go.Table(
                    header=dict(values=list(df.columns), fill_color='paleturquoise', align='left'),
                    cells=dict(values=[df[col] for col in df.columns], fill_color='lavender', align='left'))
                ])
                fig.update_layout(title=title or 'Data Table')
            
            if fig:
                # Convert to JSON for web rendering
                import plotly.utils
                chart_json = plotly.utils.PlotlyJSONEncoder().encode(fig)
                chart_data = json.loads(chart_json)
                
                return {
                    "success": True,
                    "message": f"✅ {viz_type.title()} chart created successfully!",
                    "chart_data": chart_data,
                    "visualization_type": viz_type
                }
            else:
                return {
                    "success": False,
                    "error": "No chart was created"
                }
                
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_analysis_notebook(self, query: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate a Jupyter notebook with analysis code"""
        if output_file is None:
            output_file = "km_sql_analysis.ipynb"
        
        try:
            result = await self.sql_query(query)
            
            if not result.get("success"):
                return result
            
            nb = nbf.v4.new_notebook()
            
            cells = []
            
            cells.append(nbf.v4.new_markdown_cell("# SQL Data Analysis\n\nGenerated by KM-MCP-SQL"))
            
            cells.append(nbf.v4.new_code_cell("""import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

plt.style.use('seaborn-v0_8-darkgrid')
pd.set_option('display.max_columns', None)"""))
            
            data_dict = {
                'columns': result['columns'],
                'data': result['rows']
            }
            
            cells.append(nbf.v4.new_code_cell(f"""# Load data
data = {json.dumps(data_dict, indent=2)}
df = pd.DataFrame(data['data'])
print(f"Data shape: {{df.shape}}")
df.head()"""))
            
            cells.append(nbf.v4.new_markdown_cell("## Data Overview"))
            cells.append(nbf.v4.new_code_cell("df.info()"))
            cells.append(nbf.v4.new_code_cell("df.describe()"))
            
            nb['cells'] = cells
            
            with open(output_file, 'w') as f:
                nbf.write(nb, f)
            
            return {
                "success": True,
                "message": f"Analysis notebook created: {output_file}",
                "notebook_file": output_file
            }
            
        except Exception as e:
            logger.error(f"Notebook generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }