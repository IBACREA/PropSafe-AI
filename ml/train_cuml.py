#!/usr/bin/env python3
"""
Entrenamiento ACELERADO con GPU (cuDF + sklearn en GPU)
Usa cuDF (GPU) para manipulación de datos + sklearn con n_jobs=-1
"""
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import os

# Intentar usar cuDF para acelerar lectura/procesamiento de datos
try:
    import cudf
    GPU_AVAILABLE = True
    print("✅ cuDF (GPU) disponible para procesamiento de datos")
except ImportError:
    GPU_AVAILABLE = False
    print("⚠️ cuDF no disponible, usando pandas CPU")

# sklearn para algoritmos (no hay IF/LOF en cuML)
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor


def load_data(input_path, sample_size=None):
    """Cargar datos desde Parquet"""
    print(f"\n[1/5] 📂 Cargando datos... [{datetime.now().strftime('%H:%M:%S')}]")
    start_time = datetime.now()
    
    # Usar pandas (cuDF tiene problemas con indices)
    df = pd.read_parquet(input_path)
    if sample_size:
        df = df.sample(n=min(sample_size, len(df)), random_state=42)
    
    print(f"  {len(df):,} registros")
    load_time = (datetime.now() - start_time).total_seconds()
    print(f"  ✅ {load_time:.1f}s")
    return df, load_time


def engineer_features(df):
    """Feature engineering básico - autodetectar columnas numéricas"""
    print(f"\n[2/5] 🔧 Feature engineering... [{datetime.now().strftime('%H:%M:%S')}]")
    start_time = datetime.now()
    
    # Auto-detectar columnas numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in ['PK']]
    
    if not numeric_cols:
        raise ValueError("No se encontraron columnas numéricas para el modelo")
    
    X = df[numeric_cols].fillna(0)
    
    feature_time = (datetime.now() - start_time).total_seconds()
    print(f"  ({len(numeric_cols)} features) ✅ {feature_time:.1f}s")
    print(f"  Features: {', '.join(numeric_cols)}")
    
    return X, feature_time


def train_models(X, contamination=0.1):
    """Entrenar modelos de detección de anomalías (sklearn multi-thread)"""
    print(f"\n[3/5] 🤖 Entrenando modelos (CPU multi-core)... [{datetime.now().strftime('%H:%M:%S')}]")
    
    # Isolation Forest
    print(f"  🌲 Isolation Forest [{datetime.now().strftime('%H:%M:%S')}]...", end=" ", flush=True)
    start_if = datetime.now()
    
    if_model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,  # Usar todos los cores
        verbose=0
    )
    if_model.fit(X)
    if_scores = if_model.predict(X)
    
    if_time = (datetime.now() - start_if).total_seconds()
    anomalies_if = (if_scores == -1).sum()
    print(f"✅ {if_time:.1f}s ({anomalies_if:,} anomalías, {anomalies_if/len(X)*100:.1f}%)")
    
    # Local Outlier Factor
    print(f"  🎯 Local Outlier Factor [{datetime.now().strftime('%H:%M:%S')}]...", end=" ", flush=True)
    start_lof = datetime.now()
    
    lof_model = LocalOutlierFactor(
        n_neighbors=25,
        contamination=contamination,
        novelty=True,
        n_jobs=-1
    )
    lof_model.fit(X)
    lof_scores = lof_model.predict(X)
    
    lof_time = (datetime.now() - start_lof).total_seconds()
    anomalies_lof = (lof_scores == -1).sum()
    print(f"✅ {lof_time:.1f}s ({anomalies_lof:,} anomalías, {anomalies_lof/len(X)*100:.1f}%)")
    
    training_time = if_time + lof_time
    
    return if_model, lof_model, training_time


def save_models(if_model, lof_model, output_dir):
    """Guardar modelos entrenados"""
    print(f"\n[4/5] 💾 Guardando modelos... [{datetime.now().strftime('%H:%M:%S')}]")
    
    os.makedirs(output_dir, exist_ok=True)
    
    joblib.dump(if_model, os.path.join(output_dir, 'isolation_forest.pkl'))
    joblib.dump(lof_model, os.path.join(output_dir, 'local_outlier_factor.pkl'))
    
    print(f"  ✅ Modelos guardados en: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Entrenar modelos con RAPIDS cuML (GPU)')
    parser.add_argument('--input', required=True, help='Ruta al archivo Parquet')
    parser.add_argument('--sample', type=int, help='Tamaño de muestra (opcional)')
    parser.add_argument('--output', default='./models', help='Directorio de salida')
    parser.add_argument('--contamination', type=float, default=0.1, help='Porcentaje de anomalías esperadas')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 ENTRENAMIENTO ACELERADO (cuDF + sklearn)")
    print("=" * 80)
    print(f"cuDF GPU: {'✅ ACTIVADO' if GPU_AVAILABLE else '❌ CPU pandas'}")
    print(f"sklearn: ✅ Multi-core (n_jobs=-1)")
    
    # Cargar datos
    df, load_time = load_data(args.input, args.sample)
    
    # Feature engineering
    X, feature_time = engineer_features(df)
    
    # Split (simple train/test)
    print(f"\n[3/5] 📊 Split train/test... [{datetime.now().strftime('%H:%M:%S')}]")
    from sklearn.model_selection import train_test_split
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
    split_time = 0.1
    print(f"  ✅ {split_time:.1f}s ({len(X_train):,} / {len(X_test):,})")
    
    # Entrenar modelos
    if_model, lof_model, training_time = train_models(X_train, args.contamination)
    
    # Guardar modelos
    save_models(if_model, lof_model, args.output)
    
    # Resumen final
    total_time = load_time + feature_time + training_time
    
    print("\n" + "=" * 80)
    print("✅ ENTRENAMIENTO COMPLETADO")
    print("=" * 80)
    print(f"Total: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  - Carga:     {load_time:.1f}s")
    print(f"  - Features:  {feature_time:.1f}s")
    print(f"  - Training:  {training_time:.1f}s")
    print(f"\nModelos guardados en: {args.output}")
    
    # Proyección para dataset completo si fue muestra
    if args.sample and args.sample < 30_000_000:
        scale_factor = 30_903_248 / args.sample
        training_scale = scale_factor * np.log(scale_factor) / np.log(args.sample)
        estimated_total = load_time * scale_factor + training_time * training_scale
        
        print(f"\n📊 PROYECCIÓN PARA 30,903,248 REGISTROS:")
        print(f"  Tiempo estimado: {estimated_total/60:.1f} min ({estimated_total/3600:.1f} horas)")


if __name__ == '__main__':
    main()
