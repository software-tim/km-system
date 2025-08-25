"""
Embedding Manager for Knowledge Management System
Handles generation and storage of vector embeddings for semantic search
"""
import hashlib
import json
import struct
from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime
import asyncio
import logging
from openai import AsyncOpenAI
import pyodbc
import pyodbc
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
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

class EmbeddingManager:
    def __init__(self, connection_string: str, openai_api_key: str):
        self.connection_string = connection_string
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-ada-002"
        self.embedding_dimension = 1536
        self.batch_size = 20  # Process embeddings in batches
        
    def get_connection(self):
        """Get database connection"""
        return pyodbc.connect(self.connection_string)
        
    @staticmethod
    def embedding_to_binary(embedding: List[float]) -> bytes:
        """Convert embedding vector to binary format for storage"""
        # Pack as array of floats (4 bytes each)
        return struct.pack(f'{len(embedding)}f', *embedding)
    
    @staticmethod
    def binary_to_embedding(binary_data: bytes) -> List[float]:
        """Convert binary data back to embedding vector"""
        # Unpack binary data to floats
        float_count = len(binary_data) // 4
        return list(struct.unpack(f'{float_count}f', binary_data))
    
    @staticmethod
    def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            response = await self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in one API call"""
        try:
            response = await self.openai_client.embeddings.create(
                input=texts,
                model=self.embedding_model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def create_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks for embedding"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:  # Don't add empty chunks
                chunks.append(chunk)
        
        return chunks
    
    async def process_document(self, document_id: int, content: str, title: str = None):
        """Process a document and generate embeddings for all chunks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create embedding job
            cursor.execute("""
                INSERT INTO embedding_jobs (document_id, status, started_at)
                VALUES (?, 'processing', GETUTCDATE())
            """, document_id)
            job_id = cursor.lastrowid
            conn.commit()
            
            # Create chunks
            chunks = self.create_chunks(content)
            total_chunks = len(chunks)
            
            # Update job with total chunks
            cursor.execute("""
                UPDATE embedding_jobs 
                SET total_chunks = ?
                WHERE id = ?
            """, total_chunks, job_id)
            conn.commit()
            
            # Process chunks in batches
            for i in range(0, total_chunks, self.batch_size):
                batch_chunks = chunks[i:i + self.batch_size]
                batch_indices = list(range(i, min(i + self.batch_size, total_chunks)))
                
                # Generate embeddings for batch
                embeddings = await self.generate_embeddings_batch(batch_chunks)
                
                # Store embeddings
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
            
            # Mark job as completed
            cursor.execute("""
                UPDATE embedding_jobs 
                SET status = 'completed', completed_at = GETUTCDATE()
                WHERE id = ?
            """, job_id)
            conn.commit()
            
            # Also generate embedding for the title if provided
            if title:
                await self.process_knowledge_node(
                    node_id=f"doc_title_{document_id}",
                    text=title
                )
            
            logger.info(f"Successfully processed document {document_id} with {total_chunks} chunks")
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            cursor.execute("""
                UPDATE embedding_jobs 
                SET status = 'failed', error_message = ?, completed_at = GETUTCDATE()
                WHERE document_id = ? AND status = 'processing'
            """, str(e), document_id)
            conn.commit()
            raise
        finally:
            cursor.close()
            conn.close()
    
    async def process_knowledge_node(self, node_id: str, text: str):
        """Generate and store embedding for a knowledge graph node"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Generate embedding
            embedding = await self.generate_embedding(text)
            binary_embedding = self.embedding_to_binary(embedding)
            
            # Check if embedding exists
            cursor.execute("SELECT node_id FROM node_embeddings WHERE node_id = ?", node_id)
            exists = cursor.fetchone()
            
            if exists:
                # Update existing
                cursor.execute("""
                    UPDATE node_embeddings 
                    SET embedding_vector = ?, updated_at = GETUTCDATE()
                    WHERE node_id = ?
                """, binary_embedding, node_id)
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO node_embeddings 
                    (node_id, embedding_vector, embedding_model, vector_dimension)
                    VALUES (?, ?, ?, ?)
                """, node_id, binary_embedding, self.embedding_model, self.embedding_dimension)
            
            conn.commit()
            logger.info(f"Processed knowledge node {node_id}")
            
        except Exception as e:
            logger.error(f"Error processing knowledge node {node_id}: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    async def get_or_create_query_embedding(self, query: str) -> Tuple[List[float], bool]:
        """Get query embedding from cache or generate new one"""
        # Normalize query for caching
        normalized_query = query.lower().strip()
        query_hash = hashlib.sha256(normalized_query.encode()).hexdigest()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check cache
            cursor.execute("""
                SELECT embedding_vector FROM query_embeddings_cache 
                WHERE query_hash = ?
            """, query_hash)
            result = cursor.fetchone()
            
            if result:
                # Update access count and timestamp
                cursor.execute("""
                    UPDATE query_embeddings_cache 
                    SET access_count = access_count + 1, 
                        last_accessed = GETUTCDATE()
                    WHERE query_hash = ?
                """, query_hash)
                conn.commit()
                
                embedding = self.binary_to_embedding(result[0])
                return embedding, True  # From cache
            
            # Generate new embedding
            embedding = await self.generate_embedding(query)
            binary_embedding = self.embedding_to_binary(embedding)
            
            # Store in cache
            cursor.execute("""
                INSERT INTO query_embeddings_cache 
                (query_hash, query_text, embedding_vector, embedding_model, vector_dimension)
                VALUES (?, ?, ?, ?, ?)
            """, query_hash, query, binary_embedding, self.embedding_model, self.embedding_dimension)
            conn.commit()
            
            return embedding, False  # Newly generated
            
        finally:
            cursor.close()
            conn.close()
    
    async def semantic_search(self, query: str, limit: int = 20, threshold: float = 0.7) -> List[Dict]:
        """Perform semantic search using cosine similarity"""
        # Get query embedding
        query_embedding, from_cache = await self.get_or_create_query_embedding(query)
        logger.info(f"Query embedding {'from cache' if from_cache else 'newly generated'}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Fetch all document embeddings
            # In production, you'd want to use a vector database or SQL Server's vector functions
            cursor.execute("""
                SELECT 
                    de.document_id,
                    de.chunk_index,
                    de.chunk_text,
                    de.embedding_vector,
                    d.title,
                    d.classification,
                    d.metadata
                FROM document_embeddings de
                JOIN documents d ON de.document_id = d.id
            """)
            
            results = []
            for row in cursor.fetchall():
                # Calculate similarity
                doc_embedding = self.binary_to_embedding(row[3])
                similarity = self.calculate_cosine_similarity(query_embedding, doc_embedding)
                
                if similarity >= threshold:
                    results.append({
                        'document_id': row[0],
                        'chunk_index': row[1],
                        'chunk_text': row[2],
                        'document_title': row[4],
                        'classification': row[5],
                        'metadata': json.loads(row[6]) if row[6] else {},
                        'similarity_score': similarity
                    })
            
            # Sort by similarity score
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Log search results
            if results:
                cursor.execute("""
                    INSERT INTO search_queries (query_text, user_id, results_count, execution_time_ms)
                    VALUES (?, 'system', ?, 0)
                """, query, len(results[:limit]))
                query_id = cursor.lastrowid
                
                # Log individual results
                for i, result in enumerate(results[:limit]):
                    cursor.execute("""
                        INSERT INTO search_results_log 
                        (query_id, document_id, chunk_index, similarity_score, rank_position)
                        VALUES (?, ?, ?, ?, ?)
                    """, query_id, result['document_id'], result['chunk_index'], 
                        result['similarity_score'], i + 1)
                
                conn.commit()
            
            return results[:limit]
            
        finally:
            cursor.close()
            conn.close()
    
    async def process_all_existing_documents(self):
        """Process all documents that don't have embeddings yet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Find documents without embeddings
            cursor.execute("""
                SELECT d.id, d.content, d.title
                FROM documents d
                LEFT JOIN document_embeddings de ON d.id = de.document_id
                WHERE de.id IS NULL
                ORDER BY d.created_at DESC
            """)
            
            documents = cursor.fetchall()
            total = len(documents)
            
            logger.info(f"Found {total} documents without embeddings")
            
            for i, (doc_id, content, title) in enumerate(documents):
                logger.info(f"Processing document {i+1}/{total}: {title}")
                await self.process_document(doc_id, content, title)
                
                # Add a small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            
            logger.info(f"Completed processing {total} documents")
            
        finally:
            cursor.close()
            conn.close()

# Usage example
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize manager
    manager = EmbeddingManager(
        connection_string=os.getenv("SQL_CONNECTION_STRING"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Process all existing documents
    asyncio.run(manager.process_all_existing_documents())