"""
Core operations for KM Orchestrator - handles service routing, health checks, and workflows
"""
import httpx
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from km_orchestrator_config import settings, HEALTH_ENDPOINTS, SERVICE_CAPABILITIES, WORKFLOW_DEFINITIONS, ROUTING_RULES
from km_orchestrator_schemas import *

logger = logging.getLogger(__name__)

class OrchestratorOperations:
    """Core operations for the orchestrator"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.service_timeout)
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.service_stats = defaultdict(lambda: {"requests": 0, "errors": 0, "total_time": 0})
    
    async def route_to_service(self, service_name: str, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Route a request to a specific MCP service"""
        if service_name not in settings.mcp_services:
            raise ValueError(f"Unknown service: {service_name}")
        
        base_url = settings.mcp_services[service_name]
        url = f"{base_url}{endpoint}"
        
        self.request_count += 1
        self.service_stats[service_name]["requests"] += 1
        start_time = time.time()
        
        try:
            logger.info(f"Routing {method} request to {service_name}: {endpoint}")
            
            if method.upper() == "GET":
                response = await self.client.get(url)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            execution_time = time.time() - start_time
            self.service_stats[service_name]["total_time"] += execution_time
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {service_name}: {e.response.status_code} - {e.response.text}")
            self.error_count += 1
            self.service_stats[service_name]["errors"] += 1
            raise
        except Exception as e:
            logger.error(f"Request failed for {service_name}: {str(e)}")
            self.error_count += 1
            self.service_stats[service_name]["errors"] += 1
            raise
    
    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """Check health of a single service"""
        if service_name not in HEALTH_ENDPOINTS:
            return ServiceHealth(
                name=service_name,
                status="unknown",
                response_time=0,
                last_checked=datetime.utcnow(),
                error_message="Service not configured"
            )
        
        start_time = time.time()
        try:
            response = await self.client.get(
                HEALTH_ENDPOINTS[service_name], 
                timeout=settings.health_check_timeout
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                return ServiceHealth(
                    name=service_name,
                    status="healthy",
                    response_time=response_time,
                    last_checked=datetime.utcnow()
                )
            else:
                return ServiceHealth(
                    name=service_name,
                    status="unhealthy",
                    response_time=response_time,
                    last_checked=datetime.utcnow(),
                    error_message=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            return ServiceHealth(
                name=service_name,
                status="unhealthy",
                response_time=response_time,
                last_checked=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def check_all_services_health(self) -> HealthResponse:
        """Check health of all MCP services"""
        tasks = [
            self.check_service_health(service_name)
            for service_name in settings.mcp_services.keys()
        ]
        
        service_healths = await asyncio.gather(*tasks)
        
        healthy_count = sum(1 for sh in service_healths if sh.status == "healthy")
        total_count = len(service_healths)
        
        avg_response_time = int(sum(sh.response_time for sh in service_healths) / len(service_healths)) if service_healths else 0
        
        overall_status = "healthy" if healthy_count == total_count else "degraded" if healthy_count > 0 else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            services_total=total_count,
            services_healthy=healthy_count,
            services=service_healths,
            avg_response_time=avg_response_time,
            total_requests=self.request_count
        )
    
    async def combine_search_results(self, results: List[Any], query: str) -> List[Dict[str, Any]]:
        """Combine and rank search results from multiple services"""
        combined = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Search service {i} failed: {result}")
                continue
            
            if isinstance(result, dict) and "results" in result:
                for item in result["results"]:
                    combined.append({
                        **item,
                        "source": f"service_{i}",
                        "relevance_score": self._calculate_relevance(item, query)
                    })
        
        # Sort by relevance score
        combined.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return combined
    
    def _calculate_relevance(self, item: Dict, query: str) -> float:
        """Calculate relevance score for search results"""
        # Simple relevance scoring - can be enhanced with ML
        score = 0.0
        query_lower = query.lower()
        
        title = item.get("title", "").lower()
        content = item.get("content", "").lower()
        
        # Title matches are more important
        if query_lower in title:
            score += 2.0
        
        # Content matches
        if query_lower in content:
            score += 1.0
        
        # Word-level matching
        query_words = query_lower.split()
        for word in query_words:
            if word in title:
                score += 0.5
            if word in content:
                score += 0.2
        
        return score
    
    async def get_available_analysis_services(self) -> List[str]:
        """Get list of services available for analysis"""
        health_response = await self.check_all_services_health()
        return [
            service.name for service in health_response.services 
            if service.status == "healthy" and service.name in ["km-mcp-llm", "km-mcp-graphrag"]
        ]
    
    async def get_available_chat_capabilities(self) -> List[str]:
        """Get available chat capabilities"""
        capabilities = []
        health_response = await self.check_all_services_health()
        
        for service in health_response.services:
            if service.status == "healthy":
                if service.name == "km-mcp-llm":
                    capabilities.extend(["ai_reasoning", "question_answering", "document_analysis"])
                elif service.name == "km-mcp-sql-docs":
                    capabilities.extend(["document_search", "content_retrieval"])
                elif service.name == "km-mcp-graphrag":
                    capabilities.extend(["entity_extraction", "knowledge_graph"])
        
        return capabilities
    
    async def determine_chat_routing(self, message: str) -> Dict[str, Any]:
        """Determine which services to route chat message to"""
        message_lower = message.lower()
        routing = {
            "primary_service": None,
            "supporting_services": [],
            "reasoning": ""
        }
        
        # Simple keyword-based routing - can be enhanced with NLP
        if any(word in message_lower for word in ["search", "find", "document", "content"]):
            routing["primary_service"] = "km-mcp-sql-docs"
            routing["supporting_services"] = ["km-mcp-search"]
            routing["reasoning"] = "Document search query detected"
        elif any(word in message_lower for word in ["analyze", "insight", "summary", "explain"]):
            routing["primary_service"] = "km-mcp-llm"
            routing["supporting_services"] = ["km-mcp-sql-docs"]
            routing["reasoning"] = "Analysis request detected"
        elif any(word in message_lower for word in ["entity", "relationship", "graph", "connection"]):
            routing["primary_service"] = "km-mcp-graphrag"
            routing["supporting_services"] = ["km-mcp-sql-docs"]
            routing["reasoning"] = "Graph/entity query detected"
        else:
            routing["primary_service"] = "km-mcp-llm"
            routing["supporting_services"] = ["km-mcp-sql-docs"]
            routing["reasoning"] = "General AI assistance"
        
        return routing
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get document statistics from sql-docs service"""
        try:
            result = await self.route_to_service("km-mcp-sql-docs", "GET", "/tools/database-stats")
            return result
        except Exception as e:
            logger.error(f"Failed to get document statistics: {e}")
            return {"error": "Unable to retrieve document statistics"}
    
    async def get_usage_metrics(self) -> Dict[str, Any]:
        """Get orchestrator usage metrics"""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "error_rate": (self.error_count / max(self.request_count, 1)) * 100,
            "requests_per_minute": (self.request_count / max(uptime / 60, 1)),
            "service_stats": dict(self.service_stats)
        }
    
    async def get_system_recommendations(self) -> List[str]:
        """Generate system recommendations based on current state"""
        recommendations = []
        health_response = await self.check_all_services_health()
        
        unhealthy_services = [s for s in health_response.services if s.status != "healthy"]
        if unhealthy_services:
            recommendations.append(f"Address {len(unhealthy_services)} unhealthy services: {', '.join(s.name for s in unhealthy_services)}")
        
        if health_response.avg_response_time > 1000:
            recommendations.append("Consider optimizing service response times (current average > 1s)")
        
        if self.error_count / max(self.request_count, 1) > 0.05:
            recommendations.append("High error rate detected - investigate service reliability")
        
        if not recommendations:
            recommendations.append("System operating optimally - all services healthy")
        
        return recommendations
    
    async def get_detailed_service_status(self) -> ServiceStatusResponse:
        """Get detailed status of all services with capabilities"""
        health_response = await self.check_all_services_health()
        
        service_capabilities = []
        for service_health in health_response.services:
            if service_health.name in SERVICE_CAPABILITIES:
                capability_info = SERVICE_CAPABILITIES[service_health.name]
                service_capabilities.append(ServiceCapability(
                    name=service_health.name,
                    description=capability_info["description"],
                    endpoints=capability_info["endpoints"],
                    capabilities=capability_info["capabilities"],
                    status=service_health.status
                ))
        
        total_capabilities = sum(len(sc.capabilities) for sc in service_capabilities)
        available_capabilities = sum(len(sc.capabilities) for sc in service_capabilities if sc.status == "healthy")
        
        return ServiceStatusResponse(
            timestamp=datetime.utcnow(),
            services=service_capabilities,
            total_capabilities=total_capabilities,
            available_capabilities=available_capabilities
        )
    
    async def get_orchestrator_metrics(self) -> MetricsResponse:
        """Get comprehensive orchestrator metrics"""
        uptime = time.time() - self.start_time
        
        service_metrics = []
        for service_name, stats in self.service_stats.items():
            if stats["requests"] > 0:
                avg_time = stats["total_time"] / stats["requests"]
                error_rate = stats["errors"] / stats["requests"]
                
                service_metrics.extend([
                    MetricData(
                        metric_name="avg_response_time",
                        value=avg_time * 1000,  # Convert to ms
                        unit="milliseconds",
                        timestamp=datetime.utcnow(),
                        tags={"service": service_name}
                    ),
                    MetricData(
                        metric_name="request_count",
                        value=stats["requests"],
                        unit="count",
                        timestamp=datetime.utcnow(),
                        tags={"service": service_name}
                    )
                ])
        
        error_rates = {
            service_name: (stats["errors"] / max(stats["requests"], 1)) * 100
            for service_name, stats in self.service_stats.items()
        }
        
        return MetricsResponse(
            timestamp=datetime.utcnow(),
            uptime_seconds=uptime,
            total_requests=self.request_count,
            successful_requests=self.request_count - self.error_count,
            failed_requests=self.error_count,
            avg_response_time=sum(stats["total_time"] for stats in self.service_stats.values()) / max(self.request_count, 1),
            service_metrics=service_metrics,
            error_rates=error_rates
        )
    
    async def execute_workflow(self, workflow_name: str, parameters: Dict[str, Any]) -> WorkflowResponse:
        """Execute a predefined workflow"""
        if workflow_name not in WORKFLOW_DEFINITIONS:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        workflow_def = WORKFLOW_DEFINITIONS[workflow_name]
        workflow_start_time = time.time()
        
        workflow_response = WorkflowResponse(
            workflow_name=workflow_name,
            status=WorkflowStatus.RUNNING,
            steps=[],
            total_execution_time=0
        )
        
        try:
            for step_def in workflow_def["steps"]:
                step_start_time = time.time()
                step_name = f"{step_def['service']}.{step_def['action']}"
                
                step_result = WorkflowStep(
                    step_name=step_name,
                    service=step_def["service"],
                    status=WorkflowStatus.RUNNING
                )
                
                try:
                    # Execute the step (simplified implementation)
                    result = await self.route_to_service(
                        step_def["service"],
                        "POST", 
                        f"/tools/{step_def['action']}", 
                        parameters
                    )
                    
                    step_result.status = WorkflowStatus.COMPLETED
                    step_result.result = result
                    step_result.execution_time = time.time() - step_start_time
                    
                except Exception as e:
                    step_result.status = WorkflowStatus.FAILED
                    step_result.error = str(e)
                    step_result.execution_time = time.time() - step_start_time
                    
                    workflow_response.status = WorkflowStatus.FAILED
                    workflow_response.error_message = f"Step {step_name} failed: {str(e)}"
                
                workflow_response.steps.append(step_result)
                
                # Break on failure unless specified otherwise
                if step_result.status == WorkflowStatus.FAILED:
                    break
            
            if workflow_response.status != WorkflowStatus.FAILED:
                workflow_response.status = WorkflowStatus.COMPLETED
            
        except Exception as e:
            workflow_response.status = WorkflowStatus.FAILED
            workflow_response.error_message = f"Workflow execution failed: {str(e)}"
        
        workflow_response.total_execution_time = time.time() - workflow_start_time
        return workflow_response
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose()