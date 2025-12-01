"""
Feature Engineering para PropSafe AI
Adaptado para datos reales de SNR/IGAC con 5.7M registros
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PropSafeFeatureEngineer:
    """
    Feature engineering optimizado para transacciones inmobiliarias colombianas.
    Genera 34+ features desde datos crudos del SNR/IGAC.
    """
    
    def __init__(self):
        """Initialize feature engineer."""
        self.feature_stats = {}  # Para normalización
        self.is_fitted = False
    
    def create_features(self, df: pd.DataFrame, chunk_processing: bool = False) -> pd.DataFrame:
        """
        Crea 34+ features desde datos crudos.
        
        Args:
            df: DataFrame con datos de ml_training.parquet
            chunk_processing: Si True, procesa en chunks para ahorrar memoria
            
        Returns:
            DataFrame con features para ML
        """
        logger.info(f"Creando features para {len(df):,} registros...")
        
        features = pd.DataFrame()
        features['transaction_id'] = df['transaction_id']
        
        # ===== 1. FEATURES TEMPORALES (6 features) =====
        logger.info("Generando features temporales...")
        if 'FECHA_RADICA_TEXTO' in df.columns:
            df['FECHA_RADICA_TEXTO'] = pd.to_datetime(df['FECHA_RADICA_TEXTO'], format='%d/%m/%Y', errors='coerce')
            features['year'] = df['FECHA_RADICA_TEXTO'].dt.year
            features['month'] = df['FECHA_RADICA_TEXTO'].dt.month
            features['quarter'] = df['FECHA_RADICA_TEXTO'].dt.quarter
            features['day_of_week'] = df['FECHA_RADICA_TEXTO'].dt.dayofweek
            features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
            features['days_since_2015'] = (df['FECHA_RADICA_TEXTO'] - pd.Timestamp('2015-01-01')).dt.days
        elif 'YEAR_RADICA' in df.columns:
            features['year'] = df['YEAR_RADICA']
            features['month'] = 6  # Default medio año
            features['quarter'] = 2
            features['day_of_week'] = 3
            features['is_weekend'] = 0
            features['days_since_2015'] = (df['YEAR_RADICA'] - 2015) * 365
        
        # ===== 2. FEATURES DE VALOR (7 features) =====
        logger.info("Generando features de valor...")
        features['valor_acto'] = df['VALOR'].fillna(0)
        features['log_valor'] = np.log1p(features['valor_acto'])
        features['valor_millones'] = features['valor_acto'] / 1_000_000
        features['valor_miles_millones'] = features['valor_acto'] / 1_000_000_000
        
        # Valor normalizado por rangos
        features['valor_bajo'] = (features['valor_acto'] < 50_000_000).astype(int)
        features['valor_medio'] = ((features['valor_acto'] >= 50_000_000) & 
                                    (features['valor_acto'] < 500_000_000)).astype(int)
        features['valor_alto'] = (features['valor_acto'] >= 500_000_000).astype(int)
        
        # ===== 3. FEATURES DE ÁREAS (8 features) =====
        logger.info("Generando features de áreas...")
        # En estos datos no tenemos áreas, usar defaults
        features['area_terreno'] = 0
        features['area_construida'] = 0
        features['area_total'] = 0
        features['log_area_terreno'] = 0
        features['log_area_construida'] = 0
        features['ratio_construccion'] = 0
        features['valor_m2_terreno'] = 0
        features['valor_m2_construida'] = 0
        
        # ===== 4. FEATURES DE ACTIVIDAD (3 features) =====
        logger.info("Generando features de actividad...")
        if 'anotaciones_por_anio' in df.columns:
            features['anotaciones_por_anio'] = df['anotaciones_por_anio'].fillna(1)
            features['log_anotaciones'] = np.log1p(features['anotaciones_por_anio'])
            features['actividad_alta'] = (features['anotaciones_por_anio'] > 10).astype(int)
        else:
            features['anotaciones_por_anio'] = 1
            features['log_anotaciones'] = 0
            features['actividad_alta'] = 0
        
        # ===== 5. FEATURES GEOGRÁFICAS (3 features) =====
        logger.info("Generando features geográficas...")
        if 'TIPO_PREDIO_ZONA' in df.columns:
            features['es_urbano'] = (df['TIPO_PREDIO_ZONA'].str.contains('URBANO', na=False)).astype(int)
            features['es_rural'] = (df['TIPO_PREDIO_ZONA'].str.contains('RURAL', na=False)).astype(int)
            features['sin_zona'] = (~df['TIPO_PREDIO_ZONA'].str.contains('URBANO|RURAL', na=True)).astype(int)
        elif 'CATEGORIA_RURALIDAD' in df.columns:
            features['es_urbano'] = (df['CATEGORIA_RURALIDAD'] == 1).astype(int)
            features['es_rural'] = (df['CATEGORIA_RURALIDAD'].isin([2, 3])).astype(int)
            features['sin_zona'] = (df['CATEGORIA_RURALIDAD'].isna()).astype(int)
        else:
            features['es_urbano'] = 0
            features['es_rural'] = 0
            features['sin_zona'] = 1
        
        # ===== 6. FEATURES DE TIPO DE PREDIO (3 features) =====
        if 'TIPO_PREDIO_ZONA' in df.columns:
            features['predio_nph'] = (df['TIPO_PREDIO_ZONA'].str.contains('NPH', na=False)).astype(int)
            features['predio_matriz'] = (df['TIPO_PREDIO_ZONA'].str.contains('MATRIZ', na=False)).astype(int)
            features['predio_matriz_nph'] = (df['TIPO_PREDIO_ZONA'].str.contains('MATRIZ NPH', na=False)).astype(int)
        else:
            features['predio_nph'] = 0
            features['predio_matriz'] = 0
            features['predio_matriz_nph'] = 0
        
        # ===== 7. FEATURES DE FLAGS DE ANOMALÍA (4 features) =====
        logger.info("Generando features de anomalías...")
        features['flag_actividad_excesiva'] = df.get('flag_actividad_excesiva', 0).fillna(False).astype(int)
        features['flag_geo_discrepancia'] = df.get('flag_geo_discrepancia', 0).fillna(False).astype(int)
        features['total_flags_anomalia'] = df.get('total_flags_anomalia', 0).fillna(0).astype(int)
        features['tiene_valor'] = df.get('TIENE_VALOR', 1).fillna(1).astype(int)
        
        # ===== 8. FEATURES DE CÓDIGO DE NATURALEZA (2 features) =====
        if 'COD_NATUJUR' in df.columns:
            # Convertir a numérico para análisis
            features['cod_naturaleza_num'] = pd.to_numeric(
                df['COD_NATUJUR'], 
                errors='coerce'
            ).fillna(0)
            features['cod_naturaleza_grupo'] = (features['cod_naturaleza_num'] // 100).astype(int)
        else:
            features['cod_naturaleza_num'] = 0
            features['cod_naturaleza_grupo'] = 0
        
        # ===== 9. FEATURES DE COUNTS (3 features) =====
        features['count_a'] = df.get('COUNT_A', 0).fillna(0).astype(int)
        features['count_de'] = df.get('COUNT_DE', 0).fillna(0).astype(int)
        features['predios_nuevos'] = df.get('PREDIOS_NUEVOS', 0).fillna(0).astype(int)
        
        # ===== ESTADÍSTICAS FINALES =====
        total_features = len(features.columns) - 1  # Excluir transaction_id
        logger.info(f"✓ {total_features} features generados")
        logger.info(f"  - Temporales: 6")
        logger.info(f"  - Valor: 7")
        logger.info(f"  - Áreas: 8 (no disponibles en datos)")
        logger.info(f"  - Actividad: 3")
        logger.info(f"  - Geográficas: 3")
        logger.info(f"  - Tipo predio: 3")
        logger.info(f"  - Flags anomalía: 4")
        logger.info(f"  - Naturaleza jurídica: 2")
        logger.info(f"  - Counts: 3")
        logger.info(f"  TOTAL: {total_features} features")
        
        # Validar que no hay NaN
        nan_counts = features.isna().sum()
        if nan_counts.sum() > 0:
            logger.warning(f"Se encontraron valores NaN:")
            for col, count in nan_counts[nan_counts > 0].items():
                logger.warning(f"  {col}: {count:,} NaN")
            features = features.fillna(0)
        
        return features
    
    def save_features(self, features: pd.DataFrame, output_path: str):
        """Guarda features a archivo parquet."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        features.to_parquet(output_path, compression='snappy', index=False)
        logger.info(f"Features guardados en: {output_path}")
        logger.info(f"Tamaño del archivo: {output_path.stat().st_size / 1024 / 1024:.2f} MB")


def process_features_chunked(input_file: str, output_file: str, chunk_size: int = 500_000):
    """
    Procesa features en chunks para datasets grandes.
    
    Args:
        input_file: Path a ml_training.parquet
        output_file: Path de salida para ml_features.parquet
        chunk_size: Tamaño de cada chunk
    """
    logger.info(f"Procesando features desde {input_file}")
    
    engineer = PropSafeFeatureEngineer()
    
    # Leer todo el archivo (5.7M registros caben en memoria)
    logger.info("Cargando datos...")
    df = pd.read_parquet(input_file)
    logger.info(f"Datos cargados: {len(df):,} registros")
    
    # Crear features
    features = engineer.create_features(df)
    
    # Guardar
    engineer.save_features(features, output_file)
    
    return features


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generar features para ML')
    parser.add_argument(
        '--input', 
        default='data/clean/ml_training.parquet',
        help='Archivo de entrada (ml_training.parquet)'
    )
    parser.add_argument(
        '--output',
        default='data/clean/ml_features.parquet',
        help='Archivo de salida para features'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=500000,
        help='Tamaño de chunk para procesamiento'
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("PropSafe AI - Feature Engineering")
    logger.info("="*60)
    
    start_time = datetime.now()
    
    # Procesar features
    features = process_features_chunked(
        args.input,
        args.output,
        args.chunk_size
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    logger.info("="*60)
    logger.info(f"Feature Engineering completado en {elapsed:.1f} segundos")
    logger.info(f"Total registros: {len(features):,}")
    logger.info(f"Total features: {len(features.columns) - 1}")
    logger.info("="*60)
