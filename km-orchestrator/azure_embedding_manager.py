"""
Azure-optimized Embedding Manager for Knowledge Management System
Handles generation and storage of vector embeddings for semantic search in Azure
"""
import hashlib
import json
import struct
import os
from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime
import asyncio
import logging
from openai import AsyncOpenAI
import pyodbc
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ChunkEmbedding:
    chunk_text: str
    chunk_index: int
    embedding: List[float]
    
@dataclass
class EmbeddingJob:
    document_id: int
    status: str
    total_chunks: int
    processed_chunks: int

class AzureEmbeddingManager:
    def __init__(self):
        """Initialize with Azure managed identity or environment variables"""
        # Use environment variables in Azure App Service
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # Build connection string from existing Azure App Service settings
        server = os.environ.get("KM_SQL_SERVER", "knowledge-sql.database.windows.net")
        database = os.environ.get("KM_SQL_DATABASE", "knowledge-base")
        username = os.environ.get("KM_SQL_USERNAME", "mcpadmin")
        password = os.environ.get("KM_SQL_PASSWORD", "Theodore03$")
        
        self.connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        
        self.embedding_model = "text-embedding-ada-002"
        self.embedding_dimension = 1536
        self.batch_size = 20  # Process embeddings in batches
        
    def get_connection(self):
        """Get database connection with retry logic for Azure SQL"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                conn = pyodbc.connect(self.connection_string)
                return conn
            except pyodbc.Error as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database connection attempt {attempt + 1} failed, retrying...")
                    asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
        
    @staticmethod
    def embedding_to_binary(embedding: List[float]) -> bytes:
        """Convert embedding vector to binary format for storage"""
        return struct.pack(f'{len(embedding)}f', *embedding)
    
    @staticmethod
    def binary_to_embedding(binary_data: bytes) -> List[float]:
        """Convert binary data back to embedding vector"""
        float_count = len(binary_data) // 4
        return list(struct.unpack(f'{float_count}f', binary_data))
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding with retry logic for API calls"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = await self.openai_client.embeddings.create(
                    input=text[:8000],  # Limit text length for API
                    model=self.embedding_model
                )
                return response.data[0].embedding
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Embedding generation attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Error generating embedding after {max_retries} attempts: {e}")
                    raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts with retry"""
        max_retries = 3
        
        # Truncate texts to API limit
        truncated_texts = [text[:8000] for text in texts]
        
        for attempt in range(max_retries):
            try:
                response = await self.openai_client.embeddings.create(
                    input=truncated_texts,
                    model=self.embedding_model
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Batch embedding attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Error generating batch embeddings: {e}")
                    raise
    
    def create_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []
            
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    async def process_document(self, document_id: int, content: str, title: str = None):
        """Process document and generate embeddings - Azure optimized"""
        if not content:
            logger.warning(f"Document {document_id} has no content, skipping")
            return
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if already processed
            cursor.execute("""
                SELECT COUNT(*) FROM document_embeddings WHERE document_id = ?
            """, document_id)
            if cursor.fetchone()[0] > 0:
                logger.info(f"Document {document_id} already has embeddings, skipping")
                return
            
            # Create embedding job
            cursor.execute("""
                INSERT INTO embedding_jobs (document_id, status, started_at)
                OUTPUT INSERTED.id
                VALUES (?, 'processing', GETUTCDATE())
            """, document_id)
            job_id = cursor.fetchone()[0]
            conn.commit()
            
            # Create chunks
            chunks = self.create_chunks(content)
            total_chunks = len(chunks)
            
            if total_chunks == 0:
                logger.warning(f"Document {document_id} produced no chunks")
                cursor.execute("""
                    UPDATE embedding_jobs 
                    SET status = 'completed', total_chunks = 0, completed_at = GETUTCDATE()
                    WHERE id = ?
                """, job_id)
                conn.commit()
                return
            
            # Update job with total chunks
            cursor.execute("""
                UPDATE embedding_jobs 
                SET total_chunks = ?
                WHERE id = ?
            """, total_chunks, job_id)
            conn.commit()
            
            logger.info(f"Processing {total_chunks} chunks for document {document_id}")
            
            # Process chunks in batches
            for i in range(0, total_chunks, self.batch_size):
                batch_chunks = chunks[i:i + self.batch_size]
                batch_indices = list(range(i, min(i + self.batch_size, total_chunks)))
                
                try:
                    # Generate embeddings for batch
                    embeddings = await self.generate_embeddings_batch(batch_chunks)
                    
                    # Store embeddings using parameterized queries
                    for chunk_text, chunk_index, embedding in zip(batch_chunks, batch_indices, embeddings):
                        binary_embedding = self.embedding_to_binary(embedding)
                        
                        cursor.execute("""
                            INSERT INTO document_embeddings 
                            (document_id, chunk_index, chunk_text, embedding_vector, embedding_model, vector_dimension)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, document_id, chunk_index, chunk_text, binary_embedding, 
                            self.embedding_model, self.embedding_dimension)
                    
                    # Update progress
                    processed = min(i + self.batch_size, total_chunks)
                    cursor.execute("""
                        UPDATE embedding_jobs 
                        SET processed_chunks = ?
                        WHERE id = ?
                    """, processed, job_id)
                    conn.commit()
                    
                    logger.info(f"Processed {processed}/{total_chunks} chunks for document {document_id}")
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error processing batch {i//self.batch_size + 1} for document {document_id}: {e}")
                    raise
            
            # Mark job as completed
            cursor.execute("""
                UPDATE embedding_jobs 
                SET status = 'completed', completed_at = GETUTCDATE()
                WHERE id = ?
            """, job_id)
            conn.commit()
            
            logger.info(f"Successfully processed document {document_id} with {total_chunks} chunks")
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            cursor.execute("""
                UPDATE embedding_jobs 
                SET status = 'failed', error_message = ?, completed_at = GETUTCDATE()
                WHERE id = ? AND status = 'processing'
            """, str(e)[:1000], job_id)
            conn.commit()
            raise
        finally:
            cursor.close()
            conn.close()
    
    async def semantic_search(self, query: str, limit: int = 20, threshold: float = 0.0) -> List[Dict]:
        """Perform semantic search using cosine similarity - Azure optimized"""
        # Get query embedding
        query_embedding = await self.generate_embedding(query)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # For now, fetch all embeddings and calculate similarity in memory
            # In production, consider using Azure Cognitive Search or a vector database
            cursor.execute("""
                SELECT TOP 1000
                    de.document_id,
                    de.chunk_index,
                    de.chunk_text,
                    de.embedding_vector,
                    d.title,
                    d.classification,
                    d.metadata
                FROM document_embeddings de
                JOIN documents d ON de.document_id = d.id
                ORDER BY de.created_at DESC
            """)
            
            results = []
            query_np = np.array(query_embedding)
            
            for row in cursor.fetchall():
                # Calculate similarity
                doc_embedding = self.binary_to_embedding(row[3])
                doc_np = np.array(doc_embedding)
                
                # Cosine similarity
                similarity = np.dot(query_np, doc_np) / (np.linalg.norm(query_np) * np.linalg.norm(doc_np))
                
                if similarity >= threshold:
                    results.append({
                        'document_id': row[0],
                        'chunk_index': row[1],
                        'chunk_text': row[2],
                        'document_title': row[4],
                        'classification': row[5],
                        'metadata': json.loads(row[6]) if row[6] else {},
                        'similarity_score': float(similarity)
                    })
            
            # Sort by similarity score
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Log search
            if results:
                cursor.execute("""
                    INSERT INTO search_queries (query_text, user_id, results_count, execution_time_ms)
                    OUTPUT INSERTED.id
                    VALUES (?, 'system', ?, 0)
                """, query, len(results[:limit]))
                query_id = cursor.fetchone()[0]
                conn.commit()
            
            return results[:limit]
            
        finally:
            cursor.close()
            conn.close()

# Azure Function endpoint for processing documents
async def process_document_endpoint(document_id: int, content: str, title: str = None):
    """Endpoint to be called from Azure Functions or orchestrator"""
    manager = AzureEmbeddingManager()
    await manager.process_document(document_id, content, title)

# Azure Function endpoint for search
async def search_endpoint(query: str, limit: int = 20) -> List[Dict]:
    """Endpoint to be called from Azure Functions or orchestrator"""
    manager = AzureEmbeddingManager()
    return await manager.semantic_search(query, limit)