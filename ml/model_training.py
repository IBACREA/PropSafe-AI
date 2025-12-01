#!/usr/bin/env python3
"""
Training script for real estate anomaly detection models.

Trains an ensemble of:
- Isolation Forest
- Local Outlier Factor  
- Statistical baselines

Run: python model_training.py
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from ml.feature_engineering import FeatureEngineer, create_sample_dataset


def train_models(data_path: str = None, output_dir: str = './models'):
    """
    Train anomaly detection models.
    
    Args:
        data_path: Path to training data (CSV or Parquet)
        output_dir: Directory to save trained models
    """
    print("=" * 70)
    print("REAL ESTATE ANOMALY DETECTION - MODEL TRAINING")
    print("=" * 70)
    print(f"Training started: {datetime.now().isoformat()}\n")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load or create data
    if data_path:
        print(f"Loading data from: {data_path}")
        if data_path.endswith('.parquet'):
            df = pd.read_parquet(data_path)
        else:
            df = pd.read_csv(data_path)
    else:
        print("No data path provided. Creating synthetic dataset...")
        df = create_sample_dataset(n_samples=50000)
    
    print(f"Dataset size: {len(df):,} transactions")
    print(f"Columns: {list(df.columns)}\n")
    
    # Feature engineering
    print("Performing feature engineering...")
    engineer = FeatureEngineer()
    X, feature_names = engineer.fit_transform(df)
    print(f"Created {X.shape[1]} features")
    print(f"Feature names: {feature_names[:10]}...\n")
    
    # Save feature engineer
    engineer_path = output_path / 'feature_engineer.joblib'
    engineer.save(engineer_path)
    print(f"✓ Feature engineer saved to: {engineer_path}\n")
    
    # Split data
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
    print(f"Training set: {X_train.shape[0]:,} samples")
    print(f"Test set: {X_test.shape[0]:,} samples\n")
    
    # Train Isolation Forest
    print("-" * 70)
    print("Training Isolation Forest...")
    print("-" * 70)
    
    iso_forest = IsolationForest(
        contamination=0.1,  # Expected 10% anomalies
        random_state=42,
        n_estimators=100,
        max_samples='auto',
        n_jobs=-1,
        verbose=1
    )
    
    iso_forest.fit(X_train)
    
    # Evaluate on test set
    y_pred_if = iso_forest.predict(X_test)
    anomaly_count_if = (y_pred_if == -1).sum()
    print(f"✓ Isolation Forest trained")
    print(f"  Anomalies detected in test set: {anomaly_count_if:,} ({anomaly_count_if/len(X_test)*100:.2f}%)")
    
    # Save Isolation Forest
    if_path = output_path / 'isolation_forest.joblib'
    joblib.dump(iso_forest, if_path)
    print(f"  Saved to: {if_path}\n")
    
    # Train Local Outlier Factor
    print("-" * 70)
    print("Training Local Outlier Factor...")
    print("-" * 70)
    
    lof = LocalOutlierFactor(
        n_neighbors=20,
        contamination=0.1,
        novelty=True,  # Enable predict on new data
        n_jobs=-1
    )
    
    lof.fit(X_train)
    
    # Evaluate
    y_pred_lof = lof.predict(X_test)
    anomaly_count_lof = (y_pred_lof == -1).sum()
    print(f"✓ Local Outlier Factor trained")
    print(f"  Anomalies detected in test set: {anomaly_count_lof:,} ({anomaly_count_lof/len(X_test)*100:.2f}%)")
    
    # Save LOF
    lof_path = output_path / 'lof.joblib'
    joblib.dump(lof, lof_path)
    print(f"  Saved to: {lof_path}\n")
    
    # Calculate feature importance (approximation using IF)
    print("-" * 70)
    print("Calculating feature importance...")
    print("-" * 70)
    
    feature_importance = {}
    scores = iso_forest.score_samples(X_test)
    
    for i, feature in enumerate(feature_names):
        # Simple correlation between feature and anomaly score
        feature_values = X_test[:, i]
        correlation = np.corrcoef(feature_values, scores)[0, 1]
        feature_importance[feature] = abs(correlation)
    
    # Sort by importance
    sorted_features = sorted(
        feature_importance.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    print("Top 10 most important features:")
    for feature, importance in sorted_features[:10]:
        print(f"  {feature:30s}: {importance:.4f}")
    
    # Save feature importance
    importance_path = output_path / 'feature_importance.joblib'
    joblib.dump(feature_importance, importance_path)
    print(f"\n✓ Feature importance saved to: {importance_path}\n")
    
    # Ensemble evaluation
    print("=" * 70)
    print("ENSEMBLE EVALUATION")
    print("=" * 70)
    
    # Combine predictions (voting)
    ensemble_pred = ((y_pred_if == -1) | (y_pred_lof == -1)).astype(int)
    ensemble_anomalies = ensemble_pred.sum()
    
    print(f"Ensemble anomalies: {ensemble_anomalies:,} ({ensemble_anomalies/len(X_test)*100:.2f}%)")
    print("\nTraining completed successfully!")
    print(f"All models saved to: {output_path.absolute()}\n")
    
    # Save metadata
    metadata = {
        'training_date': datetime.now().isoformat(),
        'n_samples': len(df),
        'n_features': X.shape[1],
        'feature_names': feature_names,
        'test_anomalies': {
            'isolation_forest': int(anomaly_count_if),
            'lof': int(anomaly_count_lof),
            'ensemble': int(ensemble_anomalies)
        },
        'models': {
            'isolation_forest': str(if_path),
            'lof': str(lof_path),
            'feature_engineer': str(engineer_path)
        }
    }
    
    import json
    metadata_path = output_path / 'training_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Training metadata saved to: {metadata_path}")
    
    return metadata


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(
        description='Train anomaly detection models for real estate transactions'
    )
    parser.add_argument(
        '--data',
        type=str,
        default=None,
        help='Path to training data (CSV or Parquet)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='./ml/models',
        help='Output directory for trained models'
    )
    
    args = parser.parse_args()
    
    try:
        train_models(data_path=args.data, output_dir=args.output)
        print("\n✓ Training pipeline completed successfully!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n✗ Error during training: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
