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
                    async with session.post(url, headers=headers, json=payload, timeout=30) as response:
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
                    async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30) as response:
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
                    async with session.post(url, headers=headers, json=payload, timeout=30) as response:
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
                    async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30) as response:
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
                    async with session.post(url, headers=headers, json=payload, timeout=30) as response:
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
                    async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30) as response:
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
    """Clean MCP server interface matching the standard format"""
    
    # Check AI service status
    if ai_service.azure_available:
        ai_status = "Connected"
        ai_provider = "Azure OpenAI"
    elif ai_service.openai_available:
        ai_status = "Connected"
        ai_provider = "OpenAI API"
    else:
        ai_status = "Not Configured"
        ai_provider = "None"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KM-MCP-LLM Server</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            .header {{
                background: white;
                padding: 30px 40px;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            .icon {{
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: white;
            }}
            .title {{
                font-size: 36px;
                font-weight: 600;
                color: #1f2937;
            }}
            .status-section {{
                padding: 30px 40px;
                background: #dcfce7;
                border-left: 4px solid #22c55e;
                margin: 0;
            }}
            .status-title {{
                font-size: 22px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 5px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .status-subtitle {{
                color: #6b7280;
                font-size: 16px;
            }}
            .stats-section {{
                padding: 30px 40px;
                background: #f9fafb;
            }}
            .stats-title {{
                font-size: 20px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .stat-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .stat-row:last-child {{ border-bottom: none; }}
            .stat-label {{ color: #1f2937; font-weight: 500; }}
            .stat-value {{ 
                color: #1f2937; 
                font-weight: 600; 
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .connected {{ color: #22c55e; }}
            .endpoints-section {{
                padding: 30px 40px;
            }}
            .endpoints-title {{
                font-size: 20px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .endpoint {{
                display: flex;
                align-items: flex-start;
                gap: 15px;
                padding: 15px 0;
                border-bottom: 1px solid #e5e7eb;
                border-left: 4px solid #e5e7eb;
                padding-left: 20px;
                margin-bottom: 10px;
            }}
            .endpoint:last-child {{ border-bottom: none; margin-bottom: 0; }}
            .method {{
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                min-width: 50px;
                text-align: center;
            }}
            .method.get {{ background: #dbeafe; color: #1d4ed8; }}
            .method.post {{ background: #dcfce7; color: #16a34a; }}
            .endpoint-content {{
                flex: 1;
            }}
            .endpoint-path {{
                font-family: 'Monaco', 'Consolas', monospace;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 5px;
            }}
            .endpoint-description {{
                color: #6b7280;
                font-size: 14px;
                line-height: 1.5;
            }}
            .footer {{
                padding: 20px 40px;
                background: #f9fafb;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
                border-top: 1px solid #e5e7eb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="icon">🤖</div>
                <div class="title">KM-MCP-LLM Server</div>
            </div>

            <div class="status-section">
                <div class="status-title">
                    ✅ Service is Running
                </div>
                <div class="status-subtitle">
                    External AI Integration Service
                </div>
            </div>

            <div class="stats-section">
                <div class="stats-title">
                    📊 System Statistics
                </div>
                <div class="stat-row">
                    <div class="stat-label">AI Provider:</div>
                    <div class="stat-value">{ai_provider}</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">AI Status:</div>
                    <div class="stat-value">
                        {"✅" if ai_status == "Connected" else "❌"} 
                        <span class="{'connected' if ai_status == 'Connected' else ''}">{ai_status}</span>
                    </div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Service Status:</div>
                    <div class="stat-value">✅ <span class="connected">Running</span></div>
                </div>
            </div>

            <div class="endpoints-section">
                <div class="endpoints-title">
                    🔗 Available API Endpoints:
                </div>
                
                <div class="endpoint">
                    <div class="method get">GET</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/health</div>
                        <div class="endpoint-description">Health check and AI provider status</div>
                    </div>
                </div>

                <div class="endpoint">
                    <div class="method post">POST</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/analyze</div>
                        <div class="endpoint-description">Analyze documents with cloud AI - comprehensive analysis, themes, entities, sentiment</div>
                    </div>
                </div>

                <div class="endpoint">
                    <div class="method post">POST</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/qa</div>
                        <div class="endpoint-description">Answer questions about documents using advanced AI models</div>
                    </div>
                </div>

                <div class="endpoint">
                    <div class="method post">POST</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/summarize</div>
                        <div class="endpoint-description">Generate intelligent summaries with multiple style options</div>
                    </div>
                </div>

                <div class="endpoint">
                    <div class="method get">GET</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/docs</div>
                        <div class="endpoint-description">Interactive API documentation (Swagger UI)</div>
                    </div>
                </div>
            </div>

            <div class="footer">
                Knowledge Management System v1.0 | Status: Production Ready
            </div>
        </div>

        <!-- Interactive Forms Section -->
        <div class="container" style="margin-top: 20px;">
            <div style="padding: 30px 40px; background: #f8fafc; border-bottom: 1px solid #e5e7eb;">
                <div style="font-size: 20px; font-weight: 600; color: #1f2937; display: flex; align-items: center; gap: 10px;">
                    🧪 Interactive Testing
                </div>
                <div style="color: #6b7280; font-size: 14px; margin-top: 5px;">
                    Test the AI endpoints directly from the browser
                </div>
            </div>

            <!-- Form Controls -->
            <div style="padding: 20px 40px; background: #f8fafc; border-bottom: 1px solid #e5e7eb;">
                <button onclick="showForm('analyze')" class="form-btn">📊 Document Analysis</button>
                <button onclick="showForm('qa')" class="form-btn">❓ Q&A System</button>
                <button onclick="showForm('summarize')" class="form-btn">📝 Summarization</button>
                <button onclick="hideAllForms()" class="form-btn secondary">✖️ Hide Forms</button>
            </div>

            <!-- Analysis Form -->
            <div class="form-container" id="analyze-form">
                <h3 style="color: #1f2937; margin-bottom: 20px;">📊 Document Analysis</h3>
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
                    <button type="submit" class="submit-btn">Analyze with AI</button>
                </form>
                <div class="result" id="analyze-result"></div>
            </div>

            <!-- Q&A Form -->
            <div class="form-container" id="qa-form">
                <h3 style="color: #1f2937; margin-bottom: 20px;">❓ Q&A System</h3>
                <form onsubmit="submitQA(event)">
                    <div class="form-group">
                        <label>Your Question</label>
                        <textarea name="question" rows="3" placeholder="Ask anything about your documents..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Context (Optional)</label>
                        <textarea name="context" rows="4" placeholder="Provide context or paste relevant document text..."></textarea>
                    </div>
                    <button type="submit" class="submit-btn">Get AI Answer</button>
                </form>
                <div class="result" id="qa-result"></div>
            </div>

            <!-- Summarization Form -->
            <div class="form-container" id="summarize-form">
                <h3 style="color: #1f2937; margin-bottom: 20px;">📝 Smart Summarization</h3>
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
                    <button type="submit" class="submit-btn">Generate Summary</button>
                </form>
                <div class="result" id="summarize-result"></div>
            </div>
        </div>

        <style>
            .form-btn {{
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                margin: 5px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s ease;
            }}
            .form-btn:hover {{ background: #5a6fd8; }}
            .form-btn.secondary {{ background: #6b7280; }}
            .form-btn.secondary:hover {{ background: #4b5563; }}
            
            .form-container {{
                display: none;
                padding: 30px 40px;
                background: white;
                border-top: 1px solid #e5e7eb;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 8px;
                color: #1f2937;
                font-weight: 500;
                font-size: 14px;
            }}
            .form-group input, .form-group textarea, .form-group select {{
                width: 100%;
                padding: 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background: white;
                color: #1f2937;
                font-size: 14px;
                font-family: inherit;
            }}
            .form-group input:focus, .form-group textarea:focus, .form-group select:focus {{
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}
            .form-group input::placeholder, .form-group textarea::placeholder {{
                color: #9ca3af;
            }}
            .submit-btn {{
                background: #22c55e;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.2s ease;
            }}
            .submit-btn:hover {{
                background: #16a34a;
                transform: translateY(-1px);
            }}
            .result {{
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 20px;
                margin-top: 20px;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 12px;
                white-space: pre-wrap;
                display: none;
                max-height: 400px;
                overflow-y: auto;
            }}
        </style>

        <script>
            function showForm(formType) {{
                document.querySelectorAll('.form-container').forEach(form => {{
                    form.style.display = 'none';
                }});
                document.getElementById(formType + '-form').style.display = 'block';
                document.getElementById(formType + '-form').scrollIntoView({{ behavior: 'smooth' }});
            }}

            function hideAllForms() {{
                document.querySelectorAll('.form-container').forEach(form => {{
                    form.style.display = 'none';
                }});
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
            "km_sql_docs": "https://km-mcp-sql-docs.azurewebsites.net",
            "km_sql_docs_status": "unchecked"
        }
    }
    
    # Try to check if km-mcp-sql-docs is accessible (async version)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://km-mcp-sql-docs.azurewebsites.net/health", timeout=5) as response:
                if response.status == 200:
                    health_status["integration"]["km_sql_docs_status"] = "connected"
                else:
                    health_status["integration"]["km_sql_docs_status"] = "limited"
    except Exception:
        health_status["integration"]["km_sql_docs_status"] = "unreachable"
    
    return JSONResponse(content=health_status)

@app.post("/analyze")
async def analyze_document(request: Request):
    """Analyze document content using external AI"""
    try:
        data = await request.json()
        content = data.get("content", "")
        analysis_type = data.get("analysis_type", "comprehensive")
        
        if not content:
            raise HTTPException(status_code=400, detail="No content provided")
        
        result = await ai_service.analyze_text(content, analysis_type)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Analysis failed: {str(e)}", "success": False}
        )

@app.post("/qa")
async def question_answer(request: Request):
    """Answer questions using external AI"""
    try:
        data = await request.json()
        question = data.get("question", "")
        context = data.get("context", "")
        
        if not question:
            raise HTTPException(status_code=400, detail="No question provided")
        
        result = await ai_service.answer_question(question, context)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Q&A failed: {str(e)}", "success": False}
        )

@app.post("/summarize")
async def summarize_content(request: Request):
    """Generate summaries using external AI"""
    try:
        data = await request.json()
        content = data.get("content", "")
        style = data.get("style", "concise")
        
        if not content:
            raise HTTPException(status_code=400, detail="No content provided")
        
        result = await ai_service.summarize_text(content, style)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Summarization failed: {str(e)}", "success": False}
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)