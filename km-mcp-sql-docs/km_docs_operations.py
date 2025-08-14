#!/usr/bin/env python3
"""
Document Operations module using SQLAlchemy for Azure SQL Database
"""

from typing import Any, Dict, List, Optional
import logging
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from km_docs_config import Settings

logger = logging.getLogger(__name__)


class DocumentOperations:
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Build connection string
        connection_string = settings.get_connection_string()
        
        # Create engine with proper settings
        self.engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=settings.debug,
            pool_recycle=3600
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
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text(create_table_query))
                conn.commit()
            logger.info("Documents table initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    async def check_connection(self):
        """Check database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                result.fetchone()
            return True
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    async def store_document(self, document):
        """Store a new document"""
        try:
            # Prepare data
            entities_json = json.dumps(document.entities) if document.entities else None
            metadata_json = json.dumps(document.metadata) if document.metadata else None
            
            query = text("""
            INSERT INTO documents (
                title, content, classification, entities, metadata,
                file_data, file_name, file_type, file_size
            ) 
            OUTPUT INSERTED.id
            VALUES (
                :title, :content, :classification, :entities, :metadata,
                :file_data, :file_name, :file_type, :file_size
            )
            """)
            
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
            
            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                document_id = result.fetchone()[0]
                conn.commit()
            
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
            search_query = text(f"""
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
            """)
            
            with self.engine.connect() as conn:
                # Get count
                count_result = conn.execute(text(count_query), params)
                total = count_result.fetchone()[0]
                
                # Get documents
                docs_result = conn.execute(search_query, params)
                rows = docs_result.fetchall()
            
            # Process results
            documents = []
            for row in rows:
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
                "total": total
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"documents": [], "total": 0}
    
    async def get_database_stats(self):
        """Get database statistics"""
        try:
            stats_query = text("""
            SELECT 
                COUNT(*) as total_documents,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_documents
            FROM documents
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(stats_query)
                row = result.fetchone()
            
            return {
                "statistics": {
                    "total_documents": row[0] if row else 0,
                    "active_documents": row[1] if row else 0
                },
                "classification_breakdown": []
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "statistics": {},
                "classification_breakdown": []
            }
    
    # Implement other methods as needed...
    async def get_document(self, document_id: int):
        return None
    
    async def update_document(self, document_id: int, update_data):
        return True
    
    async def delete_document(self, document_id: int):
        return True
    
    async def get_document_file(self, document_id: int):
        return None
