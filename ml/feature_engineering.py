import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, Any
from pathlib import Path

from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib


class FeatureEngineer:
    """
    Feature engineering for real estate transaction data.
    
    Transforms raw transaction data into ML-ready features.
    """
    
    def __init__(self):
        """Initialize feature engineer with encoders and scalers."""
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.is_fitted = False
    
    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, list]:
        """
        Fit feature engineering pipeline and transform data.
        
        Args:
            df: Raw transaction DataFrame
            
        Returns:
            Tuple of (features array, feature names)
        """
        # Create features
        features_df = self._create_features(df)
        
        # Fit label encoders for categorical features
        categorical_cols = [
            'tipo_acto', 'tipo_predio', 'estado_folio',
            'departamento', 'municipio'
        ]
        
        for col in categorical_cols:
            if col in features_df.columns:
                self.label_encoders[col] = LabelEncoder()
                features_df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(
                    features_df[col].astype(str)
                )
        
        # Select numerical features
        numerical_features = self._select_numerical_features(features_df)
        
        # Fit and transform scaler
        scaled_features = self.scaler.fit_transform(numerical_features)
        
        self.feature_names = numerical_features.columns.tolist()
        self.is_fitted = True
        
        return scaled_features, self.feature_names
    
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        Transform new data using fitted pipeline.
        
        Args:
            df: Raw transaction DataFrame
            
        Returns:
            Transformed features array
        """
        if not self.is_fitted:
            raise ValueError("FeatureEngineer must be fitted before transform")
        
        # Create features
        features_df = self._create_features(df)
        
        # Encode categorical features
        for col, encoder in self.label_encoders.items():
            if col in features_df.columns:
                # Handle unseen labels
                features_df[f'{col}_encoded'] = features_df[col].apply(
                    lambda x: encoder.transform([str(x)])[0] 
                    if str(x) in encoder.classes_ 
                    else -1
                )
        
        # Select numerical features
        numerical_features = self._select_numerical_features(features_df)
        
        # Ensure same columns as training
        for col in self.feature_names:
            if col not in numerical_features.columns:
                numerical_features[col] = 0
        
        numerical_features = numerical_features[self.feature_names]
        
        # Transform
        scaled_features = self.scaler.transform(numerical_features)
        
        return scaled_features
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create engineered features from raw data."""
        features = df.copy()
        
        # Temporal features
        if 'fecha_acto' in features.columns:
            features['fecha_acto'] = pd.to_datetime(features['fecha_acto'])
            features['year'] = features['fecha_acto'].dt.year
            features['month'] = features['fecha_acto'].dt.month
            features['day_of_week'] = features['fecha_acto'].dt.dayofweek
            features['quarter'] = features['fecha_acto'].dt.quarter
            features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Value-based features
        if 'valor_acto' in features.columns:
            features['log_valor'] = np.log1p(features['valor_acto'])
            features['valor_millions'] = features['valor_acto'] / 1_000_000
        
        # Area-based features
        if 'area_terreno' in features.columns and 'area_construida' in features.columns:
            features['area_terreno'] = features['area_terreno'].fillna(0)
            features['area_construida'] = features['area_construida'].fillna(0)
            
            # Avoid division by zero
            features['construction_ratio'] = np.where(
                features['area_terreno'] > 0,
                features['area_construida'] / features['area_terreno'],
                0
            )
            
            features['valor_m2_terreno'] = np.where(
                features['area_terreno'] > 0,
                features['valor_acto'] / features['area_terreno'],
                0
            )
            
            features['valor_m2_construida'] = np.where(
                features['area_construida'] > 0,
                features['valor_acto'] / features['area_construida'],
                0
            )
        
        # Intervinientes features
        if 'numero_intervinientes' in features.columns:
            features['multiple_intervinientes'] = (
                features['numero_intervinientes'] > 2
            ).astype(int)
            features['many_intervinientes'] = (
                features['numero_intervinientes'] > 5
            ).astype(int)
        
        # Missing data indicators
        features['missing_catastral'] = (
            features['numero_catastral'].isna()
        ).astype(int) if 'numero_catastral' in features.columns else 0
        
        features['missing_areas'] = (
            (features['area_terreno'] == 0) | 
            (features['area_construida'] == 0)
        ).astype(int) if 'area_terreno' in features.columns else 0
        
        return features
    
    def _select_numerical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select only numerical features for modeling."""
        numerical_cols = [
            'valor_acto', 'log_valor', 'valor_millions',
            'numero_intervinientes',
            'year', 'month', 'day_of_week', 'quarter', 'is_weekend',
            'area_terreno', 'area_construida',
            'construction_ratio', 'valor_m2_terreno', 'valor_m2_construida',
            'multiple_intervinientes', 'many_intervinientes',
            'missing_catastral', 'missing_areas',
            'tipo_acto_encoded', 'tipo_predio_encoded', 'estado_folio_encoded',
            'departamento_encoded', 'municipio_encoded'
        ]
        
        # Select only existing columns
        available_cols = [col for col in numerical_cols if col in df.columns]
        
        return df[available_cols].fillna(0)
    
    def save(self, path: str):
        """Save feature engineer to disk."""
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        joblib.dump({
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'is_fitted': self.is_fitted
        }, save_path)
    
    @classmethod
    def load(cls, path: str) -> 'FeatureEngineer':
        """Load feature engineer from disk."""
        data = joblib.load(path)
        
        engineer = cls()
        engineer.scaler = data['scaler']
        engineer.label_encoders = data['label_encoders']
        engineer.feature_names = data['feature_names']
        engineer.is_fitted = data['is_fitted']
        
        return engineer


def create_sample_dataset(n_samples: int = 10000) -> pd.DataFrame:
    """
    Create synthetic sample dataset for testing.
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        DataFrame with synthetic transaction data
    """
    np.random.seed(42)
    
    # Colombian departments
    departamentos = [
        'CUNDINAMARCA', 'ANTIOQUIA', 'VALLE DEL CAUCA', 'ATLANTICO',
        'BOLIVAR', 'SANTANDER', 'TOLIMA', 'CALDAS'
    ]
    
    # Types
    tipos_acto = ['compraventa', 'hipoteca', 'donacion', 'permuta', 'otro']
    tipos_predio = ['urbano', 'rural', 'mixto']
    estados_folio = ['activo', 'cancelado', 'cerrado']
    
    data = {
        'valor_acto': np.random.lognormal(19, 0.8, n_samples),  # ~200M COP mean
        'tipo_acto': np.random.choice(tipos_acto, n_samples),
        'fecha_acto': pd.date_range('2020-01-01', periods=n_samples, freq='H'),
        'departamento': np.random.choice(departamentos, n_samples),
        'municipio': np.random.choice(['BOGOTA', 'MEDELLIN', 'CALI'], n_samples),
        'tipo_predio': np.random.choice(tipos_predio, n_samples),
        'numero_intervinientes': np.random.randint(1, 8, n_samples),
        'estado_folio': np.random.choice(estados_folio, n_samples, p=[0.9, 0.05, 0.05]),
        'area_terreno': np.random.exponential(150, n_samples),
        'area_construida': np.random.exponential(100, n_samples),
        'numero_catastral': [f'CAT{i:020d}' for i in range(n_samples)]
    }
    
    df = pd.DataFrame(data)
    
    # Add some anomalies (10%)
    n_anomalies = int(n_samples * 0.1)
    anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
    
    # Type 1: Very low values
    df.loc[anomaly_indices[:n_anomalies//3], 'valor_acto'] *= 0.1
    
    # Type 2: Many intervinientes
    df.loc[anomaly_indices[n_anomalies//3:2*n_anomalies//3], 'numero_intervinientes'] = 15
    
    # Type 3: Canceled folios with high values
    df.loc[anomaly_indices[2*n_anomalies//3:], 'estado_folio'] = 'cancelado'
    
    return df
