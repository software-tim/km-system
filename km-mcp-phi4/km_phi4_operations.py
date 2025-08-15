import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import nltk

from km_phi4_config import settings
from km_phi4_schemas import *

logger = logging.getLogger(__name__)

class Phi4Operations:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.docs_client = httpx.AsyncClient(timeout=settings.km_docs_timeout)
        
    async def initialize_models(self):
        try:
            logger.info("Initializing Phi-4 models...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.phi4_model_name,
                trust_remote_code=True,
                cache_dir=settings.cache_dir if settings.enable_model_cache else None
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.phi4_model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True,
                cache_dir=settings.cache_dir if settings.enable_model_cache else None
            )
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=settings.max_tokens,
                temperature=settings.temperature,
                do_sample=True
            )
            
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
                
            logger.info("Models initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            return False
    
    async def check_docs_service(self) -> bool:
        try:
            response = await self.docs_client.get(f"{settings.km_docs_service_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Document service check failed: {e}")
            return False
    
    async def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        try:
            search_payload = {"limit": 20, "offset": 0}
            
            response = await self.docs_client.post(
                f"{settings.km_docs_service_url}/tools/search-documents",
                json=search_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("documents"):
                    for doc in data["documents"]:
                        if doc.get("id") == document_id:
                            return doc
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    async def search_documents(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            search_payload = {"query": query, "limit": limit, "offset": 0}
            
            response = await self.docs_client.post(
                f"{settings.km_docs_service_url}/tools/search-documents",
                json=search_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("documents", [])
            return []
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []
    
    async def analyze_document(self, request: AnalyzeDocumentRequest) -> AnalysisResult:
        start_time = time.time()
        
        try:
            document = await self.get_document_by_id(request.document_id)
            if not document:
                raise ValueError(f"Document {request.document_id} not found")
            
            content = document.get("content", "")
            title = document.get("title", "Untitled")
            
            if request.analysis_type == "summary":
                prompt = f"Summarize this document:\n\nTitle: {title}\n\nContent: {content}\n\nSummary:"
            else:
                prompt = f"Analyze this document:\n\nTitle: {title}\n\nContent: {content}\n\nAnalysis:"
            
            response = self.pipeline(prompt, max_new_tokens=500)[0]['generated_text']
            analysis_text = response.split(":")[-1].strip()
            
            results = {
                "analysis_text": analysis_text,
                "document_info": {
                    "title": title,
                    "content_length": len(content),
                    "classification": document.get("classification")
                }
            }
            
            processing_time = time.time() - start_time
            
            return AnalysisResult(
                document_id=request.document_id,
                document_title=title,
                analysis_type=request.analysis_type,
                results=results,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise
    
    async def answer_question(self, request: AnswerQuestionRequest) -> AnswerResponse:
        start_time = time.time()
        
        try:
            search_query = request.search_query or request.question
            documents = await self.search_documents(search_query, request.max_documents)
            
            if not documents:
                raise ValueError("No relevant documents found")
            
            context_parts = []
            sources = []
            
            for doc in documents:
                context_parts.append(f"Document: {doc.get('title', 'Untitled')}\nContent: {doc.get('content', '')[:1000]}")
                sources.append({
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "relevance": "high"
                })
            
            context = "\n\n".join(context_parts)
            
            prompt = f"Based on these documents, answer the question.\n\nContext:\n{context}\n\nQuestion: {request.question}\n\nAnswer:"
            
            response = self.pipeline(prompt, max_new_tokens=400)[0]['generated_text']
            answer_text = response.split("Answer:")[-1].strip()
            
            processing_time = time.time() - start_time
            
            return AnswerResponse(
                question=request.question,
                answer=answer_text,
                confidence_score=0.8,
                sources=sources,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            raise
    
    async def summarize_content(self, request: SummarizeContentRequest) -> SummaryResponse:
        start_time = time.time()
        
        try:
            content = ""
            
            if request.document_id:
                document = await self.get_document_by_id(request.document_id)
                if not document:
                    raise ValueError(f"Document {request.document_id} not found")
                content = document.get("content", "")
            elif request.content:
                content = request.content
            else:
                raise ValueError("Either document_id or content must be provided")
            
            if request.summary_type == "bullet_points":
                prompt = f"Create bullet points for:\n\n{content}\n\nBullet Points:"
            else:
                prompt = f"Summarize this content:\n\n{content}\n\nSummary:"
            
            response = self.pipeline(prompt, max_new_tokens=300)[0]['generated_text']
            summary_text = response.split(":")[-1].strip()
            
            key_points = []
            if "•" in summary_text or "-" in summary_text:
                lines = summary_text.split("\n")
                key_points = [line.strip() for line in lines if line.strip().startswith(("•", "-", "1.", "2."))]
            
            processing_time = time.time() - start_time
            
            return SummaryResponse(
                original_length=len(content),
                summary=summary_text,
                summary_type=request.summary_type,
                key_points=key_points[:5],
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Content summarization failed: {e}")
            raise
    
    async def extract_insights(self, request: ExtractInsightsRequest) -> InsightsResponse:
        start_time = time.time()
        
        try:
            documents = await self.search_documents(request.search_query, 5)
            
            if not documents:
                raise ValueError("No documents found for insight extraction")
            
            combined_content = "\n\n".join([
                f"Document: {doc.get('title', 'Untitled')}\n{doc.get('content', '')[:800]}"
                for doc in documents
            ])
            
            insights = {}
            
            for insight_type in request.insight_types:
                if insight_type == "themes":
                    prompt = f"Identify themes in these documents:\n\n{combined_content}\n\nThemes:"
                elif insight_type == "entities":
                    prompt = f"Extract entities from these documents:\n\n{combined_content}\n\nEntities:"
                else:
                    continue
                
                response = self.pipeline(prompt, max_new_tokens=200)[0]['generated_text']
                insight_text = response.split(":")[-1].strip()
                insights[insight_type] = insight_text
            
            processing_time = time.time() - start_time
            
            return InsightsResponse(
                insights=insights,
                document_count=len(documents),
                insight_types=request.insight_types,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            raise
