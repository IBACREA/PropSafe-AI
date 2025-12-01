from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import Dict, Any
import pandas as pd
import io
import time
from datetime import datetime

from api.schemas import (
    TransactionInput,
    TransactionAnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BatchAnalysisStats,
    AnomalyAnalysisResult,
    RiskLevel,
    ContributingFeature
)
from models.anomaly_model import AnomalyDetector
from core.logger import get_logger
from utils.validators import validate_transaction_data

logger = get_logger(__name__)
router = APIRouter(prefix="/api/transactions", tags=["transactions"])

# Global model instance (initialized on startup)
anomaly_detector: AnomalyDetector = None


def get_anomaly_detector() -> AnomalyDetector:
    """Get the global anomaly detector instance."""
    global anomaly_detector
    if anomaly_detector is None:
        anomaly_detector = AnomalyDetector()
    return anomaly_detector


@router.post("/analyze-transaction", response_model=TransactionAnalysisResponse)
async def analyze_transaction(transaction: TransactionInput) -> TransactionAnalysisResponse:
    """
    Analyze a single real estate transaction for anomalies and fraud risk.
    
    Returns risk score, classification, and contributing features.
    """
    start_time = time.time()
    
    try:
        logger.info("analyzing_transaction", 
                   municipio=transaction.municipio,
                   valor=transaction.valor_acto)
        
        # Validate transaction data
        validate_transaction_data(transaction)
        
        # Get detector
        detector = get_anomaly_detector()
        
        # Convert to features
        features = detector.prepare_features(transaction)
        
        # Predict anomaly
        result = detector.predict_anomaly(features, transaction)
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info("transaction_analyzed",
                   score=result.anomaly_score,
                   classification=result.classification,
                   processing_time_ms=processing_time)
        
        return TransactionAnalysisResponse(
            result=result,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error("transaction_analysis_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error analyzing transaction: {str(e)}")


@router.post("/batch-analyze", response_model=BatchAnalysisResponse)
async def batch_analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    analyze_all: bool = True,
    limit: int = None
) -> BatchAnalysisResponse:
    """
    Analyze multiple transactions from CSV or Parquet file.
    
    Returns aggregated statistics and high-risk transactions.
    """
    start_time = time.time()
    
    try:
        logger.info("batch_analysis_started", filename=file.filename)
        
        # Read file based on format
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith('.parquet'):
            df = pd.read_parquet(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Parquet.")
        
        # Apply limit if specified
        if limit and not analyze_all:
            df = df.head(limit)
        
        detector = get_anomaly_detector()
        
        # Process in chunks
        results = []
        high_risk_transactions = []
        
        for idx, row in df.iterrows():
            try:
                # Convert row to TransactionInput
                transaction = TransactionInput(**row.to_dict())
                features = detector.prepare_features(transaction)
                result = detector.predict_anomaly(features, transaction)
                
                results.append({
                    'index': idx,
                    'score': result.anomaly_score,
                    'classification': result.classification
                })
                
                # Collect high-risk transactions
                if result.classification == RiskLevel.HIGH_RISK:
                    high_risk_transactions.append({
                        'row_index': idx,
                        'data': row.to_dict(),
                        'analysis': result.dict()
                    })
                    
            except Exception as e:
                logger.warning("row_analysis_failed", index=idx, error=str(e))
                continue
        
        # Calculate statistics
        total = len(results)
        normal = sum(1 for r in results if r['classification'] == RiskLevel.NORMAL)
        suspicious = sum(1 for r in results if r['classification'] == RiskLevel.SUSPICIOUS)
        high_risk = sum(1 for r in results if r['classification'] == RiskLevel.HIGH_RISK)
        avg_score = sum(r['score'] for r in results) / total if total > 0 else 0
        
        processing_time = time.time() - start_time
        
        stats = BatchAnalysisStats(
            total_transactions=total,
            normal_count=normal,
            suspicious_count=suspicious,
            high_risk_count=high_risk,
            average_score=avg_score,
            processing_time_seconds=processing_time
        )
        
        logger.info("batch_analysis_completed",
                   total=total,
                   high_risk=high_risk,
                   processing_time=processing_time)
        
        return BatchAnalysisResponse(
            stats=stats,
            high_risk_transactions=high_risk_transactions[:100]  # Limit to top 100
        )
        
    except Exception as e:
        logger.error("batch_analysis_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error in batch analysis: {str(e)}")


@router.get("/stats")
async def get_transaction_stats() -> Dict[str, Any]:
    """Get general transaction statistics from the system."""
    return {
        "status": "active",
        "model_loaded": anomaly_detector is not None,
        "timestamp": datetime.utcnow().isoformat()
    }
