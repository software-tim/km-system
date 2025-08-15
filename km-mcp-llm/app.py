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
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                font-family: 'Courier New', monospace;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
            }}
            .endpoint:hover {{
                background: #e9ecef;
                border-left-color: #4c63d2;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .method {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                margin-right: 10px;
                color: white;
            }}
            .method.get {{ background: #61affe; }}
            .method.post {{ background: #49cc90; }}
            .footer {{
                padding: 20px 40px;
                background: #f9fafb;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
                border-top: 1px solid #e5e7eb;
            }}
            
            /* Form styles matching other services */
            .form-area {{
                margin-top: 15px;
                padding: 15px;
                background: #fff;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                display: none;
            }}
            .form-area.show {{ display: block; }}
            .form-group {{
                margin-bottom: 15px;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #333;
            }}
            .form-group input, .form-group textarea, .form-group select {{
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 14px;
            }}
            .form-group textarea {{
                min-height: 100px;
                resize: vertical;
            }}
            .btn {{
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin-right: 10px;
            }}
            .btn:hover {{
                background: #0056b3;
            }}
            
            /* Result display area */
            .result-area {{
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                display: none;
            }}
            .result-area.show {{ display: block; }}
            .result-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            .result-content {{
                background: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                overflow-x: auto;
                white-space: pre-wrap;
            }}
            .close-btn {{
                background: #dc3545;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                cursor: pointer;
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
                
                <div class="endpoint" onclick="callEndpoint('GET', '/health')">
                    <span class="method get">GET</span>
                    <span>/health</span> - Health check and AI provider status
                </div>

                <div class="endpoint" onclick="showForm('analyze')">
                    <span class="method post">POST</span>
                    <span>/analyze</span> - Analyze documents with cloud AI - comprehensive analysis, themes, entities, sentiment
                    <div class="form-area" id="form-analyze">
                        <div class="form-group">
                            <label>Document Text:</label>
                            <textarea id="analyze-content" placeholder="Paste document text here for AI analysis..." required></textarea>
                        </div>
                        <div class="form-group">
                            <label>Analysis Type:</label>
                            <select id="analyze-type">
                                <option value="comprehensive">Comprehensive Analysis</option>
                                <option value="themes">Theme Extraction</option>
                                <option value="entities">Entity Recognition</option>
                                <option value="sentiment">Sentiment Analysis</option>
                            </select>
                        </div>
                        <button class="btn" onclick="submitAnalysis()">🔍 Analyze with AI</button>
                        <button class="btn" style="background: #6c757d;" onclick="hideForm('analyze')">Cancel</button>
                    </div>
                </div>

                <div class="endpoint" onclick="showForm('qa')">
                    <span class="method post">POST</span>
                    <span>/qa</span> - Answer questions about documents using advanced AI models
                    <div class="form-area" id="form-qa">
                        <div class="form-group">
                            <label>Your Question:</label>
                            <textarea id="qa-question" rows="3" placeholder="Ask anything about your documents..." required></textarea>
                        </div>
                        <div class="form-group">
                            <label>Context (Optional):</label>
                            <textarea id="qa-context" rows="4" placeholder="Provide context or paste relevant document text..."></textarea>
                        </div>
                        <button class="btn" onclick="submitQA()">❓ Get AI Answer</button>
                        <button class="btn" style="background: #6c757d;" onclick="hideForm('qa')">Cancel</button>
                    </div>
                </div>

                <div class="endpoint" onclick="showForm('summarize')">
                    <span class="method post">POST</span>
                    <span>/summarize</span> - Generate intelligent summaries with multiple style options
                    <div class="form-area" id="form-summarize">
                        <div class="form-group">
                            <label>Text to Summarize:</label>
                            <textarea id="summarize-content" rows="6" placeholder="Paste text or document content here..." required></textarea>
                        </div>
                        <div class="form-group">
                            <label>Summary Style:</label>
                            <select id="summarize-style">
                                <option value="concise">Concise (2-3 sentences)</option>
                                <option value="detailed">Detailed (paragraph)</option>
                                <option value="bullets">Bullet Points</option>
                                <option value="executive">Executive Summary</option>
                            </select>
                        </div>
                        <button class="btn" onclick="submitSummarization()">📝 Generate Summary</button>
                        <button class="btn" style="background: #6c757d;" onclick="hideForm('summarize')">Cancel</button>
                    </div>
                </div>

                <div class="endpoint" onclick="callEndpoint('GET', '/docs')">
                    <span class="method get">GET</span>
                    <span>/docs</span> - Interactive API documentation (Swagger UI)
                </div>
            </div>

            <div class="footer">
                Knowledge Management System v1.0 | Status: Production Ready
            </div>
        </div>

        <!-- Result display area -->
        <div class="result-area" id="result-area">
            <div class="result-header">
                <h3 id="result-title">AI Results</h3>
                <button class="close-btn" onclick="hideResult()">Close</button>
            </div>
            <div class="result-content" id="result-content"></div>
        </div>

        <script>
            // Show form for POST endpoints (matching other services behavior)
            function showForm(formType) {{
                // Hide all forms first
                const forms = document.querySelectorAll('.form-area');
                forms.forEach(form => form.classList.remove('show'));
                
                // Show the requested form
                const form = document.getElementById(`form-${{formType}}`);
                if (form) {{
                    form.classList.add('show');
                }}
            }}
            
            // Hide form
            function hideForm(formType) {{
                const form = document.getElementById(`form-${{formType}}`);
                if (form) {{
                    form.classList.remove('show');
                }}
            }}
            
            // Call GET endpoints directly
            async function callEndpoint(method, path) {{
                showResult(`${{method}} ${{path}}`, 'Loading...');
                
                try {{
                    const response = await fetch(path, {{ method: method }});
                    const data = await response.json();
                    showResult(`${{method}} ${{path}}`, JSON.stringify(data, null, 2));
                }} catch (error) {{
                    showResult(`${{method}} ${{path}}`, `Error: ${{error.message}}`);
                }}
            }}
            
            // Submit analysis form
            async function submitAnalysis() {{
                const content = document.getElementById('analyze-content').value;
                const analysisType = document.getElementById('analyze-type').value;
                
                if (!content.trim()) {{
                    alert('Please enter document text for analysis');
                    return;
                }}
                
                showResult('POST /analyze', 'Analyzing with AI...');
                
                try {{
                    const response = await fetch('/analyze', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ content, analysis_type: analysisType }})
                    }});
                    
                    const result = await response.json();
                    displayAIResult(result, 'Document Analysis');
                    hideForm('analyze');
                }} catch (e) {{
                    showResult('POST /analyze', `Error: ${{e.message}}`);
                }}
            }}
            
            // Submit Q&A form
            async function submitQA() {{
                const question = document.getElementById('qa-question').value;
                const context = document.getElementById('qa-context').value;
                
                if (!question.trim()) {{
                    alert('Please enter a question');
                    return;
                }}
                
                showResult('POST /qa', 'Getting AI answer...');
                
                try {{
                    const response = await fetch('/qa', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ question, context }})
                    }});
                    
                    const result = await response.json();
                    displayAIResult(result, 'Q&A Response');
                    hideForm('qa');
                }} catch (e) {{
                    showResult('POST /qa', `Error: ${{e.message}}`);
                }}
            }}
            
            // Submit summarization form
            async function submitSummarization() {{
                const content = document.getElementById('summarize-content').value;
                const style = document.getElementById('summarize-style').value;
                
                if (!content.trim()) {{
                    alert('Please enter text to summarize');
                    return;
                }}
                
                showResult('POST /summarize', 'Generating summary...');
                
                try {{
                    const response = await fetch('/summarize', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ content, style }})
                    }});
                    
                    const result = await response.json();
                    displayAIResult(result, 'Summary');
                    hideForm('summarize');
                }} catch (e) {{
                    showResult('POST /summarize', `Error: ${{e.message}}`);
                }}
            }}
            
            // Display AI results in a user-friendly format
            function displayAIResult(result, title) {{
                if (!result.success) {{
                    showResult(title, `Error: ${{result.error}}`);
                    return;
                }}
                
                let formattedResult = `${{title}} Result\\n`;
                formattedResult += `Provider: ${{result.provider || 'OpenAI'}}\\n`;
                if (result.model) formattedResult += `Model: ${{result.model}}\\n`;
                formattedResult += `\\n`;
                
                if (result.analysis) {{
                    formattedResult += `Analysis:\\n${{result.analysis}}`;
                }} else if (result.answer) {{
                    formattedResult += `Answer:\\n${{result.answer}}`;
                }} else if (result.summary) {{
                    formattedResult += `Summary (${{result.style}}):\\n${{result.summary}}`;
                }} else {{
                    formattedResult += JSON.stringify(result, null, 2);
                }}
                
                showResult(title, formattedResult);
            }}
            
            // Show result in the result area
            function showResult(title, content) {{
                document.getElementById('result-title').textContent = title;
                document.getElementById('result-content').textContent = content;
                document.getElementById('result-area').classList.add('show');
                document.getElementById('result-area').scrollIntoView({{ behavior: 'smooth' }});
            }}
            
            // Hide result area
            function hideResult() {{
                document.getElementById('result-area').classList.remove('show');
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