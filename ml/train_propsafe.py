"""
Model Training para PropSafe AI
Entrena ensemble de Isolation Forest + LOF con 5.7M registros
Optimizado para CPU (t3.small compatible)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging
import joblib

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PropSafeAnomalyDetector:
    """
    Detector de anomalías con ensemble de Isolation Forest + LOF.
    """
    
    def __init__(
        self,
        contamination: float = 0.1,  # 10% esperado como anomalías
        n_estimators: int = 100,
        max_samples: int = 10000,  # Para acelerar IF
        n_neighbors: int = 20,
        random_state: int = 42
    ):
        """
        Inicializa detectores.
        
        Args:
            contamination: Proporción esperada de anomalías
            n_estimators: Número de árboles en Isolation Forest
            max_samples: Muestras por árbol (menor = más rápido)
            n_neighbors: Vecinos para LOF
            random_state: Semilla aleatoria
        """
        self.contamination = contamination
        self.random_state = random_state
        
        logger.info("Inicializando modelos...")
        logger.info(f"  Contamination: {contamination}")
        logger.info(f"  IF estimators: {n_estimators}")
        logger.info(f"  IF max_samples: {max_samples}")
        logger.info(f"  LOF neighbors: {n_neighbors}")
        
        # Isolation Forest
        self.iso_forest = IsolationForest(
            n_estimators=n_estimators,
            max_samples=max_samples,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,  # Usar todos los cores
            verbose=0
        )
        
        # Local Outlier Factor
        self.lof = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            novelty=True,  # Para predict en datos nuevos
            n_jobs=-1
        )
        
        # Scaler para normalización
        self.scaler = StandardScaler()
        
        self.is_fitted = False
        self.feature_names = []
    
    def fit(self, X: np.ndarray, feature_names: list = None):
        """
        Entrena ambos modelos.
        
        Args:
            X: Features array
            feature_names: Nombres de las features
        """
        logger.info(f"Entrenando con {len(X):,} muestras y {X.shape[1]} features")
        
        # Guardar nombres de features
        if feature_names:
            self.feature_names = feature_names
        
        # Normalizar
        logger.info("Normalizando features...")
        X_scaled = self.scaler.fit_transform(X)
        
        # Entrenar Isolation Forest
        logger.info("Entrenando Isolation Forest...")
        start = datetime.now()
        self.iso_forest.fit(X_scaled)
        if_time = (datetime.now() - start).total_seconds()
        logger.info(f"  ✓ IF entrenado en {if_time:.1f}s")
        
        # Entrenar LOF
        logger.info("Entrenando Local Outlier Factor...")
        start = datetime.now()
        self.lof.fit(X_scaled)
        lof_time = (datetime.now() - start).total_seconds()
        logger.info(f"  ✓ LOF entrenado en {lof_time:.1f}s")
        
        self.is_fitted = True
        logger.info("✓ Entrenamiento completado")
    
    def predict(self, X: np.ndarray) -> dict:
        """
        Predice anomalías y genera scores.
        
        Args:
            X: Features array
            
        Returns:
            Dict con scores y predicciones
        """
        if not self.is_fitted:
            raise ValueError("Modelo no entrenado")
        
        # Normalizar
        X_scaled = self.scaler.transform(X)
        
        # Predicciones de IF (1 = normal, -1 = anomalía)
        if_pred = self.iso_forest.predict(X_scaled)
        if_scores = self.iso_forest.decision_function(X_scaled)
        
        # Predicciones de LOF (1 = normal, -1 = anomalía)
        lof_pred = self.lof.predict(X_scaled)
        lof_scores = -self.lof.decision_function(X_scaled)  # Negativo para coherencia
        
        # Normalizar scores a [0, 1]
        if_scores_norm = self._normalize_scores(if_scores)
        lof_scores_norm = self._normalize_scores(lof_scores)
        
        # Ensemble: promedio ponderado
        # IF tiene más peso porque es más robusto
        ensemble_scores = 0.6 * if_scores_norm + 0.4 * lof_scores_norm
        
        # Clasificación por umbrales
        classifications = self._classify_risk(ensemble_scores)
        
        return {
            'anomaly_scores': ensemble_scores,
            'classifications': classifications,
            'if_scores': if_scores_norm,
            'lof_scores': lof_scores_norm,
            'if_predictions': if_pred,
            'lof_predictions': lof_pred
        }
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normaliza scores a rango [0, 1]."""
        # Usar percentiles para manejar outliers
        p5, p95 = np.percentile(scores, [5, 95])
        scores_clipped = np.clip(scores, p5, p95)
        
        # Min-max normalization
        score_min = scores_clipped.min()
        score_max = scores_clipped.max()
        
        if score_max - score_min > 0:
            normalized = (scores_clipped - score_min) / (score_max - score_min)
        else:
            normalized = np.zeros_like(scores)
        
        return normalized
    
    def _classify_risk(self, scores: np.ndarray) -> np.ndarray:
        """
        Clasifica en 3 niveles de riesgo.
        
        Returns:
            Array con 0 = normal, 1 = sospechoso, 2 = alto riesgo
        """
        classifications = np.zeros(len(scores), dtype=int)
        classifications[scores >= 0.4] = 1  # Sospechoso
        classifications[scores >= 0.7] = 2  # Alto riesgo
        return classifications
    
    def evaluate(self, X: np.ndarray, y_true: np.ndarray) -> dict:
        """
        Evalúa el modelo si hay etiquetas verdaderas.
        
        Args:
            X: Features
            y_true: Etiquetas verdaderas (0 = normal, 1 = anomalía)
            
        Returns:
            Dict con métricas
        """
        results = self.predict(X)
        y_pred = (results['anomaly_scores'] >= 0.5).astype(int)
        
        cm = confusion_matrix(y_true, y_pred)
        report = classification_report(y_true, y_pred, output_dict=True)
        
        return {
            'confusion_matrix': cm,
            'classification_report': report,
            'accuracy': report['accuracy'],
            'precision': report['1']['precision'],
            'recall': report['1']['recall'],
            'f1_score': report['1']['f1-score']
        }
    
    def save(self, path: str):
        """Guarda modelo entrenado."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'iso_forest': self.iso_forest,
            'lof': self.lof,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'contamination': self.contamination,
            'is_fitted': self.is_fitted
        }
        
        joblib.dump(model_data, path)
        logger.info(f"Modelo guardado en: {path}")
        logger.info(f"Tamaño: {path.stat().st_size / 1024 / 1024:.2f} MB")
    
    @classmethod
    def load(cls, path: str) -> 'PropSafeAnomalyDetector':
        """Carga modelo entrenado."""
        model_data = joblib.load(path)
        
        detector = cls(contamination=model_data['contamination'])
        detector.iso_forest = model_data['iso_forest']
        detector.lof = model_data['lof']
        detector.scaler = model_data['scaler']
        detector.feature_names = model_data['feature_names']
        detector.is_fitted = model_data['is_fitted']
        
        return detector


def train_model(
    features_file: str,
    output_dir: str = 'ml/models',
    sample_size: int = None,
    contamination: float = 0.1
):
    """
    Entrena modelo desde archivo de features.
    
    Args:
        features_file: Path a ml_features.parquet
        output_dir: Directorio de salida para modelos
        sample_size: Si se especifica, usar solo N muestras (para pruebas rápidas)
        contamination: Proporción esperada de anomalías
    """
    logger.info("="*60)
    logger.info("PropSafe AI - Model Training")
    logger.info("="*60)
    
    # Cargar features
    logger.info(f"Cargando features desde {features_file}")
    df = pd.read_parquet(features_file)
    logger.info(f"Datos cargados: {len(df):,} registros, {len(df.columns)} columnas")
    
    # Sample si se especifica
    if sample_size and sample_size < len(df):
        logger.info(f"Usando muestra de {sample_size:,} registros")
        df = df.sample(n=sample_size, random_state=42)
    
    # Separar transaction_id y features
    transaction_ids = df['transaction_id'].values
    feature_cols = [col for col in df.columns if col != 'transaction_id']
    X = df[feature_cols].values
    
    logger.info(f"Features para entrenamiento: {len(feature_cols)}")
    
    # Crear y entrenar modelo
    start_time = datetime.now()
    
    detector = PropSafeAnomalyDetector(
        contamination=contamination,
        n_estimators=100,
        max_samples=10000,
        n_neighbors=20,
        random_state=42
    )
    
    detector.fit(X, feature_names=feature_cols)
    
    train_time = (datetime.now() - start_time).total_seconds()
    
    # Hacer predicciones en el dataset de entrenamiento
    logger.info("Generando predicciones...")
    results = detector.predict(X)
    
    # Estadísticas
    scores = results['anomaly_scores']
    classifications = results['classifications']
    
    normal_count = (classifications == 0).sum()
    suspicious_count = (classifications == 1).sum()
    high_risk_count = (classifications == 2).sum()
    
    logger.info("="*60)
    logger.info("Estadísticas del modelo:")
    logger.info("="*60)
    logger.info(f"Registros procesados: {len(scores):,}")
    logger.info(f"Normal: {normal_count:,} ({normal_count/len(scores)*100:.1f}%)")
    logger.info(f"Sospechoso: {suspicious_count:,} ({suspicious_count/len(scores)*100:.1f}%)")
    logger.info(f"Alto riesgo: {high_risk_count:,} ({high_risk_count/len(scores)*100:.1f}%)")
    logger.info(f"Tiempo de entrenamiento: {train_time:.1f}s")
    logger.info("="*60)
    
    # Guardar modelo
    output_path = Path(output_dir) / 'propsafe_anomaly_model.joblib'
    detector.save(output_path)
    
    # Guardar predicciones
    results_df = pd.DataFrame({
        'transaction_id': transaction_ids,
        'anomaly_score': scores,
        'risk_classification': classifications,
        'if_score': results['if_scores'],
        'lof_score': results['lof_scores']
    })
    
    results_path = Path(output_dir) / 'training_predictions.parquet'
    results_df.to_parquet(results_path, compression='snappy', index=False)
    logger.info(f"Predicciones guardadas en: {results_path}")
    
    logger.info("="*60)
    logger.info("✓ Entrenamiento completado exitosamente")
    logger.info("="*60)
    
    return detector, results_df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Entrenar modelo de detección de anomalías')
    parser.add_argument(
        '--features',
        default='data/clean/ml_features.parquet',
        help='Archivo de features'
    )
    parser.add_argument(
        '--output',
        default='ml/models',
        help='Directorio de salida'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help='Tamaño de muestra (None = usar todo)'
    )
    parser.add_argument(
        '--contamination',
        type=float,
        default=0.1,
        help='Proporción esperada de anomalías (0.0-0.5)'
    )
    
    args = parser.parse_args()
    
    train_model(
        features_file=args.features,
        output_dir=args.output,
        sample_size=args.sample,
        contamination=args.contamination
    )
