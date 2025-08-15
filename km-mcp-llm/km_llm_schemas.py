from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalyzeDocumentRequest(BaseModel):
    document_id: int = Field(..., description="ID of document to analyze")
    analysis_type: str = Field(default="general", description="Type of analysis")

class AnswerQuestionRequest(BaseModel):
    question: str = Field(..., description="Question to answer")
    search_query: Optional[str] = Field(default=None, description="Search query")
    max_documents: int = Field(default=5, description="Max documents to use")

class SummarizeContentRequest(BaseModel):
    document_id: Optional[int] = Field(default=None, description="Document to summarize")
    content: Optional[str] = Field(default=None, description="Direct content")
    summary_type: str = Field(default="concise", description="Summary type")

class ExtractInsightsRequest(BaseModel):
    search_query: Optional[str] = Field(default=None, description="Search query")
    insight_types: List[str] = Field(default=["themes", "entities"], description="Insight types")

class AnalysisResult(BaseModel):
    document_id: int
    document_title: str
    analysis_type: str
    results: Dict[str, Any]
    processing_time: float

class AnswerResponse(BaseModel):
    question: str
    answer: str
    confidence_score: float
    sources: List[Dict[str, Any]]
    processing_time: float

class SummaryResponse(BaseModel):
    original_length: int
    summary: str
    summary_type: str
    key_points: List[str]
    processing_time: float

class InsightsResponse(BaseModel):
    insights: Dict[str, Any]
    document_count: int
    insight_types: List[str]
    processing_time: float

class ServiceHealth(BaseModel):
    status: str
    service: str
    version: str
    model_loaded: bool
    docs_service_connected: bool
    timestamp: datetime

class ToolResponse(BaseModel):
    success: bool = True
    result: Any
    error: Optional[str] = None
    processing_time: Optional[float] = None

