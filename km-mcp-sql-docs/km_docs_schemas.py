from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentCreate(BaseModel):
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
    title: Optional[str] = None
    content: Optional[str] = None
    classification: Optional[str] = None
    entities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    classification: Optional[str] = None
    entities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SearchRequest(BaseModel):
    query: Optional[str] = None
    classification: Optional[str] = None
    limit: int = 10
    offset: int = 0

class SearchResponse(BaseModel):
    documents: List[Dict[str, Any]]
    total: int
    success: bool = True

class StatsResponse(BaseModel):
    statistics: Dict[str, Any]
    classification_breakdown: List[Dict[str, Any]] = []
    success: bool = True
