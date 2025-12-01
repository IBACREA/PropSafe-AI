from typing import List, Dict, Any, Optional
import openai
from datetime import datetime

from core.logger import get_logger
from core.config import get_settings
from services.rag.vector_store import get_vector_store
from services.rag.embedder import get_embedder

logger = get_logger(__name__)
settings = get_settings()


class RAGPipeline:
    """
    RAG (Retrieval Augmented Generation) pipeline for question answering.
    
    Combines vector search with LLM generation for accurate, context-aware answers.
    """
    
    def __init__(self):
        """Initialize RAG pipeline."""
        self.vector_store = get_vector_store()
        self.embedder = get_embedder()
        
        # Configure OpenAI (if available)
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.llm_available = True
        else:
            logger.warning("openai_key_not_configured")
            self.llm_available = False
        
        logger.info("rag_pipeline_initialized")
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG.
        
        Args:
            question: User question
            top_k: Number of context documents to retrieve
            include_sources: Whether to include source documents in response
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            start_time = datetime.now()
            
            logger.info("rag_query_started", question=question[:100])
            
            # Step 1: Retrieve relevant documents
            retrieval_results = self.vector_store.query(
                query_text=question,
                n_results=top_k
            )
            
            documents = retrieval_results['documents']
            metadatas = retrieval_results['metadatas']
            distances = retrieval_results['distances']
            
            logger.info("documents_retrieved", n_docs=len(documents))
            
            # Step 2: Prepare context
            context = self._prepare_context(documents, metadatas)
            
            # Step 3: Generate answer
            if self.llm_available:
                answer = self._generate_answer(question, context)
                confidence = self._calculate_confidence(distances)
            else:
                answer = self._generate_fallback_answer(question, documents)
                confidence = 0.5
            
            # Prepare sources
            sources = []
            if include_sources:
                sources = self._prepare_sources(documents, metadatas, distances)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                'answer': answer,
                'sources': sources,
                'confidence': confidence,
                'processing_time_ms': processing_time,
                'retrieved_docs': len(documents)
            }
            
            logger.info(
                "rag_query_completed",
                confidence=confidence,
                processing_time_ms=processing_time
            )
            
            return result
            
        except Exception as e:
            logger.error("rag_query_error", error=str(e))
            raise
    
    def _prepare_context(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> str:
        """Prepare context string from retrieved documents."""
        context_parts = []
        
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            context_parts.append(f"[Documento {i+1}]")
            if meta:
                context_parts.append(f"Metadata: {meta}")
            context_parts.append(doc)
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM."""
        try:
            prompt = self._create_prompt(question, context)
            
            response = openai.ChatCompletion.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente experto en análisis de transacciones inmobiliarias en Colombia. Responde de manera precisa y concisa basándote únicamente en el contexto proporcionado."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
            
        except Exception as e:
            logger.error("llm_generation_error", error=str(e))
            return self._generate_fallback_answer(question, [context])
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create prompt for LLM."""
        return f"""Contexto:
{context}

Pregunta: {question}

Basándote únicamente en el contexto anterior, proporciona una respuesta clara y concisa. Si el contexto no contiene información suficiente, indícalo."""
    
    def _generate_fallback_answer(
        self,
        question: str,
        documents: List[str]
    ) -> str:
        """Generate fallback answer when LLM is not available."""
        if not documents:
            return "No se encontró información relevante para responder tu pregunta."
        
        # Simple keyword-based response
        return f"""He encontrado {len(documents)} documentos relacionados con tu pregunta.

Para obtener respuestas más detalladas, configura la API de OpenAI en las variables de entorno.

Documentos encontrados:
{documents[0][:500]}..."""
    
    def _calculate_confidence(self, distances: List[float]) -> float:
        """Calculate confidence score based on retrieval distances."""
        if not distances:
            return 0.0
        
        # Convert distances to similarity scores
        # Lower distance = higher confidence
        avg_distance = sum(distances) / len(distances)
        
        # Normalize to 0-1 range (assuming max distance of 2.0)
        confidence = max(0.0, min(1.0, 1.0 - (avg_distance / 2.0)))
        
        return confidence
    
    def _prepare_sources(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        distances: List[float]
    ) -> List[Dict[str, Any]]:
        """Prepare source information for response."""
        sources = []
        
        for doc, meta, dist in zip(documents, metadatas, distances):
            source = {
                'content': doc[:200] + "..." if len(doc) > 200 else doc,
                'metadata': meta,
                'relevance_score': 1.0 - (dist / 2.0)  # Convert distance to score
            }
            sources.append(source)
        
        return sources
    
    def index_document(
        self,
        document: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Index a new document into the vector store.
        
        Args:
            document: Document text
            metadata: Optional metadata
            
        Returns:
            Document ID
        """
        doc_ids = self.vector_store.add_documents(
            documents=[document],
            metadatas=[metadata] if metadata else None
        )
        
        logger.info("document_indexed", doc_id=doc_ids[0])
        return doc_ids[0]
    
    def index_batch(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Index multiple documents.
        
        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            
        Returns:
            List of document IDs
        """
        doc_ids = self.vector_store.add_documents(
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info("batch_indexed", n_docs=len(doc_ids))
        return doc_ids


# Global RAG instance
_rag_instance = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create global RAG pipeline instance."""
    global _rag_instance
    
    if _rag_instance is None:
        _rag_instance = RAGPipeline()
    
    return _rag_instance
