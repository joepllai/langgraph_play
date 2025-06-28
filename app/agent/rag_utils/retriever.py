from langchain_postgres import PGVector
from app.config.agent import PGVectorConfig
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import asyncio
from typing import List, Optional
from langchain_core.documents import Document
import hashlib
import json
import sqlalchemy as sa
from sqlalchemy import text

print("Initializing FHIR API docs store...", PGVectorConfig.PSQL_CONNECTION)

class AsyncRetrieverWrapper:
    def __init__(self, retriever):
        self.retriever = retriever

    async def ainvoke(self, query, config=None):
        loop = asyncio.get_event_loop()
        # Run the sync invoke in a thread pool to avoid blocking
        return await loop.run_in_executor(None, self.retriever.invoke, query, config)

    def invoke(self, query, config=None):
        return self.retriever.invoke(query, config)


class IdempotentPGVector(PGVector):
    """
    Enhanced PGVector with proper database-based duplicate detection and upsert functionality.
    Uses PostgreSQL's ON CONFLICT for true idempotency.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ensure_document_hash_table()
    
    def _ensure_document_hash_table(self):
        """Ensure the document hash table exists for duplicate tracking."""
        try:
            # Use the connection string to create a direct connection
            import psycopg2
            from urllib.parse import urlparse
            
            # Parse the connection string
            parsed = urlparse(PGVectorConfig.PSQL_CONNECTION.replace('postgresql+psycopg://', 'postgresql://'))
            
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password
            )
            
            with conn.cursor() as cursor:
                # Create a table to track document hashes
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS document_hashes (
                    id SERIAL PRIMARY KEY,
                    document_hash VARCHAR(32) UNIQUE NOT NULL,
                    url VARCHAR(500),
                    title VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                cursor.execute(create_table_sql)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_hashes_hash ON document_hashes(document_hash);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_hashes_url ON document_hashes(url);")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not create document hash table: {e}")
    
    def _get_db_connection(self):
        """Get a database connection for direct SQL operations."""
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse the connection string
        parsed = urlparse(PGVectorConfig.PSQL_CONNECTION.replace('postgresql+psycopg://', 'postgresql://'))
        
        return psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
    
    def _generate_document_hash(self, document: Document) -> str:
        """
        Generate a hash for a document based on content and metadata.
        This helps identify duplicates.
        """
        # Create a hash based on content and key metadata
        content = document.page_content
        metadata_str = json.dumps({
            k: v for k, v in document.metadata.items() 
            if k in ['url', 'title', 'path', 'method', 'section', 'name']
        }, sort_keys=True)
        
        hash_input = f"{content}|{metadata_str}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _check_document_exists(self, document_hash: str) -> bool:
        """Check if a document hash already exists in the database."""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM document_hashes WHERE document_hash = %s",
                    (document_hash,)
                )
                result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            print(f"Error checking document existence: {e}")
            return False
    
    def _mark_document_added(self, document_hash: str, document: Document):
        """Mark a document as added in the hash tracking table."""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO document_hashes (document_hash, url, title) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (document_hash) DO NOTHING
                    """,
                    (
                        document_hash,
                        document.metadata.get('url', ''),
                        document.metadata.get('title', '')
                    )
                )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error marking document as added: {e}")
    
    def add_documents_idempotent(
        self, 
        documents: List[Document], 
        check_duplicates: bool = True
    ) -> List[str]:
        """
        Add documents to the vector store with proper database-based duplicate detection.
        
        Args:
            documents: List of documents to add
            check_duplicates: Whether to check for duplicates before adding
            
        Returns:
            List of document hashes that were actually added (not duplicates)
        """
        if not check_duplicates:
            return self.add_documents(documents)
        
        # Filter out duplicates using database checks
        unique_documents = []
        added_hashes = []
        
        for doc in documents:
            doc_hash = self._generate_document_hash(doc)
            
            if not self._check_document_exists(doc_hash):
                unique_documents.append(doc)
                added_hashes.append(doc_hash)
                print(f"New document: {doc.metadata.get('url', 'Unknown URL')}")
            else:
                print(f"Skipping duplicate document: {doc.metadata.get('url', 'Unknown URL')}")
        
        if unique_documents:
            # Add only unique documents to the vector store
            self.add_documents(unique_documents)
            
            # Mark documents as added in the tracking table
            for doc, doc_hash in zip(unique_documents, added_hashes):
                self._mark_document_added(doc_hash, doc)
            
            print(f"Added {len(unique_documents)} unique documents, skipped {len(documents) - len(unique_documents)} duplicates")
        else:
            print("All documents were duplicates, nothing added")
        
        return added_hashes
    
    def get_document_stats(self) -> dict:
        """Get statistics about documents in the vector store."""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cursor:
                # Count total documents in vector store
                cursor.execute(f"SELECT COUNT(*) FROM {self.collection_name}")
                vector_result = cursor.fetchone()
                vector_count = vector_result[0] if vector_result else 0
                
                # Count unique document hashes
                cursor.execute("SELECT COUNT(*) FROM document_hashes")
                hash_result = cursor.fetchone()
                hash_count = hash_result[0] if hash_result else 0
            
            conn.close()
            return {
                "total_documents": vector_count,
                "unique_documents": hash_count,
                "duplicate_documents": vector_count - hash_count
            }
        except Exception as e:
            print(f"Error getting document stats: {e}")
            return {"error": str(e)}
    
    def cleanup_duplicates(self) -> int:
        """
        Remove duplicate documents from the vector store.
        This is a more expensive operation that requires careful handling.
        
        Returns:
            Number of duplicate documents removed
        """
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cursor:
                # This is a complex operation that would require:
                # 1. Finding documents with same content
                # 2. Keeping only one copy
                # 3. Updating references
                
                # For now, just return 0 as this requires careful implementation
                print("Cleanup duplicates not implemented yet - requires careful handling")
            conn.close()
            return 0
        except Exception as e:
            print(f"Error cleaning up duplicates: {e}")
            return 0


embeddings = GoogleGenerativeAIEmbeddings(
    model=PGVectorConfig.FHIRAPIDocs.EMBEDDINGS_MODEL
)

# Use the enhanced PGVector with proper database-based duplicate detection
fhir_api_docs_store = IdempotentPGVector(
    embeddings=embeddings,
    connection=PGVectorConfig.PSQL_CONNECTION,
    collection_name=PGVectorConfig.FHIRAPIDocs.COLLECTION_NAME,
    use_jsonb=PGVectorConfig.FHIRAPIDocs.USE_JSONB,
)

fhir_api_docs_retriever = fhir_api_docs_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.1, "k": 10},
)

fhir_api_docs_retriever = AsyncRetrieverWrapper(fhir_api_docs_retriever)
