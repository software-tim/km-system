"""
km-mcp-llm: External AI Integration Service
Uses Azure OpenAI, OpenAI API, and other cloud AI services
Better performance than local models without hardware requirements
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import aiohttp

# Initialize FastAPI app
app = FastAPI(
    title="KM MCP LLM Service",
    description="External AI Integration Service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Configuration
class AIConfig:
    def __init__(self):
        # Azure OpenAI (preferred)
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_key = os.getenv("AZURE_OPENAI_KEY") 
        self.azure_deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4")
        
        # OpenAI API (fallback)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Document service integration
        self.km_docs_url = "https://km-mcp-sql-docs.azurewebsites.net"

ai_config = AIConfig()

class ExternalAIService:
    """Handles external AI API calls with fallback options"""
    
    def __init__(self):
        self.azure_available = bool(ai_config.azure_openai_key and ai_config.azure_openai_endpoint)
        self.openai_available = bool(ai_config.openai_api_key)
    
    async def analyze_text(self, text: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze text using external AI"""
        
        prompts = {
            "comprehensive": f"Analyze this document comprehensively. Extract key themes, main points, entities, and provide insights:\n\n{text}",
            "themes": f"Extract the main themes and topics from this document:\n\n{text}",
            "entities": f"Identify and extract all named entities (people, organizations, locations, dates) from this text:\n\n{text}",
            "sentiment": f"Analyze the sentiment and emotional tone of this document:\n\n{text}"
        }
        
        prompt = prompts.get(analysis_type, prompts["comprehensive"])
        
        try:
            # Try Azure OpenAI first
            if self.azure_available:
                headers = {
                    "Content-Type": "application/json",
                    "api-key": ai_config.azure_openai_key
                }
                
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.3
                }
                
                async with aiohttp.ClientSession() as session:
                    url = f"{ai_config.azure_openai_endpoint}/openai/deployments/{ai_config.azure_deployment_name}/chat/completions?api-version=2024-02-15-preview"
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "analysis": result["choices"][0]["message"]["content"],
                                "provider": "Azure OpenAI",
                                "model": ai_config.azure_deployment_name,
                                "success": True
                            }
            
            # Fallback to OpenAI
            elif self.openai_available:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ai_config.openai_api_key}"
                }
                
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.3
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "analysis": result["choices"][0]["message"]["content"],
                                "provider": "OpenAI",
                                "model": "gpt-3.5-turbo",
                                "success": True
                            }
            
            else:
                return {
                    "error": "No AI service configured. Please set up Azure OpenAI or OpenAI API keys.",
                    "setup_instructions": {
                        "azure_openai": "Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, and AZURE_DEPLOYMENT_NAME environment variables",
                        "openai": "Set OPENAI_API_KEY environment variable"
                    },
                    "success": False
                }
                
        except Exception as e:
            return {
                "error": f"AI analysis failed: {str(e)}",
                "success": False
            }
    
    async def answer_question(self, question: str, context: str = "") -> Dict[str, Any]:
        """Answer questions using external AI"""
        
        prompt = f"""Answer this question based on the provided context. If the context doesn't contain enough information, say so clearly.

Question: {question}

Context: {context}

Answer:"""
        
        try:
            if self.azure_available:
                headers = {
                    "Content-Type": "application/json",
                    "api-key": ai_config.azure_openai_key
                }
                
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.2
                }
                
                async with aiohttp.ClientSession() as session:
                    url = f"{ai_config.azure_openai_endpoint}/openai/deployments/{ai_config.azure_deployment_name}/chat/completions?api-version=2024-02-15-preview"
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "answer": result["choices"][0]["message"]["content"],
                                "provider": "Azure OpenAI",
                                "success": True
                            }
            
            elif self.openai_available:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ai_config.openai_api_key}"
                }
                
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.2
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "answer": result["choices"][0]["message"]["content"],
                                "provider": "OpenAI",
                                "success": True
                            }
            
            else:
                return {
                    "error": "No AI service configured",
                    "success": False
                }
                
        except Exception as e:
            return {
                "error": f"Q&A failed: {str(e)}",
                "success": False
            }
    
    async def summarize_text(self, text: str, style: str = "concise") -> Dict[str, Any]:
        """Summarize text using external AI"""
        
        style_prompts = {
            "concise": "Provide a concise 2-3 sentence summary of this document:",
            "detailed": "Provide a detailed paragraph summary of this document:",
            "bullets": "Summarize this document as a bulleted list of key points:",
            "executive": "Provide an executive summary suitable for senior management:"
        }
        
        prompt = f"{style_prompts.get(style, style_prompts['concise'])}\n\n{text}"
        
        try:
            if self.azure_available:
                headers = {
                    "Content-Type": "application/json",
                    "api-key": ai_config.azure_openai_key
                }
                
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.3
                }
                
                async with aiohttp.ClientSession() as session:
                    url = f"{ai_config.azure_openai_endpoint}/openai/deployments/{ai_config.azure_deployment_name}/chat/completions?api-version=2024-02-15-preview"
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "summary": result["choices"][0]["message"]["content"],
                                "provider": "Azure OpenAI",
                                "style": style,
                                "success": True
                            }
            
            elif self.openai_available:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ai_config.openai_api_key}"
                }
                
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.3
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "summary": result["choices"][0]["message"]["content"],
                                "provider": "OpenAI",
                                "style": style,
                                "success": True
                            }
            
            else:
                return {
                    "error": "No AI service configured",
                    "success": False
                }
                
        except Exception as e:
            return {
                "error": f"Summarization failed: {str(e)}",
                "success": False
            }

# Initialize AI service
ai_service = ExternalAIService()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Beautiful HTML interface for the external AI service"""
    
    # Check AI service status
    if ai_service.azure_available:
        ai_status = "🟢 Azure OpenAI"
    elif ai_service.openai_available:
        ai_status = "🟡 OpenAI API"
    else:
        ai_status = "🔴 Not Configured"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 KM LLM Service</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
                padding: 20px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .header h1 {{ font-size: 3.5rem; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
            .status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .status-card {{ 
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 25px;
                border: 1px solid rgba(255,255,255,0.2);
                transition: transform 0.3s ease;
            }}
            .status-card:hover {{ transform: translateY(-5px); }}
            .status-card h3 {{ color: #ffeb3b; margin-bottom: 15px; font-size: 1.3rem; }}
            .status-value {{ font-size: 2rem; font-weight: bold; margin: 10px 0; }}
            .endpoints-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }}
            .endpoint-card {{ 
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 25px;
                border: 1px solid rgba(255,255,255,0.2);
                transition: all 0.3s ease;
                cursor: pointer;
            }}
            .endpoint-card:hover {{ 
                transform: translateY(-5px);
                background: rgba(255,255,255,0.2);
            }}
            .endpoint-card h4 {{ color: #4caf50; margin-bottom: 10px; font-size: 1.2rem; }}
            .method {{ 
                background: #2196f3;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                margin-bottom: 10px;
                display: inline-block;
            }}
            .description {{ color: #e0e0e0; line-height: 1.5; }}
            .form-container {{ 
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 25px;
                margin-top: 20px;
                display: none;
            }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 5px; color: #ffeb3b; }}
            .form-group input, .form-group textarea, .form-group select {{ 
                width: 100%;
                padding: 12px;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 8px;
                background: rgba(255,255,255,0.1);
                color: white;
                font-size: 16px;
            }}
            .form-group input::placeholder, .form-group textarea::placeholder {{ color: #ccc; }}
            .btn {{ 
                background: linear-gradient(45deg, #4caf50, #45a049);
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                transition: all 0.3s ease;
            }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }}
            .result {{ 
                background: rgba(0,0,0,0.3);
                border-radius: 10px;
                padding: 20px;
                margin-top: 20px;
                font-family: 'Courier New', monospace;
                white-space: pre-wrap;
                display: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 KM LLM Service</h1>
                <p>External AI Integration • Powered by Cloud AI</p>
            </div>

            <div class="status-grid">
                <div class="status-card">
                    <h3>🚀 AI Status</h3>
                    <div class="status-value">{ai_status}</div>
                    <p>Cloud AI Integration</p>
                </div>
                <div class="status-card">
                    <h3>📊 Document Database</h3>
                    <div class="status-value" id="doc-count">17+</div>
                    <p>Documents Available</p>
                </div>
                <div class="status-card">
                    <h3>⚡ Performance</h3>
                    <div class="status-value">🚀 Fast</div>
                    <p>Cloud-powered responses</p>
                </div>
            </div>

            <div class="endpoints-grid">
                <div class="endpoint-card" onclick="showForm('analyze')">
                    <h4>🔍 Document Analysis</h4>
                    <span class="method">POST</span>
                    <p class="description">Analyze documents with cloud AI - faster and more accurate than local models.</p>
                </div>

                <div class="endpoint-card" onclick="showForm('qa')">
                    <h4>❓ Q&A System</h4>
                    <span class="method">POST</span>
                    <p class="description">Ask questions about your documents using advanced cloud AI models.</p>
                </div>

                <div class="endpoint-card" onclick="showForm('summarize')">
                    <h4>📝 Smart Summarization</h4>
                    <span class="method">POST</span>
                    <p class="description">Generate intelligent summaries using GPT-4 or GPT-3.5 models.</p>
                </div>

                <div class="endpoint-card" onclick="window.open('/health', '_blank')">
                    <h4>❤️ Health Check</h4>
                    <span class="method">GET</span>
                    <p class="description">Check service health and AI provider status.</p>
                </div>

                <div class="endpoint-card" onclick="window.open('/docs', '_blank')">
                    <h4>📚 API Documentation</h4>
                    <span class="method">GET</span>
                    <p class="description">Interactive Swagger documentation for all AI endpoints.</p>
                </div>

                <div class="endpoint-card" onclick="window.open('https://km-mcp-sql-docs.azurewebsites.net', '_blank')">
                    <h4>📄 Document Service</h4>
                    <span class="method">External</span>
                    <p class="description">Access your document collection and search capabilities.</p>
                </div>
            </div>

            <!-- Analysis Form -->
            <div class="form-container" id="analyze-form">
                <h3>🔍 Document Analysis</h3>
                <form onsubmit="submitAnalysis(event)">
                    <div class="form-group">
                        <label>Document Text</label>
                        <textarea name="content" rows="6" placeholder="Paste document text here for AI analysis..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Analysis Type</label>
                        <select name="analysis_type">
                            <option value="comprehensive">Comprehensive Analysis</option>
                            <option value="themes">Theme Extraction</option>
                            <option value="entities">Entity Recognition</option>
                            <option value="sentiment">Sentiment Analysis</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">Analyze with AI</button>
                </form>
                <div class="result" id="analyze-result"></div>
            </div>

            <!-- Q&A Form -->
            <div class="form-container" id="qa-form">
                <h3>❓ Q&A System</h3>
                <form onsubmit="submitQA(event)">
                    <div class="form-group">
                        <label>Your Question</label>
                        <textarea name="question" rows="3" placeholder="Ask anything about your documents..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Context (Optional)</label>
                        <textarea name="context" rows="4" placeholder="Provide context or paste relevant document text..."></textarea>
                    </div>
                    <button type="submit" class="btn">Get AI Answer</button>
                </form>
                <div class="result" id="qa-result"></div>
            </div>

            <!-- Summarization Form -->
            <div class="form-container" id="summarize-form">
                <h3>📝 Smart Summarization</h3>
                <form onsubmit="submitSummarization(event)">
                    <div class="form-group">
                        <label>Text to Summarize</label>
                        <textarea name="content" rows="6" placeholder="Paste text or document content here..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Summary Style</label>
                        <select name="style">
                            <option value="concise">Concise (2-3 sentences)</option>
                            <option value="detailed">Detailed (paragraph)</option>
                            <option value="bullets">Bullet Points</option>
                            <option value="executive">Executive Summary</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">Generate Summary</button>
                </form>
                <div class="result" id="summarize-result"></div>
            </div>

            <div style="text-align: center; margin-top: 40px; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 15px;">
                <h3>🎯 AI Configuration</h3>
                <p>To enable AI features, configure environment variables:</p>
                <ul style="text-align: left; margin: 20px 0; list-style-position: inside;">
                    <li>• <strong>Azure OpenAI:</strong> AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_DEPLOYMENT_NAME</li>
                    <li>• <strong>OpenAI API:</strong> OPENAI_API_KEY</li>
                </ul>
                <p>Current Status: <strong>{ai_status}</strong></p>
            </div>
        </div>

        <script>
            function showForm(formType) {{
                document.querySelectorAll('.form-container').forEach(form => {{
                    form.style.display = 'none';
                }});
                document.getElementById(formType + '-form').style.display = 'block';
                document.getElementById(formType + '-form').scrollIntoView({{ behavior: 'smooth' }});
            }}

            async function submitAnalysis(event) {{
                event.preventDefault();
                const formData = new FormData(event.target);
                const data = Object.fromEntries(formData);
                
                try {{
                    const response = await fetch('/analyze', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
                    const result = await response.json();
                    document.getElementById('analyze-result').textContent = JSON.stringify(result, null, 2);
                    document.getElementById('analyze-result').style.display = 'block';
                }} catch (e) {{
                    document.getElementById('analyze-result').textContent = 'Error: ' + e.message;
                    document.getElementById('analyze-result').style.display = 'block';
                }}
            }}

            async function submitQA(event) {{
                event.preventDefault();
                const formData = new FormData(event.target);
                const data = Object.fromEntries(formData);
                
                try {{
                    const response = await fetch('/qa', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
                    const result = await response.json();
                    document.getElementById('qa-result').textContent = JSON.stringify(result, null, 2);
                    document.getElementById('qa-result').style.display = 'block';
                }} catch (e) {{
                    document.getElementById('qa-result').textContent = 'Error: ' + e.message;
                    document.getElementById('qa-result').style.display = 'block';
                }}
            }}

            async function submitSummarization(event) {{
                event.preventDefault();
                const formData = new FormData(event.target);
                const data = Object.fromEntries(formData);
                
                try {{
                    const response = await fetch('/summarize', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
                    const result = await response.json();
                    document.getElementById('summarize-result').textContent = JSON.stringify(result, null, 2);
                    document.getElementById('summarize-result').style.display = 'block';
                }} catch (e) {{
                    document.getElementById('summarize-result').textContent = 'Error: ' + e.message;
                    document.getElementById('summarize-result').style.display = 'block';
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint with AI service status"""
    
    ai_providers = []
    if ai_service.azure_available:
        ai_providers.append("Azure OpenAI")
    if ai_service.openai_available:
        ai_providers.append("OpenAI")
    
    health_status = {
        "service": "km-mcp-llm",
        "status": "running",
        "version": "1.0.0-external-ai",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_providers": ai_providers,
        "ai_configured": len(ai_providers) > 0,
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze", 
            "qa": "/qa",
            "summarize": "/summarize",
            "docs": "/docs"
        },
        "integration": {
            "km_sql_docs": "https://km-mcp-sql-docs.azurewebsites.net"
        }
    }
    
    # Try to check if km-mcp-sql-docs is accessible
    try:
        response = requests.get("https://km-mcp-sql-docs.azurewebsites.net/health", timeout=5)
        if response.status_code == 200:
            health_status["integration"]["km_sql_docs_status"] = "connected"
        else:
            health_status["integration"]["km_sql_docs_status"] = "limited"
    except:
        health_status["integration"]["km_sql_docs_status"] = "checking"
    
    return JSONResponse(content=health_status)

@app.post("/analyze")
async def analyze_document(request: Request):
    """Analyze document content using external AI"""
    data = await request.json()
    content = data.get("content", "")
    analysis_type = data.get("analysis_type", "comprehensive")
    
    if not content:
        raise HTTPException(status_code=400, detail="No content provided")
    
    result = await ai_service.analyze_text(content, analysis_type)
    return JSONResponse(content=result)

@app.post("/qa")
async def question_answer(request: Request):
    """Answer questions using external AI"""
    data = await request.json()
    question = data.get("question", "")
    context = data.get("context", "")
    
    if not question:
        raise HTTPException(status_code=400, detail="No question provided")
    
    result = await ai_service.answer_question(question, context)
    return JSONResponse(content=result)

@app.post("/summarize")
async def summarize_content(request: Request):
    """Generate summaries using external AI"""
    data = await request.json()
    content = data.get("content", "")
    style = data.get("style", "concise")
    
    if not content:
        raise HTTPException(status_code=400, detail="No content provided")
    
    result = await ai_service.summarize_text(content, style)
    return JSONResponse(content=result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)