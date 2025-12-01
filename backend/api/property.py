"""
API Router for Property Search
Endpoint para buscar propiedades por matrícula inmobiliaria
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import sys
from pathlib import Path

# Agregar path de utils para importar parquet_reader
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path.parent))

router = APIRouter(prefix="/api/property", tags=["property"])


class PropertySearchRequest(BaseModel):
    """Request para buscar propiedad por matrícula"""
    matricula: str = Field(..., min_length=1, max_length=50, description="Número de matrícula inmobiliaria")


class PropertyTransaction(BaseModel):
    """Una transacción de la propiedad"""
    fecha: str = Field(..., description="Fecha de la transacción")
    tipo_acto: str = Field(..., description="Tipo de acto jurídico")
    valor: float = Field(..., description="Valor de la transacción")
    departamento: str = Field(..., description="Departamento")
    municipio: str = Field(..., description="Municipio")
    tipo_predio: str = Field(..., description="Tipo de predio")
    count_intervinientes: int = Field(..., description="Número de intervinientes")
    es_anomalo: bool = Field(default=False, description="Si fue detectado como anomalía")


class PropertySearchResponse(BaseModel):
    """Response de búsqueda de propiedad"""
    matricula: str = Field(..., description="Matrícula buscada")
    encontrada: bool = Field(..., description="Si se encontró la propiedad")
    total_transacciones: int = Field(default=0, description="Número total de transacciones")
    historial: List[PropertyTransaction] = Field(default_factory=list, description="Historial de transacciones")
    precio_promedio: Optional[float] = Field(default=None, description="Precio promedio de transacciones")
    precio_ultima: Optional[float] = Field(default=None, description="Precio de última transacción")
    tasa_anomalias: Optional[float] = Field(default=None, description="% de transacciones anómalas")
    ubicacion: Optional[Dict[str, str]] = Field(default=None, description="Departamento y municipio")
    alertas: List[str] = Field(default_factory=list, description="Alertas sobre la propiedad")
    score_riesgo: Optional[float] = Field(default=None, description="Score de riesgo 0-1")


@router.get("/debug/{matricula}")
async def debug_search(matricula: str):
    """Endpoint de debug para probar búsqueda directa"""
    import pandas as pd
    
    backend_path = Path(__file__).parent.parent
    data_path = backend_path.parent / 'data' / 'processed' / 'snr_synthetic.parquet'
    
    df = pd.read_parquet(data_path, columns=['matricula', 'valor_acto', 'departamento'])
    filtered = df[df['matricula'] == matricula]
    
    return {
        "matricula_buscada": matricula,
        "total_en_dataset": len(df),
        "encontrados": len(filtered),
        "registros": filtered.to_dict('records')
    }


@router.post("/search", response_model=PropertySearchResponse)
async def search_property(request: PropertySearchRequest):
    """
    Busca una propiedad por su número de matrícula inmobiliaria.
    
    Retorna:
    - Historial completo de transacciones
    - Análisis de riesgo
    - Precios históricos
    - Alertas de anomalías detectadas
    
    ⚠️ IMPORTANTE: Esta información es probabilística y con fines informativos únicamente.
    No constituye asesoría legal ni garantiza exactitud al 100%.
    """
    import logging
    logger = logging.getLogger("uvicorn")
    
    try:
        logger.info(f"POST /api/property/search - Matrícula: {request.matricula}")
        
        # Normalizar matrícula (sin espacios, mantener case original para números)
        matricula_clean = request.matricula.strip()
        
        logger.info(f"Matrícula limpia: '{matricula_clean}'")
        
        # Buscar en dataset SNR
        transactions = await _search_in_dataset(matricula_clean)
        
        if not transactions:
            return PropertySearchResponse(
                matricula=request.matricula,
                encontrada=False,
                total_transacciones=0,
                historial=[],
                alertas=["No se encontraron registros para esta matrícula en la base de datos."]
            )
        
        # Analizar transacciones
        historial = []
        valores = []
        anomalias = 0
        ultima_fecha = None
        ubicacion = None
        
        for tx in transactions:
            # Determinar si es anomalía (placeholder - en producción usar ML)
            es_anomalo = _detect_anomaly(tx)
            if es_anomalo:
                anomalias += 1
            
            valores.append(tx.get('valor_acto', 0))
            
            # Capturar ubicación de la primera transacción
            if ubicacion is None:
                ubicacion = {
                    "departamento": tx.get('departamento', 'N/A'),
                    "municipio": tx.get('municipio', 'N/A')
                }
            
            # Guardar fecha más reciente
            fecha_str = str(tx.get('fecha_radicacion', ''))
            if ultima_fecha is None or fecha_str > ultima_fecha:
                ultima_fecha = fecha_str
            
            historial.append(PropertyTransaction(
                fecha=fecha_str,
                tipo_acto=tx.get('nombre_natujur', 'N/A'),
                valor=tx.get('valor_acto', 0),
                departamento=tx.get('departamento', 'N/A'),
                municipio=tx.get('municipio', 'N/A'),
                tipo_predio=tx.get('tipo_predio', 'N/A'),
                count_intervinientes=tx.get('count_a', 0) + tx.get('count_de', 0),
                es_anomalo=es_anomalo
            ))
        
        # Calcular métricas
        total_tx = len(transactions)
        precio_promedio = sum(valores) / len(valores) if valores else None
        precio_ultima = valores[-1] if valores else None
        tasa_anomalias = (anomalias / total_tx * 100) if total_tx > 0 else 0
        
        # Calcular score de riesgo (0-1)
        score_riesgo = _calculate_risk_score(transactions, tasa_anomalias)
        
        # Generar alertas
        alertas = _generate_alerts(transactions, tasa_anomalias, score_riesgo)
        
        # Ordenar historial por fecha (más reciente primero)
        historial.sort(key=lambda x: x.fecha, reverse=True)
        
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
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar propiedad: {str(e)}"
        )


async def _search_in_dataset(matricula: str) -> List[Dict[str, Any]]:
    """
    Busca transacciones en el dataset SNR por matrícula.
    En producción, esto consultaría la base de datos real.
    """
    import pandas as pd
    import logging
    
    logger = logging.getLogger("uvicorn")
    
    # Path al dataset - usar path absoluto desde __file__
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    data_path = project_root / 'data' / 'processed' / 'snr_synthetic.parquet'
    
    logger.info(f"Buscando matrícula: {matricula}")
    logger.info(f"Path dataset: {data_path}")
    logger.info(f"Existe? {data_path.exists()}")
    
    if not data_path.exists():
        logger.error(f"Dataset no encontrado en {data_path}")
        return []
    
    try:
        # Leer solo las columnas necesarias
        df = pd.read_parquet(
            data_path,
            columns=[
                'matricula', 'fecha_radicacion', 'nombre_natujur', 'valor_acto',
                'departamento', 'municipio', 'tipo_predio',
                'count_a', 'count_de', 'tiene_valor'
            ]
        )
        
        logger.info(f"Dataset cargado: {len(df)} registros")
        logger.info(f"Primeras matrículas: {df['matricula'].head().tolist()}")
        
        # Filtrar por matrícula
        df_filtered = df[df['matricula'] == matricula]
        
        logger.info(f"Encontrados: {len(df_filtered)} registros")
        
        # Convertir a lista de diccionarios
        result = df_filtered.to_dict('records')
        logger.info(f"Retornando {len(result)} registros")
        return result
        
    except Exception as e:
        logger.error(f"Error leyendo dataset: {e}", exc_info=True)
        return []


def _detect_anomaly(transaction: Dict[str, Any]) -> bool:
    """
    Detecta si una transacción es anómala.
    Usa heurística simple basada en valor.
    En producción, esto usaría el modelo ML de anomalías.
    """
    # Heurística simple basada en valor
    valor = transaction.get('valor_acto', 0)
    if valor < 10_000_000 or valor > 5_000_000_000:  # < 10M o > 5B COP
        return True
    
    return False


def _calculate_risk_score(transactions: List[Dict[str, Any]], tasa_anomalias: float) -> float:
    """
    Calcula un score de riesgo 0-1 basado en el historial.
    
    Factores:
    - Tasa de anomalías (40%)
    - Variabilidad de precios (30%)
    - Frecuencia de transacciones (30%)
    """
    if not transactions:
        return 0.5
    
    # Factor 1: Tasa de anomalías (0-1)
    factor_anomalias = min(tasa_anomalias / 50, 1.0)  # 50% anomalías = riesgo máximo
    
    # Factor 2: Variabilidad de precios
    valores = [tx.get('valor', 0) for tx in transactions if tx.get('valor', 0) > 0]
    if len(valores) > 1:
        import numpy as np
        std = np.std(valores)
        mean = np.mean(valores)
        cv = (std / mean) if mean > 0 else 0  # Coeficiente de variación
        factor_variabilidad = min(cv, 1.0)
    else:
        factor_variabilidad = 0.0
    
    # Factor 3: Frecuencia (muchas transacciones en poco tiempo = sospechoso)
    total_tx = len(transactions)
    if total_tx > 10:
        factor_frecuencia = min(total_tx / 20, 1.0)  # >20 transacciones = riesgo máximo
    else:
        factor_frecuencia = 0.0
    
    # Score ponderado
    score = (
        factor_anomalias * 0.4 +
        factor_variabilidad * 0.3 +
        factor_frecuencia * 0.3
    )
    
    return round(score, 3)


def _generate_alerts(transactions: List[Dict[str, Any]], tasa_anomalias: float, score_riesgo: float) -> List[str]:
    """
    Genera alertas basadas en el análisis de transacciones.
    """
    alertas = []
    
    # Alerta por tasa de anomalías alta
    if tasa_anomalias > 30:
        alertas.append(f"⚠️ Alta tasa de transacciones anómalas ({tasa_anomalias:.1f}%)")
    
    # Alerta por score de riesgo alto
    if score_riesgo > 0.7:
        alertas.append("🚨 Score de riesgo elevado - Revisar historial detalladamente")
    elif score_riesgo > 0.4:
        alertas.append("⚠️ Score de riesgo moderado - Se recomienda precaución")
    
    # Alerta por transacciones recientes
    total_tx = len(transactions)
    if total_tx > 5:
        alertas.append(f"📊 Propiedad con historial amplio ({total_tx} transacciones registradas)")
    
    # Alerta por variabilidad de precios
    valores = [tx.get('valor', 0) for tx in transactions if tx.get('valor', 0) > 0]
    if len(valores) > 1:
        max_val = max(valores)
        min_val = min(valores)
        if max_val > min_val * 3:  # Variación >300%
            alertas.append("📈 Variabilidad significativa de precios en el historial")
    
    # Si no hay alertas, dar mensaje positivo
    if not alertas:
        alertas.append("[OK] No se detectaron senales de alerta significativas")
    
    return alertas


@router.get("/health")
async def health():
    """Health check del servicio de búsqueda de propiedades"""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    data_path = project_root / 'data' / 'processed' / 'snr_synthetic.parquet'
    
    return {
        "status": "ok",
        "dataset_disponible": data_path.exists(),
        "dataset_path": str(data_path)
    }


@router.get("/test/{matricula}")
async def test_search(matricula: str):
    """Test de búsqueda directa"""
    import pandas as pd
    
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    data_path = project_root / 'data' / 'processed' / 'snr_synthetic.parquet'
    
    if not data_path.exists():
        return {"error": "Dataset no existe", "path": str(data_path)}
    
    df = pd.read_parquet(data_path)
    result = df[df['matricula'] == matricula]
    
    return {
        "matricula": matricula,
        "encontrados": len(result),
        "columnas": df.columns.tolist(),
        "primeras_matriculas": df['matricula'].head(5).tolist()
    }
