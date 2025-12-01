"""
Simple FastAPI Backend - Con predicción de precios ML
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

app = FastAPI(
    title="Real Estate Risk Platform API",
    description="API para detección de anomalías en transacciones inmobiliarias",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
try:
    from api.valuation import router as valuation_router
    app.include_router(valuation_router)
    print("[OK] Valuation router cargado")
except Exception as e:
    print(f"[WARN] No se pudo cargar valuation router: {e}")

try:
    from api.property import router as property_router
    app.include_router(property_router)
    print("[OK] Property router cargado")
except Exception as e:
    print(f"[WARN] No se pudo cargar property router: {e}")

try:
    from api.chat import router as chat_router
    app.include_router(chat_router)
    print("[OK] Chat router cargado")
except Exception as e:
    print(f"[WARN] No se pudo cargar chat router: {e}")

# Schemas
class TransactionRequest(BaseModel):
    valor_acto: float
    tipo_acto: str = "compraventa"
    fecha_acto: Optional[datetime] = None
    departamento: str = "BOGOTA"
    municipio: str = "BOGOTA"
    tipo_predio: str = "urbano"
    numero_intervinientes: int = 2

class AnomalyResponse(BaseModel):
    anomaly_score: float
    classification: str
    explanation: str
    confidence: float

@app.get("/")
async def root():
    return {
        "message": "Real Estate Risk Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/transactions/analyze", response_model=AnomalyResponse)
async def analyze_transaction(transaction: TransactionRequest):
    """Análisis simplificado de transacción"""
    # Simulación de análisis
    score = 0.3 if transaction.valor_acto > 100000000 else 0.6
    
    classification = "normal" if score < 0.4 else "suspicious" if score < 0.7 else "high-risk"
    
    return AnomalyResponse(
        anomaly_score=score,
        classification=classification,
        explanation=f"Transacción de tipo {transaction.tipo_acto} por valor de ${transaction.valor_acto:,.0f} COP en {transaction.municipio}",
        confidence=0.85
    )

@app.get("/api/map/transactions")
async def get_map_data():
    """Datos mock para visualización de mapa"""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-74.0721, 4.7110]},
                "properties": {"municipio": "BOGOTA", "count": 15000, "anomaly_rate": 0.15}
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-75.5636, 6.2476]},
                "properties": {"municipio": "MEDELLIN", "count": 8000, "anomaly_rate": 0.12}
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
