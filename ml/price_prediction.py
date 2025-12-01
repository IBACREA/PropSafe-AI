"""
Price Prediction Model Training
Modelo de ML para predecir precios justos de transacciones inmobiliarias
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PricePredictor:
    """Modelo de predicción de precios inmobiliarios"""
    
    def __init__(self):
        self.model = None
        self.encoders = {}
        self.feature_names = []
        self.stats = {}
        
    def prepare_features(self, df):
        """Prepara features para el modelo usando columnas SNR"""
        logger.info(f"Preparando features para {len(df)} registros")
        
        df_clean = df.copy()
        
        # Limpiar valores nulos en columnas críticas
        required_cols = ['valor_acto', 'municipio', 'departamento']
        df_clean = df_clean.dropna(subset=required_cols)
        
        # Filtrar valores extremos (outliers)
        q_low = df_clean['valor_acto'].quantile(0.01)
        q_high = df_clean['valor_acto'].quantile(0.99)
        df_clean = df_clean[
            (df_clean['valor_acto'] >= q_low) & 
            (df_clean['valor_acto'] <= q_high)
        ]
        
        logger.info(f"Después de limpieza: {len(df_clean)} registros")
        
        # Features categóricas principales
        categorical_features = [
            'municipio', 
            'departamento', 
            'tipo_predio',
            'nombre_natujur',  # Tipo de acto jurídico (SNR)
            'estado_folio',
            'categoria_ruralidad'
        ]
        
        for col in categorical_features:
            if col in df_clean.columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    df_clean[f'{col}_encoded'] = self.encoders[col].fit_transform(
                        df_clean[col].fillna('UNKNOWN')
                    )
                else:
                    # Manejar valores no vistos durante entrenamiento
                    le = self.encoders[col]
                    df_clean[f'{col}_encoded'] = df_clean[col].fillna('UNKNOWN').apply(
                        lambda x: le.transform([x])[0] if x in le.classes_ else -1
                    )
        
        # Features numéricas SNR
        numeric_features = {
            'count_a': 1,  # Receptores (default 1)
            'count_de': 1,  # Otorgantes (default 1)
            'predios_nuevos': 0,  # Si es predio nuevo
            'dinamica_inmobiliaria': 1,  # Si es mercado inmobiliario
        }
        
        for col, default_val in numeric_features.items():
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(default_val)
            else:
                df_clean[col] = default_val
        
        # Features derivadas
        df_clean['total_intervinientes'] = df_clean['count_a'] + df_clean['count_de']
        
        # Extraer features temporales
        if 'year' in df_clean.columns:
            df_clean['año'] = df_clean['year']
        elif 'year_radica' in df_clean.columns:
            df_clean['año'] = pd.to_numeric(df_clean['year_radica'], errors='coerce').fillna(2024)
        else:
            df_clean['año'] = 2024
            
        if 'month' in df_clean.columns:
            df_clean['mes'] = df_clean['month']
        else:
            df_clean['mes'] = 1
            
        if 'quarter' in df_clean.columns:
            df_clean['trimestre'] = df_clean['quarter']
        else:
            df_clean['trimestre'] = 1
        
        # Seleccionar features finales
        feature_columns = [
            'municipio_encoded', 'departamento_encoded', 'tipo_predio_encoded',
            'nombre_natujur_encoded', 'estado_folio_encoded',
            'count_a', 'count_de', 'total_intervinientes',
            'predios_nuevos', 'dinamica_inmobiliaria',
            'año', 'mes', 'trimestre'
        ]
        
        # Agregar categoria_ruralidad si está disponible
        if 'categoria_ruralidad_encoded' in df_clean.columns:
            feature_columns.append('categoria_ruralidad_encoded')
        
        # Verificar que todas las columnas existen
        available_features = [col for col in feature_columns if col in df_clean.columns]
        
        self.feature_names = available_features
        logger.info(f"Features seleccionadas: {available_features}")
        
        return df_clean[available_features], df_clean['valor_acto']
    
    def train(self, data, test_size=0.2, n_estimators=100):
        """Entrena el modelo de predicción de precios
        
        Args:
            data: DataFrame o path al archivo (parquet/csv)
            test_size: Fracción para test
            n_estimators: Número de árboles en RF
        """
        # Cargar datos si es path, sino usar DataFrame directamente
        if isinstance(data, pd.DataFrame):
            df = data
            logger.info(f"Usando DataFrame proporcionado: {len(df)} registros")
        else:
            logger.info(f"Cargando datos desde {data}")
            if str(data).endswith('.parquet'):
                df = pd.read_parquet(data)
            elif str(data).endswith('.csv'):
                df = pd.read_csv(data)
            else:
                raise ValueError("Formato no soportado. Use .parquet o .csv")
            logger.info(f"Dataset cargado: {len(df)} registros, {len(df.columns)} columnas")
        
        # Preparar features
        X, y = self.prepare_features(df)
        
        # Calcular estadísticas
        self.stats = {
            'total_samples': len(X),
            'mean_price': float(y.mean()),
            'median_price': float(y.median()),
            'min_price': float(y.min()),
            'max_price': float(y.max()),
            'std_price': float(y.std()),
        }
        
        logger.info(f"Estadísticas: precio promedio=${self.stats['mean_price']:,.0f}")
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Entrenar Random Forest
        logger.info(f"Entrenando Random Forest con {n_estimators} árboles...")
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=20,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluar
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        
        logger.info(f"Train MAE: ${train_mae:,.0f} | R²: {train_r2:.3f}")
        logger.info(f"Test MAE: ${test_mae:,.0f} | R²: {test_r2:.3f} | RMSE: ${test_rmse:,.0f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info("\nTop 10 features importantes:")
        logger.info(feature_importance.head(10).to_string(index=False))
        
        self.stats['train_mae'] = float(train_mae)
        self.stats['test_mae'] = float(test_mae)
        self.stats['train_r2'] = float(train_r2)
        self.stats['test_r2'] = float(test_r2)
        self.stats['test_rmse'] = float(test_rmse)
        self.stats['feature_importance'] = feature_importance.to_dict('records')
        
        return self.stats
    
    def predict(self, transaction_data):
        """Predice el precio de una transacción"""
        if self.model is None:
            raise ValueError("Modelo no entrenado. Ejecuta train() primero.")
        
        # Convertir a DataFrame
        df = pd.DataFrame([transaction_data])
        
        # Preparar features
        X, _ = self.prepare_features(df)
        
        # Predecir
        predicted_price = self.model.predict(X)[0]
        
        # Calcular intervalo de confianza (usando percentiles del bosque)
        tree_predictions = np.array([tree.predict(X)[0] for tree in self.model.estimators_])
        confidence_low = np.percentile(tree_predictions, 5)
        confidence_high = np.percentile(tree_predictions, 95)
        
        # Calcular score de anomalía
        actual_price = transaction_data.get('valor_acto', predicted_price)
        deviation = abs(actual_price - predicted_price) / predicted_price
        anomaly_score = min(deviation, 1.0)  # Normalizar 0-1
        
        is_suspicious = anomaly_score > 0.3  # 30% desviación
        
        return {
            'predicted_price': float(predicted_price),
            'confidence_interval': {
                'low': float(confidence_low),
                'high': float(confidence_high)
            },
            'actual_price': float(actual_price),
            'anomaly_score': float(anomaly_score),
            'is_suspicious': bool(is_suspicious),
            'deviation_percentage': float(deviation * 100)
        }
    
    def save(self, output_dir):
        """Guarda el modelo entrenado"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Guardar modelo
        model_path = output_path / 'price_predictor.joblib'
        joblib.dump(self.model, model_path)
        logger.info(f"Modelo guardado en: {model_path}")
        
        # Guardar encoders
        encoders_path = output_path / 'encoders.joblib'
        joblib.dump(self.encoders, encoders_path)
        logger.info(f"Encoders guardados en: {encoders_path}")
        
        # Guardar metadata
        metadata = {
            'feature_names': self.feature_names,
            'stats': self.stats,
            'model_type': 'RandomForestRegressor',
            'n_estimators': self.model.n_estimators if self.model else 0
        }
        
        metadata_path = output_path / 'price_predictor_metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Metadata guardada en: {metadata_path}")
    
    @classmethod
    def load(cls, model_dir):
        """Carga un modelo entrenado"""
        model_path = Path(model_dir)
        
        predictor = cls()
        predictor.model = joblib.load(model_path / 'price_predictor.joblib')
        predictor.encoders = joblib.load(model_path / 'encoders.joblib')
        
        with open(model_path / 'price_predictor_metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            predictor.feature_names = metadata['feature_names']
            predictor.stats = metadata['stats']
        
        logger.info(f"Modelo cargado desde: {model_path}")
        return predictor


def main():
    """Función principal para entrenar el modelo"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Entrenar modelo de predicción de precios')
    parser.add_argument('--data', type=str, required=True, help='Ruta al archivo de datos')
    parser.add_argument('--output', type=str, default='ml/models', help='Directorio de salida')
    parser.add_argument('--n-estimators', type=int, default=100, help='Número de árboles')
    
    args = parser.parse_args()
    
    # Crear y entrenar modelo
    predictor = PricePredictor()
    stats = predictor.train(args.data, n_estimators=args.n_estimators)
    
    # Guardar modelo
    predictor.save(args.output)
    
    logger.info("\n✅ Entrenamiento completado!")
    logger.info(f"Test R²: {stats['test_r2']:.3f}")
    logger.info(f"Test MAE: ${stats['test_mae']:,.0f}")
    
    # Ejemplo de predicción
    logger.info("\n🧪 Ejemplo de predicción:")
    test_transaction = {
        'municipio': 'BOGOTA',
        'departamento': 'CUNDINAMARCA',
        'tipo_predio': 'urbano',
        'tipo_acto': 'compraventa',
        'estado_folio': 'activo',
        'area_terreno': 120,
        'area_construida': 85,
        'numero_intervinientes': 2,
        'valor_acto': 250000000
    }
    
    result = predictor.predict(test_transaction)
    logger.info(f"Precio predicho: ${result['predicted_price']:,.0f}")
    logger.info(f"Rango confianza: ${result['confidence_interval']['low']:,.0f} - ${result['confidence_interval']['high']:,.0f}")
    logger.info(f"¿Sospechoso?: {result['is_suspicious']}")


if __name__ == '__main__':
    main()
