"""
API Router for Price Valuation
Endpoint para validar precios de transacciones usando ML
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Agregar path de ml para importar (ir un nivel arriba del backend)
ml_path = Path(__file__).parent.parent.parent / 'ml'
sys.path.insert(0, str(ml_path.parent))

try:
    from ml.price_prediction import PricePredictor
    model_path = ml_path / 'models'
    predictor = PricePredictor.load(str(model_path))
    PREDICTOR_LOADED = True
    print(f"[OK] Modelo de prediccion cargado desde: {model_path}")
except Exception as e:
    print(f"⚠️ No se pudo cargar el modelo de predicción: {e}")
    print(f"   Path intentado: {ml_path}")
    predictor = None
    PREDICTOR_LOADED = False

router = APIRouter(prefix="/api/valuation", tags=["valuation"])


class ValuationRequest(BaseModel):
    """Request para validar precio de transacción - Columnas SNR"""
    municipio: str = Field(..., description="Municipio (MAYÚSCULAS)")
    departamento: str = Field(..., description="Departamento (MAYÚSCULAS)")
    tipo_predio: str = Field(default="URBANO", description="URBANO, RURAL, SIN INFORMACION")
    nombre_natujur: str = Field(default="COMPRAVENTA", description="Tipo de acto jurídico")
    estado_folio: str = Field(default="ACTIVO", description="Estado del folio")
    count_a: int = Field(default=1, description="Número de receptores")
    count_de: int = Field(default=1, description="Número de otorgantes")
    predios_nuevos: int = Field(default=0, description="1 si es predio nuevo, 0 si no")
    categoria_ruralidad: Optional[str] = Field(default=None, description="Categoría de ruralidad DNP")
    valor_acto: float = Field(..., description="Valor de la transacción a validar")


class ValuationResponse(BaseModel):
    """Response de validación de precio"""
    precio_predicho: float = Field(..., description="Precio predicho por el modelo")
    rango_normal: Dict[str, float] = Field(..., description="Rango de confianza")
    tu_precio: float = Field(..., description="Precio ingresado")
    score_confianza: float = Field(..., description="Nivel de confianza 0-1")
    es_sospechoso: bool = Field(..., description="Si el precio es sospechoso")
    desviacion_porcentaje: float = Field(..., description="% de desviación")
    mensaje: str = Field(..., description="Mensaje explicativo")
    clasificacion: str = Field(..., description="normal, precaucion, sospechoso")
    recomendaciones: list[str] = Field(default_factory=list, description="Recomendaciones")


@router.get("/health")
async def health_check():
    """Verifica si el modelo está cargado"""
    return {
        "status": "ok" if PREDICTOR_LOADED else "model_not_loaded",
        "model_loaded": PREDICTOR_LOADED,
        "model_stats": predictor.stats if predictor else None
    }


@router.post("/predict", response_model=ValuationResponse)
async def predict_price(request: ValuationRequest):
    """
    Predice el precio justo de una transacción y valida si es sospechoso
    
    Retorna:
    - Precio predicho por el modelo
    - Rango de confianza (percentil 5-95)
    - Si el precio es sospechoso
    - Recomendaciones
    """
    if not PREDICTOR_LOADED or not predictor:
        raise HTTPException(
            status_code=503,
            detail="Modelo de predicción no disponible. Entrena el modelo primero."
        )
    
    try:
        # Convertir request a dict para el predictor
        transaction_data = request.model_dump()
        
        # Hacer predicción
        result = predictor.predict(transaction_data)
        
        # Clasificar según desviación
        desviacion = result['deviation_percentage']
        if desviacion < 15:
            clasificacion = "normal"
            mensaje = "[OK] Precio dentro del rango esperado para transacciones similares en esta zona"
            recomendaciones = []
        elif desviacion < 30:
            clasificacion = "precaucion"
            mensaje = "[WARN] Precio con desviación moderada. Revisar detalles de la transacción"
            recomendaciones = [
                "Verificar características específicas del inmueble",
                "Comparar con transacciones recientes en la misma zona",
                "Consultar avalúo catastral actualizado"
            ]
        else:
            clasificacion = "sospechoso"
            if request.valor_acto < result['predicted_price']:
                mensaje = "[ALERT] Precio significativamente BAJO. Posible subvaluación o fraude"
                recomendaciones = [
                    "[!] Revisar si existe un avalúo independiente reciente",
                    "[!] Verificar estado real del inmueble",
                    "[!] Consultar si existen gravámenes o limitaciones",
                    "[!] Validar identidad de compradores y vendedores",
                    "[!] Considerar auditoría adicional"
                ]
            else:
                mensaje = "[ALERT] Precio significativamente ALTO. Posible sobrevaloración"
                recomendaciones = [
                    "Verificar mejoras o características premium no declaradas",
                    "Comparar con avalúo comercial reciente",
                    "Revisar si incluye bienes muebles o servicios adicionales"
                ]
        
        # Calcular score de confianza (inverso de la desviación)
        score_confianza = max(0, 1 - (desviacion / 100))
        
        return ValuationResponse(
            precio_predicho=result['predicted_price'],
            rango_normal={
                "minimo": result['confidence_interval']['low'],
                "maximo": result['confidence_interval']['high']
            },
            tu_precio=request.valor_acto,
            score_confianza=score_confianza,
            es_sospechoso=result['is_suspicious'],
            desviacion_porcentaje=desviacion,
            mensaje=mensaje,
            clasificacion=clasificacion,
            recomendaciones=recomendaciones
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al predecir precio: {str(e)}"
        )


@router.get("/stats")
async def get_model_stats():
    """Obtiene estadísticas del modelo entrenado"""
    if not PREDICTOR_LOADED or not predictor:
        raise HTTPException(
            status_code=503,
            detail="Modelo no disponible"
        )
    
    stats = predictor.stats.copy()
    
    # Formatear precios
    stats['precio_promedio_fmt'] = f"${stats['mean_price']:,.0f}"
    stats['precio_mediano_fmt'] = f"${stats['median_price']:,.0f}"
    stats['mae_fmt'] = f"${stats['test_mae']:,.0f}"
    
    return {
        "model_stats": stats,
        "top_features": stats.get('feature_importance', [])[:10]
    }
