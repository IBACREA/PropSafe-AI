from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class TipoActo(str, Enum):
    """Tipos de actos registrales en Colombia."""
    COMPRAVENTA = "compraventa"
    HIPOTECA = "hipoteca"
    DONACION = "donacion"
    PERMUTA = "permuta"
    DACION_PAGO = "dacion_pago"
    ADJUDICACION = "adjudicacion"
    SUCESION = "sucesion"
    OTRO = "otro"


class TipoPredio(str, Enum):
    """Tipos de predio."""
    URBANO = "urbano"
    RURAL = "rural"
    MIXTO = "mixto"


class EstadoFolio(str, Enum):
    """Estados del folio de matrícula."""
    ACTIVO = "activo"
    CANCELADO = "cancelado"
    CERRADO = "cerrado"
    SUSPENDIDO = "suspendido"


class RiskLevel(str, Enum):
    """Niveles de riesgo de la transacción."""
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high-risk"


class TransactionInput(BaseModel):
    """Schema para una transacción inmobiliaria individual."""
    
    valor_acto: float = Field(..., description="Valor del acto en pesos colombianos", gt=0)
    tipo_acto: TipoActo = Field(..., description="Tipo de acto registral")
    fecha_acto: datetime = Field(..., description="Fecha del acto")
    departamento: str = Field(..., description="Departamento de Colombia", min_length=2)
    municipio: str = Field(..., description="Municipio", min_length=2)
    tipo_predio: TipoPredio = Field(..., description="Tipo de predio")
    numero_intervinientes: int = Field(..., description="Número de intervinientes", ge=1)
    estado_folio: EstadoFolio = Field(..., description="Estado del folio de matrícula")
    numero_catastral: Optional[str] = Field(None, description="Número catastral del predio")
    matricula_inmobiliaria: Optional[str] = Field(None, description="Matrícula inmobiliaria")
    area_terreno: Optional[float] = Field(None, description="Área del terreno en m2", gt=0)
    area_construida: Optional[float] = Field(None, description="Área construida en m2", gt=0)
    
    @validator("departamento", "municipio")
    def normalize_text(cls, v):
        """Normalize text fields."""
        return v.strip().upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "valor_acto": 250000000,
                "tipo_acto": "compraventa",
                "fecha_acto": "2024-01-15T10:30:00",
                "departamento": "CUNDINAMARCA",
                "municipio": "BOGOTA",
                "tipo_predio": "urbano",
                "numero_intervinientes": 2,
                "estado_folio": "activo",
                "numero_catastral": "AAA0000000000000000000000000",
                "matricula_inmobiliaria": "50C-1234567",
                "area_terreno": 120.5,
                "area_construida": 85.3
            }
        }


class ContributingFeature(BaseModel):
    """Feature que contribuye a la anomalía."""
    feature_name: str
    value: Any
    contribution_score: float
    explanation: str


class AnomalyAnalysisResult(BaseModel):
    """Resultado del análisis de anomalías."""
    
    anomaly_score: float = Field(..., description="Score de anomalía (0-1)", ge=0, le=1)
    classification: RiskLevel = Field(..., description="Clasificación de riesgo")
    contributing_features: List[ContributingFeature] = Field(
        ..., 
        description="Top 5 features que contribuyen a la anomalía"
    )
    confidence: float = Field(..., description="Confianza del modelo", ge=0, le=1)
    explanation: str = Field(..., description="Explicación en lenguaje natural")
    recommendations: List[str] = Field(default_factory=list, description="Recomendaciones")
    
    class Config:
        json_schema_extra = {
            "example": {
                "anomaly_score": 0.85,
                "classification": "high-risk",
                "contributing_features": [
                    {
                        "feature_name": "valor_acto",
                        "value": 50000000,
                        "contribution_score": 0.45,
                        "explanation": "Valor significativamente inferior al promedio del mercado"
                    }
                ],
                "confidence": 0.92,
                "explanation": "Transacción con riesgo alto debido a valor atípico y múltiples intervinientes",
                "recommendations": [
                    "Verificar avalúo catastral",
                    "Validar identidad de intervinientes"
                ]
            }
        }


class TransactionAnalysisResponse(BaseModel):
    """Respuesta del análisis de una transacción."""
    
    transaction_id: Optional[str] = None
    result: AnomalyAnalysisResult
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchAnalysisRequest(BaseModel):
    """Request para análisis en lote."""
    
    file_format: str = Field(..., description="Formato del archivo: csv o parquet")
    analyze_all: bool = Field(True, description="Analizar todas las filas")
    limit: Optional[int] = Field(None, description="Límite de filas a procesar", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_format": "csv",
                "analyze_all": True,
                "limit": 10000
            }
        }


class BatchAnalysisStats(BaseModel):
    """Estadísticas del análisis en lote."""
    
    total_transactions: int
    normal_count: int
    suspicious_count: int
    high_risk_count: int
    average_score: float
    processing_time_seconds: float


class BatchAnalysisResponse(BaseModel):
    """Respuesta del análisis en lote."""
    
    stats: BatchAnalysisStats
    high_risk_transactions: List[Dict[str, Any]] = Field(
        ..., 
        description="Transacciones de alto riesgo con detalles"
    )
    report_url: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]
