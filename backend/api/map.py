from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from core.config import get_settings

logger = get_logger(__name__)
router = APIRouter(prefix="/api/map", tags=["map"])
settings = get_settings()


@router.get("/transactions")
async def get_map_transactions(
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    start_date: Optional[datetime] = Query(None, description="Fecha inicial"),
    end_date: Optional[datetime] = Query(None, description="Fecha final"),
    risk_level: Optional[str] = Query(None, description="Filtrar por nivel de riesgo"),
    limit: int = Query(1000, description="Límite de resultados", le=10000)
) -> Dict[str, Any]:
    """
    Get geo-ready transaction data for map visualization.
    
    Returns aggregated statistics by municipality with coordinates.
    """
    try:
        logger.info("map_data_requested",
                   departamento=departamento,
                   risk_level=risk_level)
        
        # TODO: Replace with actual database query
        # For now, return mock data with Colombia municipalities
        
        mock_data = generate_mock_map_data(departamento, risk_level, limit)
        
        return {
            "type": "FeatureCollection",
            "features": mock_data,
            "metadata": {
                "total_transactions": len(mock_data),
                "timestamp": datetime.utcnow().isoformat(),
                "filters": {
                    "departamento": departamento,
                    "risk_level": risk_level,
                    "date_range": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error("map_data_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching map data: {str(e)}")


@router.get("/municipalities/{departamento}")
async def get_municipalities(departamento: str) -> List[Dict[str, Any]]:
    """Get list of municipalities for a given department."""
    try:
        # Mock data - replace with actual database
        municipalities_data = get_colombia_municipalities()
        
        filtered = [
            m for m in municipalities_data 
            if m['departamento'].upper() == departamento.upper()
        ]
        
        return filtered
        
    except Exception as e:
        logger.error("municipalities_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heatmap")
async def get_heatmap_data(
    metric: str = Query("transaction_count", description="Métrica a visualizar"),
    departamento: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get heatmap data for visualization.
    
    Metrics: transaction_count, average_value, risk_score, anomaly_rate
    """
    try:
        logger.info("heatmap_requested", metric=metric, departamento=departamento)
        
        heatmap_data = generate_heatmap_data(metric, departamento)
        
        return {
            "metric": metric,
            "data": heatmap_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("heatmap_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def generate_mock_map_data(departamento: Optional[str], risk_level: Optional[str], limit: int) -> List[Dict]:
    """Generate mock GeoJSON features for map visualization."""
    
    # Sample Colombian municipalities with coordinates
    municipalities = [
        {"name": "BOGOTA", "dept": "CUNDINAMARCA", "lat": 4.7110, "lon": -74.0721},
        {"name": "MEDELLIN", "dept": "ANTIOQUIA", "lat": 6.2476, "lon": -75.5658},
        {"name": "CALI", "dept": "VALLE DEL CAUCA", "lat": 3.4516, "lon": -76.5320},
        {"name": "BARRANQUILLA", "dept": "ATLANTICO", "lat": 10.9685, "lon": -74.7813},
        {"name": "CARTAGENA", "dept": "BOLIVAR", "lat": 10.3910, "lon": -75.4794},
        {"name": "CUCUTA", "dept": "NORTE DE SANTANDER", "lat": 7.8939, "lon": -72.5078},
        {"name": "BUCARAMANGA", "dept": "SANTANDER", "lat": 7.1254, "lon": -73.1198},
        {"name": "PEREIRA", "dept": "RISARALDA", "lat": 4.8133, "lon": -75.6961},
        {"name": "IBAGUE", "dept": "TOLIMA", "lat": 4.4389, "lon": -75.2322},
        {"name": "MANIZALES", "dept": "CALDAS", "lat": 5.0689, "lon": -75.5174},
    ]
    
    features = []
    for muni in municipalities[:limit]:
        if departamento and muni['dept'] != departamento.upper():
            continue
            
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [muni['lon'], muni['lat']]
            },
            "properties": {
                "municipio": muni['name'],
                "departamento": muni['dept'],
                "transaction_count": 1250,
                "average_value": 285000000,
                "high_risk_count": 45,
                "suspicious_count": 120,
                "normal_count": 1085,
                "anomaly_rate": 0.132
            }
        }
        features.append(feature)
    
    return features


def get_colombia_municipalities() -> List[Dict[str, Any]]:
    """Get Colombia municipalities data."""
    return [
        {"municipio": "BOGOTA", "departamento": "CUNDINAMARCA", "codigo": "11001"},
        {"municipio": "MEDELLIN", "departamento": "ANTIOQUIA", "codigo": "05001"},
        {"municipio": "CALI", "departamento": "VALLE DEL CAUCA", "codigo": "76001"},
        # Add more municipalities as needed
    ]


def generate_heatmap_data(metric: str, departamento: Optional[str]) -> List[Dict]:
    """Generate heatmap data points."""
    # Mock implementation
    return [
        {"lat": 4.7110, "lon": -74.0721, "intensity": 0.85, "value": 1250},
        {"lat": 6.2476, "lon": -75.5658, "intensity": 0.72, "value": 980},
        {"lat": 3.4516, "lon": -76.5320, "intensity": 0.65, "value": 850},
    ]
