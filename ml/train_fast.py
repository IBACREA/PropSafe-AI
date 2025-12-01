#!/usr/bin/env python3
"""
Entrenamiento rápido - SOLO Isolation Forest (CPU optimizado)
Tiempo estimado: 23 minutos para 30M registros
"""
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import os
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split


def load_data(input_path):
    """Cargar datos desde Parquet"""
    print(f"\n[1/4] 📂 Cargando datos... [{datetime.now().strftime('%H:%M:%S')}]")
    start_time = datetime.now()
    
    df = pd.read_parquet(input_path)
    print(f"  Dataset: {len(df):,} registros")
    
    load_time = (datetime.now() - start_time).total_seconds()
    print(f"  ✅ {load_time:.1f}s")
    return df, load_time


def engineer_features(df):
    """Feature engineering básico - autodetectar columnas numéricas"""
    print(f"\n[2/4] 🔧 Feature engineering... [{datetime.now().strftime('%H:%M:%S')}]")
    start_time = datetime.now()
    
    # Auto-detectar columnas numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in ['PK']]
    
    if not numeric_cols:
        raise ValueError("No se encontraron columnas numéricas para el modelo")
    
    X = df[numeric_cols].fillna(0)
    
    feature_time = (datetime.now() - start_time).total_seconds()
    print(f"  ({len(numeric_cols)} features) ✅ {feature_time:.1f}s")
    print(f"  Features: {', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''}")
    
    return X, feature_time


def train_isolation_forest(X, contamination=0.1):
    """Entrenar Isolation Forest optimizado"""
    print(f"\n[3/4] 🌲 Entrenando Isolation Forest... [{datetime.now().strftime('%H:%M:%S')}]")
    start_train = datetime.now()
    
    # Split train/test
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
    print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")
    
    # Entrenar con todos los cores disponibles
    model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,  # Usar todos los cores
        verbose=1,   # Mostrar progreso
        max_samples='auto'
    )
    
    model.fit(X_train)
    
    # Evaluar
    train_scores = model.predict(X_train)
    test_scores = model.predict(X_test)
    
    train_anomalies = (train_scores == -1).sum()
    test_anomalies = (test_scores == -1).sum()
    
    train_time = (datetime.now() - start_train).total_seconds()
    
    print(f"  ✅ {train_time:.1f}s ({train_time/60:.1f} min)")
    print(f"  Train anomalías: {train_anomalies:,} ({train_anomalies/len(X_train)*100:.2f}%)")
    print(f"  Test anomalías:  {test_anomalies:,} ({test_anomalies/len(X_test)*100:.2f}%)")
    
    return model, train_time


def save_model(model, output_dir):
    """Guardar modelo entrenado"""
    print(f"\n[4/4] 💾 Guardando modelo... [{datetime.now().strftime('%H:%M:%S')}]")
    
    os.makedirs(output_dir, exist_ok=True)
    
    model_path = os.path.join(output_dir, 'isolation_forest.pkl')
    joblib.dump(model, model_path)
    
    print(f"  ✅ Modelo guardado: {model_path}")


def main():
    parser = argparse.ArgumentParser(description='Entrenamiento rápido con Isolation Forest')
    parser.add_argument('--input', required=True, help='Ruta al archivo Parquet')
    parser.add_argument('--output', default='./models', help='Directorio de salida')
    parser.add_argument('--contamination', type=float, default=0.1, help='Porcentaje de anomalías esperadas')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 ENTRENAMIENTO RÁPIDO - ISOLATION FOREST (CPU OPTIMIZADO)")
    print("=" * 80)
    
    total_start = datetime.now()
    
    # Cargar datos
    df, load_time = load_data(args.input)
    
    # Feature engineering
    X, feature_time = engineer_features(df)
    
    # Entrenar modelo
    model, train_time = train_isolation_forest(X, args.contamination)
    
    # Guardar modelo
    save_model(model, args.output)
    
    # Resumen final
    total_time = (datetime.now() - total_start).total_seconds()
    
    print("\n" + "=" * 80)
    print("✅ ENTRENAMIENTO COMPLETADO")
    print("=" * 80)
    print(f"Total: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  - Carga:     {load_time:.1f}s")
    print(f"  - Features:  {feature_time:.1f}s")
    print(f"  - Training:  {train_time:.1f}s ({train_time/60:.1f} min)")
    print(f"\nModelo guardado en: {args.output}")
    print("\n💡 TIP: Este modelo detecta anomalías en {:.0f}% de los datos".format(args.contamination * 100))


if __name__ == '__main__':
    main()
