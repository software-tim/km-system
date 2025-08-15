from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

from km_llm_config import settings
from km_llm_schemas import *
from km_llm_operations import llmOperations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="km-mcp-llm API",
    description="AI-powered document analysis using Phi-4 model",
    version=settings.version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_ops = llmOperations()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting km-mcp-llm service")
    success = await llm_ops.initialize_models()
    if not success:
        logger.error("Failed to initialize models")
    logger.info("Service started")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>km-mcp-llm AI Analysis</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 1000px;
            width: 100%;
        }
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 30px;
        }
        .icon {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 20px;
            font-size: 24px;
            color: white;
        }
        h1 { color: #333; font-size: 32px; }
        .status {
            background: #d4f4dd;
            border-left: 4px solid #4caf50;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 5px;
            display: flex;
            align-items: center;
        }
        .status-icon { color: #4caf50; margin-right: 10px; font-size: 20px; }
        .stats {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .stat-value { color: #333; font-weight: bold; }
        .endpoint {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            font-family: 'Courier New', monospace;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .endpoint:hover {
            background: #e9ecef;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .method {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            margin-right: 10px;
            color: white;
        }
        .method.get { background: #61affe; }
        .method.post { background: #49cc90; }
        .ai-badge {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 10px;
        }
        .form-area {
            margin-top: 15px;
            padding: 15px;
            background: #fff;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            display: none;
        }
        .form-area.show { display: block; }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
        }
        .btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
        }
        .btn:hover { background: #0056b3; }
        .result-area {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .result-area.show { display: block; }
        .result-content {
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">🧠</div>
            <h1>km-mcp-llm AI Analysis <span class="ai-badge">AI POWERED</span></h1>
        </div>

        <div class="status">
            <span class="status-icon">✅</span>
            <div>
                <strong>AI Service is Running</strong><br>
                <span style="color: #666;">Phi-4 powered document analysis and reasoning</span>
            </div>
        </div>

        <div class="stats">
            <h3>🤖 AI Service Status</h3>
            <div class="stat-item">
                <span>Model Status:</span>
                <span class="stat-value" id="model-status">Loading...</span>
            </div>
            <div class="stat-item">
                <span>Document Service:</span>
                <span class="stat-value" id="docs-status">Loading...</span>
            </div>
        </div>

        <h2>🔧 AI Analysis Tools:</h2>
        
        <div class="endpoint" onclick="callEndpoint('GET', '/health')">
            <span class="method get">GET</span>
            <span>/health</span> - AI service health and model status
        </div>
        
        <div class="endpoint" onclick="showForm('analyze-document')">
            <span class="method post">POST</span>
            <span>/tools/analyze-document</span> - Analyze specific document with AI
            <div class="form-area" id="form-analyze-document">
                <div class="form-group">
                    <label>Document ID:</label>
                    <input type="number" id="analyze-doc-id" placeholder="Enter document ID" required>
                </div>
                <div class="form-group">
                    <label>Analysis Type:</label>
                    <select id="analyze-type">
                        <option value="general">General Analysis</option>
                        <option value="summary">Summary</option>
                        <option value="insights">Insights</option>
                    </select>
                </div>
                <button class="btn" onclick="submitAnalyzeDocument()">Analyze Document</button>
                <button class="btn" style="background: #6c757d;" onclick="hideForm('analyze-document')">Cancel</button>
            </div>
        </div>
        
        <div class="endpoint" onclick="showForm('answer-question')">
            <span class="method post">POST</span>
            <span>/tools/answer-question</span> - Ask AI questions about documents
            <div class="form-area" id="form-answer-question">
                <div class="form-group">
                    <label>Question:</label>
                    <textarea id="question-text" placeholder="Ask any question about your documents..."></textarea>
                </div>
                <div class="form-group">
                    <label>Search Query (optional):</label>
                    <input type="text" id="question-search" placeholder="Keywords to find relevant documents">
                </div>
                <button class="btn" onclick="submitAnswerQuestion()">Ask AI</button>
                <button class="btn" style="background: #6c757d;" onclick="hideForm('answer-question')">Cancel</button>
            </div>
        </div>
        
        <div class="endpoint" onclick="showForm('summarize-content')">
            <span class="method post">POST</span>
            <span>/tools/summarize-content</span> - AI-powered content summarization
            <div class="form-area" id="form-summarize-content">
                <div class="form-group">
                    <label>Document ID (optional):</label>
                    <input type="number" id="summarize-doc-id" placeholder="Document ID to summarize">
                </div>
                <div class="form-group">
                    <label>Direct Content (optional):</label>
                    <textarea id="summarize-content" placeholder="Or paste content directly..."></textarea>
                </div>
                <div class="form-group">
                    <label>Summary Type:</label>
                    <select id="summarize-type">
                        <option value="concise">Concise</option>
                        <option value="detailed">Detailed</option>
                        <option value="bullet_points">Bullet Points</option>
                    </select>
                </div>
                <button class="btn" onclick="submitSummarizeContent()">Generate Summary</button>
                <button class="btn" style="background: #6c757d;" onclick="hideForm('summarize-content')">Cancel</button>
            </div>
        </div>
        
        <div class="endpoint" onclick="showForm('extract-insights')">
            <span class="method post">POST</span>
            <span>/tools/extract-insights</span> - Extract AI insights from documents
            <div class="form-area" id="form-extract-insights">
                <div class="form-group">
                    <label>Search Query:</label>
                    <input type="text" id="insights-search" placeholder="Find documents to analyze">
                </div>
                <button class="btn" onclick="submitExtractInsights()">Extract Insights</button>
                <button class="btn" style="background: #6c757d;" onclick="hideForm('extract-insights')">Cancel</button>
            </div>
        </div>
        
        <div class="endpoint" onclick="window.open('/docs', '_blank')">
            <span class="method get">GET</span>
            <span>/docs</span> - Interactive API documentation
        </div>

        <div class="result-area" id="result-area">
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <h3 id="result-title">AI Analysis Result</h3>
                <button onclick="hideResult()" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 5px;">Close</button>
            </div>
            <div class="result-content" id="result-content"></div>
        </div>

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center; color: #999; font-size: 14px;">
            Knowledge Management System v1.0 | AI Analysis Service | Powered by Phi-4
        </div>
    </div>

    <script>
        async function loadStatus() {
            try {
                const healthRes = await fetch('/health');
                const health = await healthRes.json();
                document.getElementById('model-status').textContent = health.model_loaded ? '✅ Loaded' : '❌ Loading...';
                document.getElementById('docs-status').textContent = health.docs_service_connected ? '✅ Connected' : '❌ Disconnected';
            } catch (error) {
                document.getElementById('model-status').textContent = '❌ Error';
                document.getElementById('docs-status').textContent = '❌ Error';
            }
        }
        
        async function callEndpoint(method, path) {
            showResult(method + ' ' + path, 'Loading...');
            try {
                const response = await fetch(path, { method: method });
                const data = await response.json();
                showResult(method + ' ' + path, JSON.stringify(data, null, 2));
            } catch (error) {
                showResult(method + ' ' + path, 'Error: ' + error.message);
            }
        }
        
        function showForm(formType) {
            const forms = document.querySelectorAll('.form-area');
            forms.forEach(form => form.classList.remove('show'));
            const form = document.getElementById('form-' + formType);
            if (form) form.classList.add('show');
        }
        
        function hideForm(formType) {
            const form = document.getElementById('form-' + formType);
            if (form) form.classList.remove('show');
        }
        
        async function submitAnalyzeDocument() {
            const data = {
                document_id: parseInt(document.getElementById('analyze-doc-id').value),
                analysis_type: document.getElementById('analyze-type').value
            };
            showResult('POST /tools/analyze-document', 'Analyzing document with AI...');
            try {
                const response = await fetch('/tools/analyze-document', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                showResult('POST /tools/analyze-document', JSON.stringify(result, null, 2));
                hideForm('analyze-document');
            } catch (error) {
                showResult('POST /tools/analyze-document', 'Error: ' + error.message);
            }
        }
        
        async function submitAnswerQuestion() {
            const data = {
                question: document.getElementById('question-text').value,
                search_query: document.getElementById('question-search').value || null
            };
            showResult('POST /tools/answer-question', 'AI is analyzing documents...');
            try {
                const response = await fetch('/tools/answer-question', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                showResult('POST /tools/answer-question', JSON.stringify(result, null, 2));
                hideForm('answer-question');
            } catch (error) {
                showResult('POST /tools/answer-question', 'Error: ' + error.message);
            }
        }
        
        async function submitSummarizeContent() {
            const data = { summary_type: document.getElementById('summarize-type').value };
            const docId = document.getElementById('summarize-doc-id').value;
            const content = document.getElementById('summarize-content').value;
            
            if (docId) {
                data.document_id = parseInt(docId);
            } else if (content) {
                data.content = content;
            } else {
                alert('Please provide either a document ID or content');
                return;
            }
            
            showResult('POST /tools/summarize-content', 'AI is generating summary...');
            try {
                const response = await fetch('/tools/summarize-content', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                showResult('POST /tools/summarize-content', JSON.stringify(result, null, 2));
                hideForm('summarize-content');
            } catch (error) {
                showResult('POST /tools/summarize-content', 'Error: ' + error.message);
            }
        }
        
        async function submitExtractInsights() {
            const data = {
                search_query: document.getElementById('insights-search').value,
                insight_types: ['themes', 'entities']
            };
            showResult('POST /tools/extract-insights', 'AI is extracting insights...');
            try {
                const response = await fetch('/tools/extract-insights', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                showResult('POST /tools/extract-insights', JSON.stringify(result, null, 2));
                hideForm('extract-insights');
            } catch (error) {
                showResult('POST /tools/extract-insights', 'Error: ' + error.message);
            }
        }
        
        function showResult(title, content) {
            document.getElementById('result-title').textContent = title;
            document.getElementById('result-content').textContent = content;
            document.getElementById('result-area').classList.add('show');
            document.getElementById('result-area').scrollIntoView({ behavior: 'smooth' });
        }
        
        function hideResult() {
            document.getElementById('result-area').classList.remove('show');
        }
        
        loadStatus();
        setInterval(loadStatus, 30000);
    </script>
</body>
</html>
    """

@app.get("/health")
async def health_check():
    docs_connected = await llm_ops.check_docs_service()
    model_loaded = llm_ops.model is not None
    
    return ServiceHealth(
        status="healthy" if model_loaded else "initializing",
        service="km-mcp-llm",
        version=settings.version,
        model_loaded=model_loaded,
        docs_service_connected=docs_connected,
        timestamp=datetime.utcnow()
    )

@app.get("/tools")
async def list_tools():
    return {
        "available_tools": [
            {"name": "analyze-document", "description": "Analyze a specific document using AI"},
            {"name": "answer-question", "description": "Answer questions using document context"},
            {"name": "summarize-content", "description": "Generate AI-powered summaries"},
            {"name": "extract-insights", "description": "Extract insights from documents"}
        ]
    }

@app.post("/tools/analyze-document")
async def analyze_document(request: AnalyzeDocumentRequest):
    try:
        if llm_ops.model is None:
            raise HTTPException(status_code=503, detail="AI model not loaded yet")
        
        result = await llm_ops.analyze_document(request)
        return ToolResponse(success=True, result=result.dict(), processing_time=result.processing_time)
    
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        return ToolResponse(success=False, error=str(e))

@app.post("/tools/answer-question")
async def answer_question(request: AnswerQuestionRequest):
    try:
        if llm_ops.model is None:
            raise HTTPException(status_code=503, detail="AI model not loaded yet")
        
        result = await llm_ops.answer_question(request)
        return ToolResponse(success=True, result=result.dict(), processing_time=result.processing_time)
    
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        return ToolResponse(success=False, error=str(e))

@app.post("/tools/summarize-content")
async def summarize_content(request: SummarizeContentRequest):
    try:
        if llm_ops.model is None:
            raise HTTPException(status_code=503, detail="AI model not loaded yet")
        
        result = await llm_ops.summarize_content(request)
        return ToolResponse(success=True, result=result.dict(), processing_time=result.processing_time)
    
    except Exception as e:
        logger.error(f"Content summarization failed: {e}")
        return ToolResponse(success=False, error=str(e))

@app.post("/tools/extract-insights")
async def extract_insights(request: ExtractInsightsRequest):
    try:
        if llm_ops.model is None:
            raise HTTPException(status_code=503, detail="AI model not loaded yet")
        
        result = await llm_ops.extract_insights(request)
        return ToolResponse(success=True, result=result.dict(), processing_time=result.processing_time)
    
    except Exception as e:
        logger.error(f"Insight extraction failed: {e}")
        return ToolResponse(success=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)


