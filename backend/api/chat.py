from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from pydantic import BaseModel

from core.logger import get_logger
from core.config import get_settings

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])
settings = get_settings()


class ChatQuery(BaseModel):
    """Chat query request."""
    question: str
    top_k: int = 5
    include_sources: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "¿Cuál es el valor promedio de transacciones en Bogotá?",
                "top_k": 5,
                "include_sources": True
            }
        }


class ChatResponse(BaseModel):
    """Chat response."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    processing_time_ms: float


@router.post("/query", response_model=ChatResponse)
async def chat_query(query: ChatQuery) -> ChatResponse:
    """
    Natural language query interface for real estate data.
    
    Uses RAG (Retrieval Augmented Generation) to answer questions about transactions.
    """
    try:
        logger.info("chat_query_received", question=query.question)
        
        # TODO: Integrate with RAG service
        # For now, return mock response
        
        answer = generate_mock_answer(query.question)
        
        return ChatResponse(
            answer=answer,
            sources=[
                {
                    "type": "transaction_aggregate",
                    "content": "Estadísticas de transacciones en Bogotá",
                    "relevance": 0.92
                }
            ],
            confidence=0.85,
            processing_time_ms=450.5
        )
        
    except Exception as e:
        logger.error("chat_query_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/suggestions")
async def get_query_suggestions() -> List[str]:
    """Get suggested queries for the chat interface."""
    return [
        "¿Cuál es el valor promedio de transacciones en Bogotá?",
        "Muestra las transacciones de alto riesgo del último mes",
        "¿Cuántas transacciones sospechosas hay en Antioquia?",
        "¿Cuál es el tipo de acto más común?",
        "Compara los valores entre departamentos",
        "¿Qué municipios tienen mayor tasa de anomalías?"
    ]


def generate_mock_answer(question: str) -> str:
    """Generate mock answer based on question keywords."""
    question_lower = question.lower()
    
    if "promedio" in question_lower or "valor" in question_lower:
        return """
        Basado en el análisis de las transacciones registradas:
        
        - **Valor promedio en Bogotá**: $285,450,000 COP
        - **Rango de valores**: $45,000,000 - $2,500,000,000 COP
        - **Transacciones analizadas**: 34,521 registros
        
        El valor promedio ha aumentado un 12.5% en el último año.
        """
    
    elif "riesgo" in question_lower or "sospechosa" in question_lower:
        return """
        Resumen de transacciones de alto riesgo:
        
        - **Total identificadas**: 1,247 transacciones
        - **Porcentaje**: 3.6% del total
        - **Principales causas**:
          - Valor atípico (45%)
          - Múltiples intervinientes (28%)
          - Datos incompletos (15%)
          - Patrones temporales inusuales (12%)
        
        Se recomienda revisión manual de casos con score > 0.8
        """
    
    else:
        return """
        He analizado tu pregunta sobre el dataset inmobiliario. 
        
        Tengo acceso a información sobre:
        - 34M+ transacciones registradas
        - Cobertura nacional (32 departamentos)
        - Período: 2015-2024
        
        ¿Podrías ser más específico sobre qué información necesitas?
        """
