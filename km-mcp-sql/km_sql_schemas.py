#!/usr/bin/env python3
"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution"""
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific arguments")


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution"""
    success: bool
    content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tool: str
    timestamp: datetime


class DatabaseInfoResponse(BaseModel):
    """Response model for database info"""
    success: bool
    server_info: Optional[Dict[str, Any]] = None
    databases: Optional[List[str]] = None
    tables: Optional[List[Dict[str, Any]]] = None
    table_count: Optional[int] = None
    error: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for SQL queries"""
    success: bool
    columns: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    rows_affected: Optional[int] = None
    error: Optional[str] = None


class TableInfo(BaseModel):
    """Model for table information"""
    TABLE_SCHEMA: str
    TABLE_NAME: str
    TABLE_TYPE: str


class ColumnInfo(BaseModel):
    """Model for column information"""
    COLUMN_NAME: str
    DATA_TYPE: str
    CHARACTER_MAXIMUM_LENGTH: Optional[int] = None
    NUMERIC_PRECISION: Optional[int] = None
    NUMERIC_SCALE: Optional[int] = None
    IS_NULLABLE: str
    COLUMN_DEFAULT: Optional[str] = None


class IndexInfo(BaseModel):
    """Model for index information"""
    table_name: str
    index_name: str
    index_type: str
    is_unique: bool
    is_primary_key: bool


class SchemaInfo(BaseModel):
    """Model for schema information"""
    schema: str
    table: str
    columns: List[Dict[str, Any]]


class VisualizationRequest(BaseModel):
    """Request model for visualization generation"""
    query: str = Field(..., description="SQL query to visualize")
    viz_type: str = Field(default="auto", description="Type of visualization")
    title: Optional[str] = Field(None, description="Chart title")


class VisualizationResponse(BaseModel):
    """Response model for visualization"""
    success: bool
    message: Optional[str] = None
    chart_data: Optional[Dict[str, Any]] = None
    visualization_type: Optional[str] = None
    error: Optional[str] = None


class NotebookRequest(BaseModel):
    """Request model for notebook generation"""
    query: str = Field(..., description="SQL query for analysis")
    output_file: Optional[str] = Field(None, description="Output filename")


class NotebookResponse(BaseModel):
    """Response model for notebook generation"""
    success: bool
    message: Optional[str] = None
    notebook_file: Optional[str] = None
    error: Optional[str] = None


class ServiceStatus(BaseModel):
    """Model for service status"""
    connected: bool
    database: Optional[str] = None
    server: Optional[str] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Response model for status endpoint"""
    status: str
    timestamp: datetime
    services: Dict[str, ServiceStatus]
    connectedServices: int
    totalServices: int
    version: str


class ToolInfo(BaseModel):
    """Model for tool information"""
    name: str
    description: str
    available: bool


class ToolsListResponse(BaseModel):
    """Response model for tools list"""
    tools: List[ToolInfo]
    count: int
    timestamp: str


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: str
    error: Optional[str] = None