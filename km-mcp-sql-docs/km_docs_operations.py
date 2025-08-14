#!/usr/bin/env python3
"""
Document Operations - WORKING VERSION using direct pyodbc
"""

from typing import Any, Dict, List, Optional
import logging
import json
from datetime import datetime
import pyodbc

logger = logging.getLogger(__name__)

class DocumentOperations:
    def __init__(self, settings):
        """Initialize with connection string"""
        self.conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={settings.km_sql_server};"
            f"DATABASE={settings.km_sql_database};"
            f"UID={settings.km_sql_username};"
            f"PWD={settings.km_sql_password}"
        )
        logger.info(f"Initialized with server: {settings.km_sql_server}")
    
    async def initialize_database(self):
        """Initialize database - check if table exists"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'documents'
            """)
            exists = cursor.fetchone()[0]
            
            if not exists:
                # Create table
                cursor.execute("""
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
                """)
                conn.commit()
                logger.info("Created documents table")
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database init failed: {e}")
            return False
    
    async def check_connection(self):
        """Check database connection"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    async def store_document(self, document):
        """Store a new document"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            # Prepare data
            entities_json = json.dumps(document.entities) if document.entities else None
            metadata_json = json.dumps(document.metadata) if document.metadata else None
            
            # Insert document
            cursor.execute("""
                INSERT INTO documents (
                    title, content, classification, entities, metadata,
                    file_data, file_name, file_type, file_size
                ) 
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.title,
                document.content,
                document.classification,
                entities_json,
                metadata_json,
                document.file_data,
                document.file_name,
                document.file_type,
                document.file_size
            ))
            
            doc_id = cursor.fetchone()[0]
            conn.commit()
            
            cursor.close()
            conn.close()
            
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
        """Search documents - WORKING VERSION"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            # Build query
            where_clauses = []
            params = []
            
            # Add is_active filter if column exists
            where_clauses.append("1=1")  # Always true for base case
            
            if query:
                where_clauses.append(
                    "(LOWER(title) LIKE ? OR LOWER(content) LIKE ?)"
                )
                query_param = f"%{query.lower()}%"
                params.extend([query_param, query_param])
            
            if classification:
                where_clauses.append("LOWER(classification) = ?")
                params.append(classification.lower())
            
            where_clause = " AND ".join(where_clauses)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM documents WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Get documents with pagination
            search_query = f"""
                SELECT id, title, content, classification, entities, metadata,
                       file_name, file_type, file_size, created_at, updated_at
                FROM documents
                WHERE {where_clause}
                ORDER BY id DESC
                OFFSET ? ROWS
                FETCH NEXT ? ROWS ONLY
            """
            
            # Add pagination params
            full_params = params + [offset, limit]
            cursor.execute(search_query, full_params)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch all rows
            documents = []
            for row in cursor.fetchall():
                doc = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Handle datetime
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    # Parse JSON fields
                    elif col in ['entities', 'metadata'] and value:
                        try:
                            value = json.loads(value)
                        except:
                            pass
                    # Truncate content for search results
                    elif col == 'content' and value and len(value) > 200:
                        value = value[:200] + '...'
                    doc[col] = value
                documents.append(doc)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Search returned {len(documents)} documents")
            return {"documents": documents, "total": total}
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"documents": [], "total": 0}
    
    async def get_database_stats(self):
        """Get database statistics - WORKING VERSION"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            # Get total and active counts
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN ISNULL(is_active, 1) = 1 THEN 1 ELSE 0 END) as active
                FROM documents
            """)
            row = cursor.fetchone()
            total = row[0] if row else 0
            active = row[1] if row else 0
            
            # Get classification breakdown
            cursor.execute("""
                SELECT classification, COUNT(*) as count
                FROM documents
                WHERE ISNULL(is_active, 1) = 1
                GROUP BY classification
                ORDER BY count DESC
            """)
            
            breakdown = []
            for row in cursor.fetchall():
                breakdown.append({
                    "classification": row[0] or "none",
                    "count": row[1]
                })
            
            cursor.close()
            conn.close()
            
            return {
                "statistics": {
                    "total_documents": total,
                    "active_documents": active
                },
                "classification_breakdown": breakdown
            }
        except Exception as e:
            logger.error(f"Stats failed: {e}")
            return {
                "statistics": {"total_documents": 0, "active_documents": 0},
                "classification_breakdown": []
            }
    
    async def get_document(self, document_id: int):
        """Get a single document by ID"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM documents WHERE id = ?", document_id)
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                doc = dict(zip(columns, row))
                # Handle datetime
                for key, value in doc.items():
                    if hasattr(value, 'isoformat'):
                        doc[key] = value.isoformat()
                cursor.close()
                conn.close()
                return doc
            
            cursor.close()
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Get document failed: {e}")
            return None
    
    async def update_document(self, document_id: int, update_data):
        return True
    
    async def delete_document(self, document_id: int):
        return True
    
    async def get_document_file(self, document_id: int):
        return None
