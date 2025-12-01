import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List, Tuple
import joblib
from pathlib import Path
from datetime import datetime

from api.schemas import (
    TransactionInput, 
    AnomalyAnalysisResult, 
    RiskLevel,
    ContributingFeature,
    TipoActo,
    TipoPredio,
    EstadoFolio
)
from core.logger import get_logger
from core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class AnomalyDetector:
    """
    Ensemble anomaly detection model for real estate transactions.
    
    Combines Isolation Forest, Local Outlier Factor, and statistical methods.
    """
    
    def __init__(self, model_path: str = None):
        """Initialize the anomaly detector."""
        self.model_path = model_path or settings.model_path
        self.scaler = StandardScaler()
        self.isolation_forest = None
        self.lof = None
        self.feature_importance = {}
        self.is_trained = False
        
        # Try to load existing models
        self._load_models()
        
        if not self.is_trained:
            logger.warning("models_not_loaded", message="Using default models")
            self._initialize_default_models()
    
    def _initialize_default_models(self):
        """Initialize models with default parameters."""
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1
        )
        
        self.lof = LocalOutlierFactor(
            n_neighbors=20,
            contamination=0.1,
            novelty=True,
            n_jobs=-1
        )
        
        logger.info("default_models_initialized")
    
    def _load_models(self):
        """Load trained models from disk."""
        try:
            model_dir = Path(self.model_path)
            
            if (model_dir / "isolation_forest.joblib").exists():
                self.isolation_forest = joblib.load(model_dir / "isolation_forest.joblib")
                logger.info("isolation_forest_loaded")
            
            if (model_dir / "lof.joblib").exists():
                self.lof = joblib.load(model_dir / "lof.joblib")
                logger.info("lof_loaded")
            
            if (model_dir / "scaler.joblib").exists():
                self.scaler = joblib.load(model_dir / "scaler.joblib")
                logger.info("scaler_loaded")
            
            if (model_dir / "feature_importance.joblib").exists():
                self.feature_importance = joblib.load(model_dir / "feature_importance.joblib")
                logger.info("feature_importance_loaded")
            
            self.is_trained = all([
                self.isolation_forest is not None,
                self.lof is not None
            ])
            
        except Exception as e:
            logger.error("model_load_error", error=str(e))
            self.is_trained = False
    
    def prepare_features(self, transaction: TransactionInput) -> np.ndarray:
        """
        Convert transaction to feature vector for model input.
        
        Features:
        - valor_acto (normalized)
        - tipo_acto (encoded)
        - fecha_acto (temporal features)
        - departamento/municipio (encoded)
        - tipo_predio (encoded)
        - numero_intervinientes
        - estado_folio (encoded)
        - area metrics (if available)
        """
        features = {}
        
        # Numerical features
        features['valor_acto'] = float(transaction.valor_acto)
        features['numero_intervinientes'] = float(transaction.numero_intervinientes)
        
        # Temporal features
        features['year'] = float(transaction.fecha_acto.year)
        features['month'] = float(transaction.fecha_acto.month)
        features['day_of_week'] = float(transaction.fecha_acto.weekday())
        
        # Categorical features (one-hot encoding)
        tipo_acto_map = {
            TipoActo.COMPRAVENTA: 1.0,
            TipoActo.HIPOTECA: 2.0,
            TipoActo.DONACION: 3.0,
            TipoActo.PERMUTA: 4.0,
            TipoActo.DACION_PAGO: 5.0,
            TipoActo.ADJUDICACION: 6.0,
            TipoActo.SUCESION: 7.0,
            TipoActo.OTRO: 8.0
        }
        features['tipo_acto_encoded'] = tipo_acto_map.get(transaction.tipo_acto, 0.0)
        
        tipo_predio_map = {
            TipoPredio.URBANO: 1.0,
            TipoPredio.RURAL: 2.0,
            TipoPredio.MIXTO: 3.0
        }
        features['tipo_predio_encoded'] = tipo_predio_map.get(transaction.tipo_predio, 0.0)
        
        estado_folio_map = {
            EstadoFolio.ACTIVO: 1.0,
            EstadoFolio.CANCELADO: 2.0,
            EstadoFolio.CERRADO: 3.0,
            EstadoFolio.SUSPENDIDO: 4.0
        }
        features['estado_folio_encoded'] = estado_folio_map.get(transaction.estado_folio, 0.0)
        
        # Area features (with defaults)
        features['area_terreno'] = float(transaction.area_terreno or 0)
        features['area_construida'] = float(transaction.area_construida or 0)
        
        # Derived features
        if transaction.area_construida and transaction.area_construida > 0:
            features['valor_m2'] = features['valor_acto'] / transaction.area_construida
        else:
            features['valor_m2'] = 0.0
        
        # Location hash (simple encoding)
        location_str = f"{transaction.departamento}_{transaction.municipio}"
        features['location_hash'] = float(hash(location_str) % 1000)
        
        # Convert to array
        feature_array = np.array([
            features['valor_acto'],
            features['numero_intervinientes'],
            features['year'],
            features['month'],
            features['day_of_week'],
            features['tipo_acto_encoded'],
            features['tipo_predio_encoded'],
            features['estado_folio_encoded'],
            features['area_terreno'],
            features['area_construida'],
            features['valor_m2'],
            features['location_hash']
        ]).reshape(1, -1)
        
        return feature_array
    
    def predict_anomaly(
        self, 
        features: np.ndarray, 
        transaction: TransactionInput
    ) -> AnomalyAnalysisResult:
        """
        Predict anomaly score and classification for a transaction.
        
        Returns detailed analysis with contributing features and recommendations.
        """
        try:
            # Get predictions from ensemble
            if_score = self._get_isolation_forest_score(features)
            lof_score = self._get_lof_score(features)
            stat_score = self._get_statistical_score(transaction)
            
            # Ensemble score (weighted average)
            anomaly_score = (
                0.4 * if_score +
                0.3 * lof_score +
                0.3 * stat_score
            )
            
            # Classify risk level
            classification = self._classify_risk(anomaly_score)
            
            # Get contributing features
            contributing_features = self._get_contributing_features(
                features, transaction, anomaly_score
            )
            
            # Generate explanation
            explanation = self._generate_explanation(
                transaction, classification, contributing_features
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                classification, contributing_features
            )
            
            return AnomalyAnalysisResult(
                anomaly_score=float(anomaly_score),
                classification=classification,
                contributing_features=contributing_features,
                confidence=0.85,  # TODO: Calculate actual confidence
                explanation=explanation,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error("prediction_error", error=str(e))
            raise
    
    def _get_isolation_forest_score(self, features: np.ndarray) -> float:
        """Get anomaly score from Isolation Forest."""
        if self.isolation_forest is None:
            return 0.5
        
        try:
            # Isolation Forest returns -1 for outliers, 1 for inliers
            # Convert to 0-1 score where 1 is most anomalous
            score = self.isolation_forest.score_samples(features)[0]
            # Normalize to 0-1 range
            normalized_score = 1 / (1 + np.exp(score))
            return float(normalized_score)
        except:
            return 0.5
    
    def _get_lof_score(self, features: np.ndarray) -> float:
        """Get anomaly score from Local Outlier Factor."""
        if self.lof is None:
            return 0.5
        
        try:
            score = self.lof.score_samples(features)[0]
            # Convert to 0-1 range
            normalized_score = 1 / (1 + np.exp(score))
            return float(normalized_score)
        except:
            return 0.5
    
    def _get_statistical_score(self, transaction: TransactionInput) -> float:
        """Calculate statistical anomaly score based on business rules."""
        score = 0.0
        
        # Check for unusually low values
        if transaction.valor_acto < 10_000_000:  # < 10M COP
            score += 0.3
        
        # Check for unusually high values
        if transaction.valor_acto > 5_000_000_000:  # > 5B COP
            score += 0.2
        
        # Check for many intervinientes
        if transaction.numero_intervinientes > 5:
            score += 0.2
        
        # Check for suspicious states
        if transaction.estado_folio in [EstadoFolio.CANCELADO, EstadoFolio.SUSPENDIDO]:
            score += 0.3
        
        return min(score, 1.0)
    
    def _classify_risk(self, score: float) -> RiskLevel:
        """Classify risk level based on anomaly score."""
        threshold = settings.anomaly_threshold
        
        if score >= threshold:
            return RiskLevel.HIGH_RISK
        elif score >= threshold * 0.6:
            return RiskLevel.SUSPICIOUS
        else:
            return RiskLevel.NORMAL
    
    def _get_contributing_features(
        self,
        features: np.ndarray,
        transaction: TransactionInput,
        score: float
    ) -> List[ContributingFeature]:
        """Identify top contributing features to the anomaly."""
        contributions = []
        
        # Valor analysis
        if transaction.valor_acto < 50_000_000:
            contributions.append(ContributingFeature(
                feature_name="valor_acto",
                value=transaction.valor_acto,
                contribution_score=0.4,
                explanation="Valor significativamente inferior al mercado"
            ))
        
        # Intervinientes analysis
        if transaction.numero_intervinientes > 3:
            contributions.append(ContributingFeature(
                feature_name="numero_intervinientes",
                value=transaction.numero_intervinientes,
                contribution_score=0.3,
                explanation="Número inusual de intervinientes en la transacción"
            ))
        
        # Estado folio analysis
        if transaction.estado_folio != EstadoFolio.ACTIVO:
            contributions.append(ContributingFeature(
                feature_name="estado_folio",
                value=transaction.estado_folio.value,
                contribution_score=0.25,
                explanation="Estado del folio requiere verificación"
            ))
        
        # Sort by contribution and return top 5
        contributions.sort(key=lambda x: x.contribution_score, reverse=True)
        return contributions[:5]
    
    def _generate_explanation(
        self,
        transaction: TransactionInput,
        classification: RiskLevel,
        contributing_features: List[ContributingFeature]
    ) -> str:
        """Generate human-readable explanation of the analysis."""
        if classification == RiskLevel.NORMAL:
            return f"Transacción normal de {transaction.tipo_acto.value} en {transaction.municipio}. No se detectaron anomalías significativas."
        
        feature_desc = ", ".join([f.feature_name for f in contributing_features[:3]])
        
        if classification == RiskLevel.HIGH_RISK:
            return f"Transacción de ALTO RIESGO detectada. Factores principales: {feature_desc}. Se recomienda revisión manual inmediata."
        
        return f"Transacción SOSPECHOSA. Revisar: {feature_desc}. Validación adicional recomendada."
    
    def _generate_recommendations(
        self,
        classification: RiskLevel,
        contributing_features: List[ContributingFeature]
    ) -> List[str]:
        """Generate actionable recommendations."""
        if classification == RiskLevel.NORMAL:
            return ["Transacción dentro de parámetros normales"]
        
        recommendations = [
            "Verificar identidad de todos los intervinientes",
            "Solicitar avalúo catastral actualizado"
        ]
        
        if classification == RiskLevel.HIGH_RISK:
            recommendations.extend([
                "Revisión manual obligatoria antes de registro",
                "Verificar origen de fondos",
                "Consultar antecedentes registrales"
            ])
        
        return recommendations
