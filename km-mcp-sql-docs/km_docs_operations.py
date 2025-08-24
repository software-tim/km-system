#!/usr/bin/env python3
"""
Document Operations - USING CORRECT COLUMN NAMES
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
        """Database already exists - just check connection"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 1 id FROM documents")
            cursor.fetchone()
            cursor.close()
            conn.close()
            logger.info("Connected to existing database")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
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

            # Insert document with CORRECT columns
            cursor.execute("""
                INSERT INTO documents (
                    title, content, classification, entities, metadata,
                    file_data, file_name, file_type, file_size, status, user_id
                )
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.title,
                document.content,
                document.classification,
                entities_json,
                metadata_json,
                document.file_data,
                document.file_name,
                document.file_type,
                document.file_size,
                1,  # status = 1 (active)
                'km-docs-api'  # user_id
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
        """Search documents using CORRECT columns"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

            # Build query using 'status' column (not is_active)
            where_clauses = []
            params = []

            # Filter by active status
            where_clauses.append("status = 1")

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
        """Get database statistics using CORRECT column names"""
        logger.info("get_database_stats called - using 'status' column")

        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

            # Count using 'status' column (not is_active)
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as active
                FROM documents
            """)
            result = cursor.fetchone()
            total_count = result[0] if result else 0
            active_count = result[1] if result else 0

            logger.info(f"Stats: total={total_count}, active={active_count}")

            # Get classification breakdown for active documents
            cursor.execute("""
                SELECT
                    COALESCE(classification, 'unclassified') as class_name,
                    COUNT(*) as class_count
                FROM documents
                WHERE status = 1
                GROUP BY classification
                ORDER BY COUNT(*) DESC
            """)

            breakdown = []
            for row in cursor.fetchall():
                breakdown.append({
                    "classification": row[0],
                    "count": row[1]
                })

            cursor.close()
            conn.close()

            response = {
                "statistics": {
                    "total_documents": total_count,
                    "active_documents": active_count
                },
                "classification_breakdown": breakdown
            }

            logger.info(f"Returning stats: total={total_count}, active={active_count}")
            return response

        except Exception as e:
            logger.error(f"Stats error: {str(e)}")
            return {
                "statistics": {
                    "total_documents": 0,
                    "active_documents": 0,
                    "error": str(e)
                },
                "classification_breakdown": []
            }

    async def get_document(self, document_id: int):
        """Get a single document by ID"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM documents WHERE id = ? AND status = 1", document_id)
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
        """Update document with new data including metadata"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            # Build dynamic update query based on provided fields
            update_fields = []
            params = []
            
            if update_data.title is not None:
                update_fields.append("title = ?")
                params.append(update_data.title)
                
            if update_data.content is not None:
                update_fields.append("content = ?")
                params.append(update_data.content)
                
            if update_data.classification is not None:
                update_fields.append("classification = ?")
                params.append(update_data.classification)
                
            if update_data.entities is not None:
                update_fields.append("entities = ?")
                params.append(json.dumps(update_data.entities))
                
            if update_data.metadata is not None:
                update_fields.append("metadata = ?")
                params.append(json.dumps(update_data.metadata))
            
            # Always update updated_at
            update_fields.append("updated_at = GETDATE()")
            
            # Add document_id as last parameter
            params.append(document_id)
            
            if update_fields:
                query = f"UPDATE documents SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                rows_affected = cursor.rowcount
                cursor.close()
                conn.close()
                
                return rows_affected > 0
            else:
                cursor.close()
                conn.close()
                return False
                
        except Exception as e:
            logger.error(f"Update document failed: {e}")
            return False

    async def delete_document(self, document_id: int):
        return True

    async def get_document_file(self, document_id: int):
        return None
