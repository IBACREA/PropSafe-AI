import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path

from core.logger import get_logger
from core.config import get_settings
from services.rag.embedder import get_embedder

logger = get_logger(__name__)
settings = get_settings()


class VectorStore:
    """
    Vector store for document retrieval using ChromaDB.
    
    Stores and retrieves document embeddings for RAG.
    """
    
    def __init__(
        self,
        collection_name: str = "real_estate_docs",
        persist_directory: str = None
    ):
        """
        Initialize vector store.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.vector_store_path
        
        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "initializing_vector_store",
            collection=collection_name,
            persist_dir=self.persist_directory
        )
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.Client(ChromaSettings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Real estate transaction documents"}
            )
            
            logger.info(
                "vector_store_initialized",
                collection=collection_name,
                doc_count=self.collection.count()
            )
            
        except Exception as e:
            logger.error("vector_store_init_error", error=str(e))
            raise
        
        # Get embedder
        self.embedder = get_embedder()
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for documents (generated if not provided)
            
        Returns:
            List of document IDs
        """
        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Generate embeddings
            logger.info("generating_embeddings", n_docs=len(documents))
            embeddings = self.embedder.embed_batch(documents)
            
            # Prepare metadatas
            if metadatas is None:
                metadatas = [{} for _ in documents]
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info("documents_added", n_docs=len(documents))
            return ids
            
        except Exception as e:
            logger.error("add_documents_error", error=str(e))
            raise
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.
        
        Args:
            query_text: Query text
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary with results including documents, distances, and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_text(query_text)
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where
            )
            
            logger.info(
                "query_executed",
                query=query_text[:50],
                n_results=len(results['documents'][0]) if results['documents'] else 0
            )
            
            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'ids': results['ids'][0] if results['ids'] else []
            }
            
        except Exception as e:
            logger.error("query_error", error=str(e))
            raise
    
    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        try:
            result = self.collection.get(ids=[doc_id])
            
            if result['documents']:
                return {
                    'id': doc_id,
                    'document': result['documents'][0],
                    'metadata': result['metadatas'][0] if result['metadatas'] else {}
                }
            return None
            
        except Exception as e:
            logger.error("get_by_id_error", error=str(e), doc_id=doc_id)
            return None
    
    def delete(self, ids: List[str]) -> None:
        """
        Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info("documents_deleted", n_docs=len(ids))
        except Exception as e:
            logger.error("delete_error", error=str(e))
            raise
    
    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()
    
    def clear(self) -> None:
        """Clear all documents from the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(self.collection_name)
            logger.info("collection_cleared")
        except Exception as e:
            logger.error("clear_error", error=str(e))
            raise


# Global vector store instance
_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global _vector_store_instance
    
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    
    return _vector_store_instance
