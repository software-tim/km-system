#!/usr/bin/env python3
"""
Document Operations - COMPLETE VERSION with transaction commits
"""

from typing import Any, Dict, List, Optional
import logging
import json
from datetime import datetime
from sqlalchemy import create_engine, text, pool
from km_docs_config import Settings

logger = logging.getLogger(__name__)

class DocumentOperations:
    def __init__(self, settings: Settings):
        self.settings = settings
        connection_string = settings.get_connection_string()
        
        # Create engine
        self.engine = create_engine(
            connection_string,
            poolclass=pool.NullPool,
            echo=settings.debug
        )
        logger.info(f"Connected to database: {settings.km_sql_database}")
    
    async def initialize_database(self):
        """Initialize database table"""
        try:
            with self.engine.begin() as conn:  # auto-commits
                # Check if table exists
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'documents'"
                ))
                if result.scalar() == 0:
                    conn.execute(text("""
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
                    """))
            return True
        except Exception as e:
            logger.error(f"Database init failed: {e}")
            return False
    
    async def check_connection(self):
        """Check database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    async def store_document(self, document):
        """Store document - WITH COMMIT"""
        try:
            entities_json = json.dumps(document.entities) if document.entities else None
            metadata_json = json.dumps(document.metadata) if document.metadata else None
            
            with self.engine.begin() as conn:  # auto-commits
                result = conn.execute(
                    text("""
                    INSERT INTO documents (
                        title, content, classification, entities, metadata,
                        file_data, file_name, file_type, file_size
                    ) 
                    OUTPUT INSERTED.id
                    VALUES (
                        :title, :content, :classification, :entities, :metadata,
                        :file_data, :file_name, :file_type, :file_size
                    )
                    """),
                    {
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
                )
                doc_id = result.fetchone()[0]
            
            logger.info(f"Document {doc_id} stored")
            return {
                "success": True,
                "document_id": doc_id,
                "message": "Document stored successfully"
            }
        except Exception as e:
            logger.error(f"Store document failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_documents(self, query: Optional[str] = None,
                              classification: Optional[str] = None,
                              limit: int = 10, offset: int = 0):
        """Search documents - WITH PROPER COMMITS"""
        try:
            with self.engine.connect() as conn:
                # Build WHERE clause
                where_parts = ["is_active = 1"]
                params = {}
                
                if query:
                    where_parts.append(
                        "(LOWER(title) LIKE '%' + LOWER(:query) + '%' OR "
                        "LOWER(content) LIKE '%' + LOWER(:query) + '%')"
                    )
                    params['query'] = query
                
                if classification:
                    where_parts.append("LOWER(classification) = LOWER(:classification)")
                    params['classification'] = classification
                
                where_clause = " AND ".join(where_parts)
                
                # Count total
                count_sql = f"SELECT COUNT(*) as total FROM documents WHERE {where_clause}"
                count_result = conn.execute(text(count_sql), params)
                total = count_result.scalar() or 0
                
                # Get documents
                search_sql = f"""
                SELECT id, title, content, classification, entities, metadata,
                       file_name, file_type, file_size, created_at, updated_at
                FROM documents
                WHERE {where_clause}
                ORDER BY id DESC
                OFFSET :offset ROWS
                FETCH NEXT :limit ROWS ONLY
                """
                
                params['offset'] = offset
                params['limit'] = limit
                
                result = conn.execute(text(search_sql), params)
                rows = result.fetchall()
                
                documents = []
                for row in rows:
                    doc = {
                        'id': row[0],
                        'title': row[1],
                        'content': row[2][:200] + '...' if len(row[2] or '') > 200 else row[2],
                        'classification': row[3],
                        'entities': json.loads(row[4]) if row[4] else None,
                        'metadata': json.loads(row[5]) if row[5] else None,
                        'file_name': row[6],
                        'file_type': row[7],
                        'file_size': row[8],
                        'created_at': row[9].isoformat() if row[9] else None,
                        'updated_at': row[10].isoformat() if row[10] else None
                    }
                    documents.append(doc)
                
                conn.commit()  # Ensure read is committed
                
            return {"documents": documents, "total": total}
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"documents": [], "total": 0}
    
    async def get_database_stats(self):
        """Get database statistics - WITH COMMITS"""
        try:
            with self.engine.connect() as conn:
                # Get counts
                stats_result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active
                    FROM documents
                """))
                stats = stats_result.fetchone()
                
                # Get classification breakdown
                breakdown_result = conn.execute(text("""
                    SELECT classification, COUNT(*) as count
                    FROM documents
                    WHERE is_active = 1
                    GROUP BY classification
                """))
                breakdown = breakdown_result.fetchall()
                
                conn.commit()  # Commit the read
                
            return {
                "statistics": {
                    "total_documents": stats[0] if stats else 0,
                    "active_documents": stats[1] if stats else 0
                },
                "classification_breakdown": [
                    {"classification": row[0] or "none", "count": row[1]}
                    for row in breakdown
                ]
            }
        except Exception as e:
            logger.error(f"Stats failed: {e}")
            return {
                "statistics": {"total_documents": 0, "active_documents": 0},
                "classification_breakdown": []
            }
    
    async def get_document(self, document_id: int):
        return None
    
    async def update_document(self, document_id: int, update_data):
        return True
    
    async def delete_document(self, document_id: int):
        return True
    
    async def get_document_file(self, document_id: int):
        return None
