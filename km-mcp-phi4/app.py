#!/usr/bin/env python3
"""
FastAPI Client for MCP Phi-4 Server
This FastAPI app acts as a client to call the deployed MCP Phi-4 server endpoints
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import httpx
import asyncio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Phi-4 MCP Client",
    description="FastAPI client for interacting with MCP Phi-4 Server",
    version="1.0.0"
)

# Configuration
PHI4_BASE_URL = "https://mcp-phi4-a8gbframhdd5ebcw.eastus2-01.azurewebsites.net"
TIMEOUT = 30.0  # Timeout for API calls

# Global HTTP client
client = httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT))

# Pydantic models for request/response validation
class GenerateTextRequest(BaseModel):
    prompt: str = Field(..., description="The prompt for text generation")
    max_tokens: int = Field(200, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")
    system_prompt: Optional[str] = Field(None, description="System prompt to set context")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Top-p sampling parameter")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    max_tokens: int = Field(200, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Top-p sampling parameter")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Phi-4 MCP Client",
        "version": "1.0.0",
        "phi4_server": PHI4_BASE_URL,
        "endpoints": {
            "GET /": "This information",
            "GET /health": "Health check",
            "GET /phi4/status": "Check Phi-4 server status",
            "POST /phi4/connect": "Connect to Phi-4 service",
            "POST /phi4/disconnect": "Disconnect from Phi-4 service",
            "POST /generate": "Generate text using Phi-4",
            "POST /chat": "Chat completion using Phi-4",
            "GET /tools": "List available Phi-4 tools"
        }
    }

@app.get("/health")
async def health_check():
    """Check health of this service and Phi-4 server"""
    try:
        # Check Phi-4 server health
        response = await client.get(f"{PHI4_BASE_URL}/health")
        phi4_health = response.json() if response.status_code == 200 else {"status": "unhealthy"}
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "phi4_server": phi4_health
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

# Phi-4 server status
@app.get("/phi4/status")
async def get_phi4_status():
    """Get the status of the Phi-4 server"""
    try:
        response = await client.get(f"{PHI4_BASE_URL}/api/status")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Phi-4 server returned status {response.status_code}"
            )
    except httpx.RequestError as e:
        logger.error(f"Failed to check Phi-4 status: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to Phi-4 server: {str(e)}")

# Connect to Phi-4 service
@app.post("/phi4/connect")
async def connect_to_phi4():
    """Connect to the Phi-4 service"""
    try:
        response = await client.post(f"{PHI4_BASE_URL}/api/connect")
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.content else {"error": "Unknown error"}
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data
            )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Phi-4: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to Phi-4 server: {str(e)}")

# Disconnect from Phi-4 service
@app.post("/phi4/disconnect")
async def disconnect_from_phi4():
    """Disconnect from the Phi-4 service"""
    try:
        response = await client.post(f"{PHI4_BASE_URL}/api/disconnect")
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.content else {"error": "Unknown error"}
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data
            )
    except httpx.RequestError as e:
        logger.error(f"Failed to disconnect from Phi-4: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to disconnect from Phi-4 server: {str(e)}")

# Generate text endpoint
@app.post("/generate")
async def generate_text(request: GenerateTextRequest):
    """Generate text using Phi-4 model"""
    try:
        # Prepare the payload
        payload = {
            "arguments": {
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "presence_penalty": request.presence_penalty,
                "frequency_penalty": request.frequency_penalty
            }
        }
        
        if request.system_prompt:
            payload["arguments"]["system_prompt"] = request.system_prompt
        
        logger.info(f"Generating text with prompt length: {len(request.prompt)}")
        
        # Call Phi-4 server
        response = await client.post(
            f"{PHI4_BASE_URL}/api/tools/generate_with_phi4",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "generated_text": result.get("content", {}).get("content", ""),
                "usage": result.get("content", {}).get("usage"),
                "finish_reason": result.get("content", {}).get("finish_reason"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            error_data = response.json() if response.content else {"error": "Unknown error"}
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data
            )
            
    except httpx.RequestError as e:
        logger.error(f"Failed to generate text: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to call Phi-4 server: {str(e)}")

# Chat completion endpoint
@app.post("/chat")
async def chat_completion(request: ChatCompletionRequest):
    """Chat completion using Phi-4 model"""
    try:
        # Convert ChatMessage objects to dicts
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Prepare the payload
        payload = {
            "arguments": {
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "presence_penalty": request.presence_penalty,
                "frequency_penalty": request.frequency_penalty
            }
        }
        
        logger.info(f"Processing chat with {len(messages)} messages")
        
        # Call Phi-4 server
        response = await client.post(
            f"{PHI4_BASE_URL}/api/tools/chat_completion",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get("content", {}).get("content", ""),
                "usage": result.get("content", {}).get("usage"),
                "finish_reason": result.get("content", {}).get("finish_reason"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            error_data = response.json() if response.content else {"error": "Unknown error"}
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data
            )
            
    except httpx.RequestError as e:
        logger.error(f"Failed to complete chat: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to call Phi-4 server: {str(e)}")

# List available tools
@app.get("/tools")
async def list_tools():
    """List available Phi-4 tools"""
    try:
        response = await client.get(f"{PHI4_BASE_URL}/api/tools")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to retrieve tools list"
            )
    except httpx.RequestError as e:
        logger.error(f"Failed to list tools: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to call Phi-4 server: {str(e)}")

# Batch processing endpoint (bonus feature)
class BatchRequest(BaseModel):
    prompts: List[str] = Field(..., description="List of prompts to process")
    max_tokens: int = Field(200, description="Maximum tokens per generation")
    temperature: float = Field(0.7, description="Temperature for generation")

@app.post("/batch/generate")
async def batch_generate(request: BatchRequest, background_tasks: BackgroundTasks):
    """Process multiple prompts in batch"""
    results = []
    
    for prompt in request.prompts:
        try:
            payload = {
                "arguments": {
                    "prompt": prompt,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature
                }
            }
            
            response = await client.post(
                f"{PHI4_BASE_URL}/api/tools/generate_with_phi4",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                results.append({
                    "prompt": prompt,
                    "success": True,
                    "generated_text": result.get("content", {}).get("content", ""),
                    "usage": result.get("content", {}).get("usage")
                })
            else:
                results.append({
                    "prompt": prompt,
                    "success": False,
                    "error": f"Status code: {response.status_code}"
                })
                
        except Exception as e:
            results.append({
                "prompt": prompt,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total_prompts": len(request.prompts),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }

# Streaming endpoint (if needed)
from fastapi.responses import StreamingResponse
import json

@app.post("/generate/stream")
async def generate_text_stream(request: GenerateTextRequest):
    """Generate text with streaming response"""
    async def stream_generator():
        try:
            payload = {
                "arguments": {
                    "prompt": request.prompt,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature
                }
            }
            
            if request.system_prompt:
                payload["arguments"]["system_prompt"] = request.system_prompt
            
            # For streaming, you'd need to modify the Phi-4 server to support SSE
            # This is a simplified example
            response = await client.post(
                f"{PHI4_BASE_URL}/api/tools/generate_with_phi4",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", {}).get("content", "")
                
                # Simulate streaming by breaking content into chunks
                chunk_size = 10
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i+chunk_size]
                    yield json.dumps({"chunk": chunk}) + "\n"
                    await asyncio.sleep(0.1)  # Simulate delay
            else:
                yield json.dumps({"error": "Failed to generate text"}) + "\n"
                
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="application/x-ndjson"
    )

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await client.aclose()
    logger.info("Client connection closed")

if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )