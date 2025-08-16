"""
Pydantic schemas for KM Orchestrator API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

class AnalysisType(str, Enum):
    """Types of document analysis available"""
    SUMMARY = "summary"
    INSIGHTS = "insights"
    ENTITIES = "entities"
    SENTIMENT = "sentiment"
    CLASSIFICATION = "classification"
    FULL = "full"

class SearchType(str, Enum):
    """Types of search available"""
    TEXT = "text"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    GRAPH = "graph"

class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Request Schemas
class UploadRequest(BaseModel):
    """Request schema for document upload"""
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    file_name: Optional[str] = Field(None, description="Original file name")
    file_type: Optional[str] = Field(None, description="File MIME type")
    category_id: Optional[int] = Field(None, description="Document category ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    source_url: Optional[str] = Field(None, description="Source URL if applicable")
    auto_process: bool = Field(True, description="Automatically trigger processing pipeline")

class SearchRequest(BaseModel):
    """Request schema for intelligent search"""
    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(SearchType.HYBRID, description="Type of search to perform")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Search filters")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    include_content: bool = Field(True, description="Include document content in results")
    include_metadata: bool = Field(True, description="Include document metadata")

class AnalyzeRequest(BaseModel):
    """Request schema for AI analysis"""
    document_id: Optional[int] = Field(None, description="Document ID to analyze")
    content: Optional[str] = Field(None, description="Direct content to analyze")
    analysis_type: AnalysisType = Field(AnalysisType.FULL, description="Type of analysis to perform")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Analysis options")

class InsightsRequest(BaseModel):
    """Request schema for combined insights"""
    timeframe: Optional[str] = Field("7d", description="Timeframe for metrics (e.g., '7d', '30d', 'all')")
    include_trends: bool = Field(True, description="Include trend analysis")
    include_recommendations: bool = Field(True, description="Include system recommendations")

class ChatRequest(BaseModel):
    """Request schema for interactive chat"""
    message: str = Field(..., description="User message/question")
    context: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Previous conversation context")
    document_context: Optional[List[int]] = Field(default_factory=list, description="Relevant document IDs for context")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Chat options")

class WorkflowRequest(BaseModel):
    """Request schema for workflow execution"""
    workflow_name: str = Field(..., description="Name of workflow to execute")
    parameters: Dict[str, Any] = Field(..., description="Workflow parameters")
    priority: int = Field(5, ge=1, le=10, description="Execution priority (1=highest, 10=lowest)")

# Response Schemas
class ServiceHealth(BaseModel):
    """Service health status"""
    name: str
    status: str  # healthy, unhealthy, unknown
    response_time: int  # milliseconds
    last_checked: datetime
    error_message: Optional[str] = None

class HealthResponse(BaseModel):
    """Overall system health response"""
    status: str
    timestamp: datetime
    services_total: int
    services_healthy: int
    services: List[ServiceHealth]
    avg_response_time: int
    total_requests: Optional[int] = 0

class SearchResult(BaseModel):
    """Individual search result"""
    document_id: int
    title: str
    content: Optional[str] = None
    score: float
    source: str  # Which service provided this result
    metadata: Optional[Dict[str, Any]] = None
    highlights: Optional[List[str]] = None

class SearchResponse(BaseModel):
    """Search results response"""
    status: str
    query: str
    search_type: SearchType
    results: List[SearchResult]
    total_results: int
    sources: List[str]
    execution_time: float

class AnalysisResult(BaseModel):
    """AI analysis result"""
    analysis_type: AnalysisType
    document_id: Optional[int] = None
    summary: Optional[str] = None
    insights: Optional[List[str]] = None
    entities: Optional[List[Dict[str, Any]]] = None
    sentiment: Optional[Dict[str, Any]] = None
    classification: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None

class AnalysisResponse(BaseModel):
    """Analysis results response"""
    status: str
    document_id: Optional[int] = None
    analysis_type: AnalysisType
    results: AnalysisResult
    services_used: List[str]
    execution_time: float

class InsightData(BaseModel):
    """Individual insight data point"""
    metric: str
    value: Union[int, float, str]
    trend: Optional[str] = None  # up, down, stable
    description: str

class InsightsResponse(BaseModel):
    """Combined insights response"""
    status: str
    timestamp: datetime
    timeframe: str
    insights: Dict[str, List[InsightData]]
    recommendations: Optional[List[str]] = None

class ChatMessage(BaseModel):
    """Chat message"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    """Chat interaction response"""
    status: str
    message: ChatMessage
    context_used: List[str]  # Which services/documents were consulted
    confidence: Optional[float] = None
    suggestions: Optional[List[str]] = None

class WorkflowStep(BaseModel):
    """Individual workflow step result"""
    step_name: str
    service: str
    status: WorkflowStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class WorkflowResponse(BaseModel):
    """Workflow execution response"""
    workflow_name: str
    status: WorkflowStatus
    steps: List[WorkflowStep]
    total_execution_time: float
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class ServiceCapability(BaseModel):
    """Service capability description"""
    name: str
    description: str
    endpoints: List[str]
    capabilities: List[str]
    status: str

class ServiceStatusResponse(BaseModel):
    """Detailed service status response"""
    timestamp: datetime
    services: List[ServiceCapability]
    total_capabilities: int
    available_capabilities: int

class MetricData(BaseModel):
    """Performance metric data"""
    metric_name: str
    value: Union[int, float]
    unit: str
    timestamp: datetime
    tags: Optional[Dict[str, str]] = None

class MetricsResponse(BaseModel):
    """Orchestrator metrics response"""
    timestamp: datetime
    uptime_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    service_metrics: List[MetricData]
    error_rates: Dict[str, float]

# Error Response Schema
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: str
    timestamp: datetime
    request_id: Optional[str] = None