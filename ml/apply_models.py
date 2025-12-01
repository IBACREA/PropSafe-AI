#!/usr/bin/env python3
"""
Apply trained ML models to database transactions

Scores all transactions in the database and updates anomaly_score and is_anomaly fields

Usage:
    python apply_models.py --batch-size 5000
"""

import sys
import argparse
from pathlib import Path
import joblib
from datetime import datetime
from sqlalchemy import text

sys.path.append(str(Path(__file__).parent.parent))

from backend.core.database import engine, SessionLocal
from backend.models.db_models import Transaction
from ml.feature_engineering import FeatureEngineer
from backend.core.logger import setup_logging, get_logger
import pandas as pd

setup_logging()
logger = get_logger(__name__)


def load_models(model_dir: str):
    """Load trained models"""
    model_path = Path(model_dir)
    
    logger.info("📦 Loading trained models...")
    
    try:
        # Load feature engineer
        engineer = FeatureEngineer.load(model_path / 'feature_engineer.joblib')
        logger.info("  ✅ Feature engineer loaded")
        
        # Load Isolation Forest
        iso_forest = joblib.load(model_path / 'isolation_forest.joblib')
        logger.info("  ✅ Isolation Forest loaded")
        
        # Load LOF
        lof = joblib.load(model_path / 'local_outlier_factor.joblib')
        logger.info("  ✅ Local Outlier Factor loaded")
        
        return engineer, iso_forest, lof
    
    except Exception as e:
        logger.error(f"❌ Error loading models: {e}")
        raise


def score_batch(df: pd.DataFrame, engineer, iso_forest, lof):
    """Score a batch of transactions"""
    
    # Feature engineering
    X, _ = engineer.transform(df)
    
    # Get scores from both models
    if_scores = iso_forest.score_samples(X)
    lof_scores = lof.score_samples(X)
    
    # Normalize to 0-1 range (higher = more anomalous)
    if_norm = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min())
    lof_norm = (lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min())
    
    # Invert (sklearn scores are negative for anomalies)
    if_norm = 1 - if_norm
    lof_norm = 1 - lof_norm
    
    # Weighted ensemble (IF: 60%, LOF: 40%)
    ensemble_scores = 0.6 * if_norm + 0.4 * lof_norm
    
    # Classify (threshold: 0.5)
    is_anomaly = ensemble_scores >= 0.5
    
    return ensemble_scores, is_anomaly


def apply_models(model_dir: str, batch_size: int = 5000):
    """Apply models to all transactions in database"""
    
    start_time = datetime.now()
    
    logger.info("=" * 80)
    logger.info("🎯 APPLYING ML MODELS TO DATABASE")
    logger.info("=" * 80)
    logger.info(f"Started at: {start_time.isoformat()}")
    logger.info(f"Batch size: {batch_size:,}")
    logger.info("=" * 80)
    
    # Load models
    engineer, iso_forest, lof = load_models(model_dir)
    
    # Get total count
    db = SessionLocal()
    total_records = db.query(Transaction).count()
    logger.info(f"📊 Total transactions in database: {total_records:,}")
    db.close()
    
    # Process in batches
    processed = 0
    anomalies_found = 0
    
    query = """
    SELECT 
        pk, matricula, fecha_radicacion, fecha_apertura, year_radica,
        orip, divipola, departamento, municipio, tipo_predio,
        nombre_natujur, valor_acto, tiene_valor, count_a, count_de,
        estado_folio, area_terreno, area_construida
    FROM transactions
    ORDER BY pk
    LIMIT {limit} OFFSET {offset}
    """
    
    offset = 0
    
    while offset < total_records:
        logger.info(f"\n📦 Processing batch {offset:,} - {offset+batch_size:,}")
        
        # Load batch
        batch_query = query.format(limit=batch_size, offset=offset)
        df = pd.read_sql(batch_query, engine)
        
        if len(df) == 0:
            break
        
        # Score batch
        scores, is_anomaly = score_batch(df, engineer, iso_forest, lof)
        
        # Update database
        db = SessionLocal()
        try:
            for idx, row in df.iterrows():
                db.query(Transaction).filter(
                    Transaction.pk == row['pk']
                ).update({
                    'anomaly_score': float(scores[idx]),
                    'is_anomaly': bool(is_anomaly[idx]),
                    'risk_classification': _classify_risk(scores[idx]),
                    'updated_at': datetime.now()
                })
            
            db.commit()
            
            batch_anomalies = is_anomaly.sum()
            anomalies_found += batch_anomalies
            processed += len(df)
            
            logger.info(f"  ✅ Updated {len(df):,} records")
            logger.info(f"  🚨 Anomalies in batch: {batch_anomalies:,} ({batch_anomalies/len(df)*100:.1f}%)")
            logger.info(f"  📈 Progress: {processed:,}/{total_records:,} ({processed/total_records*100:.1f}%)")
        
        except Exception as e:
            db.rollback()
            logger.error(f"  ❌ Error updating batch: {e}")
        
        finally:
            db.close()
        
        offset += batch_size
    
    # Final statistics
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ MODEL APPLICATION COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total processed: {processed:,}")
    logger.info(f"Anomalies found: {anomalies_found:,} ({anomalies_found/processed*100:.1f}%)")
    logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    logger.info(f"Throughput: {processed/duration:.0f} records/second")
    logger.info("=" * 80)


def _classify_risk(score: float) -> str:
    """Classify risk based on score"""
    if score >= 0.7:
        return "high-risk"
    elif score >= 0.4:
        return "suspicious"
    else:
        return "normal"


def main():
    parser = argparse.ArgumentParser(description='Apply trained models to database')
    parser.add_argument('--model-dir', type=str, default='./ml/models',
                       help='Directory with trained models')
    parser.add_argument('--batch-size', type=int, default=5000,
                       help='Batch size for processing')
    
    args = parser.parse_args()
    
    apply_models(args.model_dir, args.batch_size)


if __name__ == '__main__':
    main()
