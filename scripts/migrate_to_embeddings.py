"""
Migration script to add embeddings to existing documents
Run this after creating the embedding tables
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from km_orchestrator.embedding_manager import EmbeddingManager
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def migrate_embeddings():
    """Migrate existing documents to include embeddings"""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    connection_string = os.getenv("SQL_CONNECTION_STRING")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not connection_string or not openai_api_key:
        logger.error("Missing required environment variables: SQL_CONNECTION_STRING or OPENAI_API_KEY")
        return
    
    logger.info("Starting embedding migration...")
    
    try:
        # Initialize embedding manager
        manager = EmbeddingManager(connection_string, openai_api_key)
        
        # Process all existing documents
        await manager.process_all_existing_documents()
        
        # Process knowledge graph nodes
        logger.info("Processing knowledge graph nodes...")
        conn = manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, label, properties
            FROM knowledge_graph_nodes
        """)
        
        nodes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for node_id, label, properties in nodes:
            logger.info(f"Processing node: {node_id} - {label}")
            await manager.process_knowledge_node(node_id, label)
            await asyncio.sleep(0.1)  # Rate limiting
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_embeddings())