#!/usr/bin/env python3
"""
Document Operations module using SQLAlchemy for Azure SQL Database
"""

from typing import Any, Dict, List, Optional
import logging
import asyncio
import json
import base64
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.pool import NullPool
from km_docs_config import Settings
from km_docs_schemas import DocumentCreate, DocumentUpdate

logger = logging.getLogger(__name__)


class DocumentOperations:
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Build connection string
        connection_string = settings.get_connection_string()
        
        # Create engine
        self.engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=settings.debug
        )
        
        logger.info(f"Connected to Azure SQL Database: {settings.km_sql_database}")
    
    async def initialize_database(self):
        """Initialize database - create documents table if not exists"""
        create_table_query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='documents' AND xtype='U')
        CREATE TABLE documents (
            id INT IDENTITY(1,1) PRIMARY KEY,
            title NVARCHAR(500) NOT NULL,
            content NVARCHAR(MAX) NOT NULL,
            classification NVARCHAR(100),
            entities NVARCHAR(MAX),
            metadata NVARCHAR(MAX),
            file_data VARBINARY(MAX),
            file_name NVARCHAR(255),
            file_type NVARCHAR(100),
            file_size BIGINT,
            is_active BIT DEFAULT 1,
            created_at DATETIME2 DEFAULT GETDATE(),
            updated_at DATETIME2 DEFAULT GETDATE()
        )
        """
        
        # Create indexes
        create_indexes_query = """
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_documents_classification')
            CREATE INDEX IX_documents_classification ON documents(classification);
        
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_documents_is_active')
            CREATE INDEX IX_documents_is_active ON documents(is_active);
        
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_documents_created_at')
            CREATE INDEX IX_documents_created_at ON documents(created_at DESC);
        """
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._execute_query, create_table_query)
            await loop.run_in_executor(None, self._execute_query, create_indexes_query)
            logger.info("Documents table and indexes initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _execute_query(self, query: str, params: Dict = None):
        """Execute a query synchronously"""
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            conn.commit()
            return result
    
    async def check_connection(self):
        """Check database connection"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._execute_query,
                "SELECT 1 as test"
            )
            return True
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    async def store_document(self, document: DocumentCreate):
        """Store a new document"""
        try:
            # Prepare data
            entities_json = json.dumps(document.entities) if document.entities else None
            metadata_json = json.dumps(document.metadata) if document.metadata else None
            
            query = """
            INSERT INTO documents (
                title, content, classification, entities, metadata,
                file_data, file_name, file_type, file_size
            ) 
            OUTPUT INSERTED.id
            VALUES (
                :title, :content, :classification, :entities, :metadata,
                :file_data, :file_name, :file_type, :file_size
            )
            """
            
            params = {
                'title': document.title,
                'content': document.content,
                'classification': document.classification,
                'entities': entities_json,
                'metadata': metadata_json,
                'file_data': document.file_data,
                'file_name': document.file_name,
                'file_type': document.file_type,
                'file_size': document.file_size
            }
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._execute_with_result(query, params)
            )
            
            document_id = result[0] if result else None
            
            return {
                "success": True,
                "document_id": document_id,
                "message": "Document stored successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_with_result(self, query: str, params: Dict = None):
        """Execute query and return results"""
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            conn.commit()
            
            if result.returns_rows:
                return result.fetchone()
            return None
    
    async def search_documents(self, query: Optional[str] = None,
                              classification: Optional[str] = None,
                              limit: int = 10, offset: int = 0):
        """Search documents"""
        try:
            where_clauses = ["is_active = 1"]
            params = {'limit': limit, 'offset': offset}
            
            if query:
                where_clauses.append("(title LIKE :query OR content LIKE :query)")
                params['query'] = f"%{query}%"
            
            if classification:
                where_clauses.append("classification = :classification")
                params['classification'] = classification
            
            where_clause = " AND ".join(where_clauses)
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM documents WHERE {where_clause}"
            
            # Get documents
            search_query = f"""
            SELECT 
                id, title, content, classification, entities, metadata,
                CASE WHEN file_data IS NOT NULL THEN 1 ELSE 0 END as has_file,
                file_name, file_type, file_size,
                created_at, updated_at
            FROM documents
            WHERE {where_clause}
            ORDER BY created_at DESC
            OFFSET :offset ROWS
            FETCH NEXT :limit ROWS ONLY
            """
            
            loop = asyncio.get_event_loop()
            
            # Execute count query
            total_result = await loop.run_in_executor(
                None,
                lambda: self._get_scalar(count_query, params)
            )
            
            # Execute search query
            docs_result = await loop.run_in_executor(
                None,
                lambda: self._get_all(search_query, params)
            )
            
            # Process results
            documents = []
            for row in docs_result:
                doc = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'classification': row[3],
                    'entities': json.loads(row[4]) if row[4] else None,
                    'metadata': json.loads(row[5]) if row[5] else None,
                    'has_file': bool(row[6]),
                    'file_name': row[7],
                    'file_type': row[8],
                    'file_size': row[9],
                    'created_at': row[10].isoformat() if row[10] else None,
                    'updated_at': row[11].isoformat() if row[11] else None
                }
                documents.append(doc)
            
            return {
                "documents": documents,
                "total": total_result or 0
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"documents": [], "total": 0}
    
    def _get_scalar(self, query: str, params: Dict = None):
        """Get a single scalar value"""
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            return result.scalar()
    
    def _get_all(self, query: str, params: Dict = None):
        """Get all rows"""
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            return result.fetchall()
    
    async def get_document(self, document_id: int):
        """Get a document by ID"""
        try:
            query = """
            SELECT 
                id, title, content, classification, entities, metadata,
                CASE WHEN file_data IS NOT NULL THEN 1 ELSE 0 END as has_file,
                file_name, file_type, file_size,
                created_at, updated_at
            FROM documents
            WHERE id = :id AND is_active = 1
            """
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._get_one(query, {'id': document_id})
            )
            
            if result:
                return {
                    'id': result[0],
                    'title': result[1],
                    'content': result[2],
                    'classification': result[3],
                    'entities': json.loads(result[4]) if result[4] else None,
                    'metadata': json.loads(result[5]) if result[5] else None,
                    'has_file': bool(result[6]),
                    'file_name': result[7],
                    'file_type': result[8],
                    'file_size': result[9],
                    'created_at': result[10].isoformat() if result[10] else None,
                    'updated_at': result[11].isoformat() if result[11] else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    def _get_one(self, query: str, params: Dict = None):
        """Get a single row"""
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            return result.fetchone()
    
    async def update_document(self, document_id: int, update_data: DocumentUpdate):
        """Update a document"""
        try:
            updates = []
            params = {'id': document_id}
            
            if update_data.title is not None:
                updates.append("title = :title")
                params['title'] = update_data.title
            
            if update_data.content is not None:
                updates.append("content = :content")
                params['content'] = update_data.content
            
            if update_data.classification is not None:
                updates.append("classification = :classification")
                params['classification'] = update_data.classification
            
            if update_data.entities is not None:
                updates.append("entities = :entities")
                params['entities'] = json.dumps(update_data.entities)
            
            if update_data.metadata is not None:
                updates.append("metadata = :metadata")
                params['metadata'] = json.dumps(update_data.metadata)
            
            updates.append("updated_at = GETDATE()")
            
            query = f"""
            UPDATE documents
            SET {', '.join(updates)}
            WHERE id = :id AND is_active = 1
            """
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._execute_query(query, params)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return False
    
    async def delete_document(self, document_id: int):
        """Delete a document (soft delete)"""
        try:
            query = """
            UPDATE documents
            SET is_active = 0, updated_at = GETDATE()
            WHERE id = :id
            """
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._execute_query(query, {'id': document_id})
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    async def get_database_stats(self):
        """Get database statistics"""
        try:
            stats_query = """
            SELECT 
                COUNT(*) as total_documents,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_documents,
                SUM(CASE WHEN file_data IS NOT NULL THEN 1 ELSE 0 END) as documents_with_files,
                AVG(LEN(content)) as avg_content_length,
                MAX(created_at) as last_document_created
            FROM documents
            """
            
            classification_query = """
            SELECT 
                ISNULL(classification, 'Unclassified') as classification,
                COUNT(*) as count
            FROM documents
            WHERE is_active = 1
            GROUP BY classification
            ORDER BY count DESC
            """
            
            loop = asyncio.get_event_loop()
            
            stats_result = await loop.run_in_executor(
                None,
                lambda: self._get_one(stats_query)
            )
            
            class_result = await loop.run_in_executor(
                None,
                lambda: self._get_all(classification_query)
            )
            
            stats = {
                'total_documents': stats_result[0] if stats_result else 0,
                'active_documents': stats_result[1] if stats_result else 0,
                'documents_with_files': stats_result[2] if stats_result else 0,
                'avg_content_length': int(stats_result[3]) if stats_result and stats_result[3] else 0,
                'last_document_created': stats_result[4].isoformat() if stats_result and stats_result[4] else None
            }
            
            classification_breakdown = [
                {'classification': row[0], 'count': row[1]}
                for row in class_result
            ]
            
            return {
                "statistics": stats,
                "classification_breakdown": classification_breakdown
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "statistics": {},
                "classification_breakdown": []
            }
    
    async def get_document_file(self, document_id: int):
        """Get document file data"""
        try:
            query = """
            SELECT file_data, file_name, file_type
            FROM documents
            WHERE id = :id AND is_active = 1 AND file_data IS NOT NULL
            """
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._get_one(query, {'id': document_id})
            )
            
            if result and result[0]:
                return {
                    'data': result[0],
                    'name': result[1],
                    'type': result[2]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            return None
