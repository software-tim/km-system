#!/usr/bin/env python3
"""
Configuration settings for KM-MCP-SQL-DOCS Server
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Azure SQL Database Configuration
    km_sql_server: str = os.getenv('KM_SQL_SERVER', 'knowledge-sql.database.windows.net')
    km_sql_database: str = os.getenv('KM_SQL_DATABASE', 'knowledge-base')
    km_sql_username: str = os.getenv('KM_SQL_USERNAME', '')
    km_sql_password: str = os.getenv('KM_SQL_PASSWORD', '')
    
    # Alternative: Single connection string
    km_sql_connection_string: Optional[str] = os.getenv('KM_SQL_CONNECTION_STRING', None)
    
    # Document-specific settings
    max_file_size: int = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB default
    allowed_file_types: List[str] = os.getenv('ALLOWED_FILE_TYPES', '.pdf,.docx,.txt,.md').split(',')
    
    # API Settings
    api_key: Optional[str] = os.getenv('API_KEY', None)
    allowed_origins: List[str] = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    # Performance Settings
    query_timeout: int = int(os.getenv('QUERY_TIMEOUT', '30000')) // 1000  # Convert to seconds
    max_rows: int = int(os.getenv('MAX_ROWS', '1000'))
    
    # Application Settings
    port: int = int(os.getenv('PORT', '8000'))
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
    
    def get_connection_string(self) -> str:
        """Build or return the connection string"""
        if self.km_sql_connection_string:
            return self.km_sql_connection_string
        
        # Build connection string for Azure SQL
        return (
            f"mssql+pyodbc://{self.km_sql_username}:{self.km_sql_password}"
            f"@{self.km_sql_server}/{self.km_sql_database}"
            f"?driver=ODBC+Driver+18+for+SQL+Server"
            f"&encrypt=yes&trust_server_certificate=no"
        )
