#!/usr/bin/env python3
"""
Pydantic schemas for document operations
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime


class DocumentCreate(BaseModel):
    """Schema for creating a document"""
    title: str
    content: str
    classification: Optional[str] = None
    entities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    file_data: Optional[bytes] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    content: Optional[str] = None
    classification: Optional[str] = None
    entities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    title: str
    content: str
    classification: Optional[str] = None
    entities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    has_file: bool = False
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SearchRequest(BaseModel):
    """Schema for search request"""
    query: Optional[str] = None
    classification: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResponse(BaseModel):
    """Schema for search response"""
    success: bool
    documents: List[DocumentResponse]
    total: int
    query: str
    source: str


class DatabaseStats(BaseModel):
    """Schema for database statistics"""
    success: bool
    statistics: Dict[str, Any]
    classification_breakdown: List[Dict[str, Any]]
    source: str


class ToolInfo(BaseModel):
    """Schema for tool information"""
    name: str
    description: str
    endpoint: str
    method: str
    parameters: List[str]
