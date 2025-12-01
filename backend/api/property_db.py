"""
Property search API using PostgreSQL database
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

import sys
from pathlib import Path

# Add parent directory to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path.parent))

from backend.core.database import get_db
from backend.models.db_models import Transaction
from backend.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/property", tags=["property"])


class PropertySearchRequest(BaseModel):
    """Request para buscar propiedad por matrícula"""
    matricula: str = Field(..., min_length=1, max_length=50)


class PropertyTransaction(BaseModel):
    """Una transacción de la propiedad"""
    fecha: str
    tipo_acto: str
    valor: float
    departamento: str
    municipio: str
    tipo_predio: str
    count_intervinientes: int
    es_anomalo: bool
    anomaly_score: Optional[float] = None


class PropertySearchResponse(BaseModel):
    """Response de búsqueda de propiedad"""
    matricula: str
    encontrada: bool
    total_transacciones: int = 0
    historial: List[PropertyTransaction] = []
    precio_promedio: Optional[float] = None
    precio_ultima: Optional[float] = None
    tasa_anomalias: Optional[float] = None
    ubicacion: Optional[Dict[str, str]] = None
    alertas: List[str] = []
    score_riesgo: Optional[float] = None


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check con información de base de datos"""
    try:
        # Count total transactions
        total = db.query(func.count(Transaction.pk)).scalar()
        
        # Count with anomaly scores
        with_scores = db.query(func.count(Transaction.pk)).filter(
            Transaction.anomaly_score.isnot(None)
        ).scalar()
        
        return {
            "status": "ok",
            "database": "connected",
            "total_transactions": total,
            "transactions_with_scores": with_scores,
            "coverage": f"{(with_scores/total*100):.1f}%" if total > 0 else "0%"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }


@router.post("/search", response_model=PropertySearchResponse)
async def search_property(
    request: PropertySearchRequest,
    db: Session = Depends(get_db)
):
    """
    Busca una propiedad por matrícula en PostgreSQL
    
    Retorna historial completo de transacciones con:
    - Análisis de anomalías (si los modelos fueron entrenados)
    - Precios históricos
    - Alertas de riesgo
    """
    logger.info(f"🔍 Buscando matrícula: {request.matricula}")
    
    try:
        # Buscar transacciones en base de datos
        transactions = db.query(Transaction).filter(
            Transaction.matricula == request.matricula.upper()
        ).order_by(Transaction.fecha_radicacion.desc()).all()
        
        if not transactions:
            logger.info(f"  ❌ No se encontraron transacciones para {request.matricula}")
            return PropertySearchResponse(
                matricula=request.matricula,
                encontrada=False,
                alertas=["No se encontraron registros para esta matrícula en la base de datos."]
            )
        
        logger.info(f"  ✅ Encontradas {len(transactions)} transacciones")
        
        # Procesar transacciones
        historial = []
        valores = []
        anomalias = 0
        suma_scores = 0
        ubicacion = None
        
        for tx in transactions:
            # Determinar si es anomalía
            es_anomalo = tx.is_anomaly if tx.is_anomaly is not None else False
            anomaly_score = tx.anomaly_score if tx.anomaly_score is not None else None
            
            if es_anomalo:
                anomalias += 1
            
            if anomaly_score:
                suma_scores += anomaly_score
            
            # Capturar valores
            if tx.valor_acto and tx.valor_acto > 0:
                valores.append(tx.valor_acto)
            
            # Ubicación (primera transacción)
            if ubicacion is None and tx.departamento:
                ubicacion = {
                    "departamento": tx.departamento,
                    "municipio": tx.municipio or "N/A"
                }
            
            # Agregar al historial
            historial.append(PropertyTransaction(
                fecha=str(tx.fecha_radicacion) if tx.fecha_radicacion else "N/A",
                tipo_acto=tx.nombre_natujur or "N/A",
                valor=tx.valor_acto or 0,
                departamento=tx.departamento or "N/A",
                municipio=tx.municipio or "N/A",
                tipo_predio=tx.tipo_predio or "N/A",
                count_intervinientes=(tx.count_a or 0) + (tx.count_de or 0),
                es_anomalo=es_anomalo,
                anomaly_score=anomaly_score
            ))
        
        # Calcular métricas
        total_tx = len(transactions)
        precio_promedio = sum(valores) / len(valores) if valores else None
        precio_ultima = valores[0] if valores else None  # Ya ordenado desc
        tasa_anomalias = (anomalias / total_tx * 100) if total_tx > 0 else 0
        score_riesgo = (suma_scores / total_tx) if total_tx > 0 else None
        
        # Generar alertas
        alertas = _generar_alertas(
            total_tx=total_tx,
            tasa_anomalias=tasa_anomalias,
            precio_promedio=precio_promedio,
            score_riesgo=score_riesgo
        )
        
        return PropertySearchResponse(
            matricula=request.matricula,
            encontrada=True,
            total_transacciones=total_tx,
            historial=historial,
            precio_promedio=precio_promedio,
            precio_ultima=precio_ultima,
            tasa_anomalias=tasa_anomalias,
            ubicacion=ubicacion,
            alertas=alertas,
            score_riesgo=score_riesgo
        )
    
    except Exception as e:
        logger.error(f"Error buscando propiedad: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


def _generar_alertas(
    total_tx: int,
    tasa_anomalias: float,
    precio_promedio: Optional[float],
    score_riesgo: Optional[float]
) -> List[str]:
    """Genera alertas basadas en análisis"""
    alertas = []
    
    # Tasa de anomalías alta
    if tasa_anomalias > 50:
        alertas.append("ALERTA: Más del 50% de las transacciones presentan señales de anomalía.")
    elif tasa_anomalias > 25:
        alertas.append("ADVERTENCIA: Tasa elevada de transacciones anómalas detectadas.")
    
    # Score de riesgo alto
    if score_riesgo:
        if score_riesgo >= 0.7:
            alertas.append("RIESGO ALTO: La propiedad tiene un score de riesgo elevado.")
        elif score_riesgo >= 0.4:
            alertas.append("RIESGO MEDIO: Se recomienda revisión adicional de las transacciones.")
    
    # Pocas transacciones
    if total_tx == 1:
        alertas.append("Información limitada: Solo se encontró una transacción registrada.")
    
    # Precios sospechosos
    if precio_promedio and precio_promedio < 1000000:  # Menos de 1M COP
        alertas.append("ADVERTENCIA: Valores de transacción inusualmente bajos detectados.")
    
    # Si no hay alertas
    if not alertas:
        alertas.append("No se detectaron señales de riesgo significativas.")
    
    return alertas


@router.get("/stats")
async def get_property_stats(db: Session = Depends(get_db)):
    """Estadísticas generales de propiedades"""
    try:
        # Total de matrículas únicas
        total_matriculas = db.query(func.count(func.distinct(Transaction.matricula))).scalar()
        
        # Total de transacciones
        total_transactions = db.query(func.count(Transaction.pk)).scalar()
        
        # Transacciones anómalas
        anomalies = db.query(func.count(Transaction.pk)).filter(
            Transaction.is_anomaly == True
        ).scalar()
        
        # Promedio de transacciones por propiedad
        avg_tx_per_property = total_transactions / total_matriculas if total_matriculas > 0 else 0
        
        return {
            "total_propiedades": total_matriculas,
            "total_transacciones": total_transactions,
            "transacciones_anomalas": anomalies,
            "tasa_anomalias_global": f"{(anomalies/total_transactions*100):.2f}%" if total_transactions > 0 else "0%",
            "promedio_tx_por_propiedad": round(avg_tx_per_property, 2)
        }
    
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
