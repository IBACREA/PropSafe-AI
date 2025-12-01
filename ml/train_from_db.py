#!/usr/bin/env python3
"""
Train ML models using data from PostgreSQL database

Usage:
    python train_from_db.py --sample-size 100000 --output ml/models
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.model_selection import train_test_split
import joblib
from sqlalchemy import text

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.core.database import engine, SessionLocal
from backend.models.db_models import Transaction, ModelMetadata
from ml.feature_engineering import FeatureEngineer
from backend.core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


class ModelTrainer:
    """Train anomaly detection models from database"""
    
    def __init__(self, output_dir: str = './ml/models'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.models = {}
        self.metadata = {}
        
    def load_data(self, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        Load training data from PostgreSQL
        
        Args:
            sample_size: Number of records to sample (None = all data)
            
        Returns:
            DataFrame with transaction data
        """
        logger.info("📂 Loading data from PostgreSQL...")
        
        query = """
        SELECT 
            pk, matricula, fecha_radicacion, fecha_apertura, year_radica,
            orip, divipola, departamento, municipio, tipo_predio,
            nombre_natujur, valor_acto, tiene_valor, count_a, count_de,
            estado_folio, area_terreno, area_construida
        FROM transactions
        WHERE matricula IS NOT NULL
        """
        
        if sample_size:
            query += f" ORDER BY RANDOM() LIMIT {sample_size}"
            
        df = pd.read_sql(query, engine)
        logger.info(f"✅ Loaded {len(df):,} transactions")
        
        return df
    
    def train_isolation_forest(self, X_train, X_test):
        """Train Isolation Forest model"""
        logger.info("🌲 Training Isolation Forest...")
        
        model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=150,
            max_samples='auto',
            max_features=1.0,
            bootstrap=False,
            n_jobs=-1,
            verbose=0
        )
        
        model.fit(X_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        scores = model.score_samples(X_test)
        anomaly_count = (y_pred == -1).sum()
        
        logger.info(f"  ✓ Anomalies in test: {anomaly_count:,} ({anomaly_count/len(X_test)*100:.1f}%)")
        
        # Save model
        model_path = self.output_dir / 'isolation_forest.joblib'
        joblib.dump(model, model_path)
        logger.info(f"  💾 Saved to: {model_path}")
        
        self.models['isolation_forest'] = {
            'model': model,
            'path': str(model_path),
            'anomalies_detected': int(anomaly_count),
            'mean_score': float(scores.mean()),
            'std_score': float(scores.std())
        }
        
        return model, scores
    
    def train_local_outlier_factor(self, X_train, X_test):
        """Train Local Outlier Factor model"""
        logger.info("🎯 Training Local Outlier Factor...")
        
        model = LocalOutlierFactor(
            n_neighbors=25,
            contamination=0.1,
            novelty=True,  # Enable prediction on new data
            algorithm='auto',
            metric='minkowski',
            n_jobs=-1
        )
        
        model.fit(X_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        scores = model.score_samples(X_test)
        anomaly_count = (y_pred == -1).sum()
        
        logger.info(f"  ✓ Anomalies in test: {anomaly_count:,} ({anomaly_count/len(X_test)*100:.1f}%)")
        
        # Save model
        model_path = self.output_dir / 'local_outlier_factor.joblib'
        joblib.dump(model, model_path)
        logger.info(f"  💾 Saved to: {model_path}")
        
        self.models['lof'] = {
            'model': model,
            'path': str(model_path),
            'anomalies_detected': int(anomaly_count),
            'mean_score': float(scores.mean()),
            'std_score': float(scores.std())
        }
        
        return model, scores
    
    def calculate_ensemble_scores(self, if_scores, lof_scores):
        """Calculate weighted ensemble anomaly scores"""
        logger.info("⚖️  Calculating ensemble scores...")
        
        # Normalize scores to 0-1 range
        if_norm = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min())
        lof_norm = (lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min())
        
        # Invert (higher = more anomalous)
        if_norm = 1 - if_norm
        lof_norm = 1 - lof_norm
        
        # Weighted average (IF: 60%, LOF: 40%)
        ensemble_scores = 0.6 * if_norm + 0.4 * lof_norm
        
        return ensemble_scores
    
    def calculate_feature_importance(self, model, X, feature_names):
        """Calculate feature importance (approximate)"""
        logger.info("📊 Calculating feature importance...")
        
        scores = model.score_samples(X)
        importance = {}
        
        for i, feature in enumerate(feature_names):
            # Correlation between feature and anomaly score
            corr = np.corrcoef(X[:, i], scores)[0, 1]
            importance[feature] = abs(corr)
        
        # Sort by importance
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        logger.info("  Top 10 features:")
        for feature, score in sorted_importance[:10]:
            logger.info(f"    {feature:30s}: {score:.4f}")
        
        # Save
        importance_path = self.output_dir / 'feature_importance.json'
        with open(importance_path, 'w') as f:
            json.dump(importance, f, indent=2)
        
        return importance
    
    def save_metadata_to_db(self, train_samples: int, feature_names: list):
        """Save model metadata to database"""
        logger.info("💾 Saving model metadata to database...")
        
        db = SessionLocal()
        try:
            # Deactivate previous models
            db.query(ModelMetadata).filter(
                ModelMetadata.is_active == True
            ).update({'is_active': False})
            
            # Save new model metadata
            for model_name, model_info in self.models.items():
                metadata = ModelMetadata(
                    model_name=model_name,
                    model_version=datetime.now().strftime('%Y%m%d_%H%M%S'),
                    model_type=model_name,
                    trained_at=datetime.now(),
                    training_samples=train_samples,
                    features_used=json.dumps(feature_names),
                    model_path=model_info['path'],
                    is_active=True
                )
                db.add(metadata)
            
            db.commit()
            logger.info("  ✅ Metadata saved to database")
            
        except Exception as e:
            db.rollback()
            logger.error(f"  ❌ Error saving metadata: {e}")
        finally:
            db.close()
    
    def run(self, sample_size: Optional[int] = None):
        """Run complete training pipeline"""
        start_time = datetime.now()
        
        logger.info("=" * 80)
        logger.info("🚀 MACHINE LEARNING MODEL TRAINING")
        logger.info("=" * 80)
        logger.info(f"Started at: {start_time.isoformat()}")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        logger.info("=" * 80)
        
        # 1. Load data
        df = self.load_data(sample_size)
        
        # 2. Feature engineering
        logger.info("🔧 Performing feature engineering...")
        engineer = FeatureEngineer()
        X, feature_names = engineer.fit_transform(df)
        logger.info(f"  ✅ Created {len(feature_names)} features")
        
        # Save feature engineer
        engineer_path = self.output_dir / 'feature_engineer.joblib'
        engineer.save(engineer_path)
        logger.info(f"  💾 Feature engineer saved to: {engineer_path}")
        
        # 3. Split data
        X_train, X_test = train_test_split(X, test_size=0.2, random_state=42, shuffle=True)
        logger.info(f"📊 Train: {X_train.shape[0]:,} | Test: {X_test.shape[0]:,}")
        
        # 4. Train models
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING MODELS")
        logger.info("=" * 80)
        
        if_model, if_scores = self.train_isolation_forest(X_train, X_test)
        lof_model, lof_scores = self.train_local_outlier_factor(X_train, X_test)
        
        # 5. Ensemble
        logger.info("\n" + "=" * 80)
        logger.info("ENSEMBLE MODEL")
        logger.info("=" * 80)
        
        ensemble_scores = self.calculate_ensemble_scores(if_scores, lof_scores)
        
        # Classify by thresholds
        high_risk = (ensemble_scores >= 0.7).sum()
        suspicious = ((ensemble_scores >= 0.4) & (ensemble_scores < 0.7)).sum()
        normal = (ensemble_scores < 0.4).sum()
        
        logger.info(f"  High Risk: {high_risk:,} ({high_risk/len(ensemble_scores)*100:.1f}%)")
        logger.info(f"  Suspicious: {suspicious:,} ({suspicious/len(ensemble_scores)*100:.1f}%)")
        logger.info(f"  Normal: {normal:,} ({normal/len(ensemble_scores)*100:.1f}%)")
        
        # 6. Feature importance
        importance = self.calculate_feature_importance(if_model, X_test, feature_names)
        
        # 7. Save metadata to database
        self.save_metadata_to_db(len(df), feature_names)
        
        # 8. Save training summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            'training_date': start_time.isoformat(),
            'duration_seconds': duration,
            'n_samples': len(df),
            'n_features': len(feature_names),
            'train_test_split': {'train': X_train.shape[0], 'test': X_test.shape[0]},
            'models': {
                name: {
                    'path': info['path'],
                    'anomalies_detected': info['anomalies_detected']
                }
                for name, info in self.models.items()
            },
            'ensemble_performance': {
                'high_risk': int(high_risk),
                'suspicious': int(suspicious),
                'normal': int(normal)
            },
            'top_features': list(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:15])
        }
        
        summary_path = self.output_dir / 'training_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ TRAINING COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        logger.info(f"Summary saved to: {summary_path}")
        logger.info("=" * 80)
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='Train ML models from PostgreSQL database')
    parser.add_argument('--sample-size', type=int, default=None,
                       help='Number of records to sample (default: all)')
    parser.add_argument('--output', type=str, default='./ml/models',
                       help='Output directory for models')
    
    args = parser.parse_args()
    
    trainer = ModelTrainer(output_dir=args.output)
    trainer.run(sample_size=args.sample_size)


if __name__ == '__main__':
    main()
