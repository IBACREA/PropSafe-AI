#!/usr/bin/env python3
"""
Entrenar con muestras progresivas para estimar tiempos

Usage:
    python train_sample.py --input datos.parquet --sample 100000
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

print("\n" + "="*80)
print("🚀 ENTRENAMIENTO CON MUESTREO PROGRESIVO")
print("="*80)

def train_with_sample(data_path: str, sample_size: int, output_dir: str):
    """Entrenar con una muestra específica"""
    
    print(f"\n📊 Sample size: {sample_size:,} registros")
    print("="*80)
    
    # 1. Cargar datos
    print(f"\n[1/5] 📂 Cargando datos... [{datetime.now().strftime('%H:%M:%S')}]", end=" ", flush=True)
    start = datetime.now()
    df = pd.read_parquet(data_path)
    
    # Muestrear
    if sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42)
    
    load_time = (datetime.now() - start).total_seconds()
    print(f"✅ {load_time:.1f}s")
    
    # 2. Ingeniería de features simple
    print(f"[2/5] 🔧 Feature engineering... [{datetime.now().strftime('%H:%M:%S')}]", end=" ", flush=True)
    start = datetime.now()
    
    # Detectar columnas numéricas disponibles
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Eliminar PK si existe
    numeric_cols = [col for col in numeric_cols if col not in ['PK', 'pk', 'id', 'ID']]
    
    print(f"({len(numeric_cols)} features)", end=" ", flush=True)
    X = df[numeric_cols].fillna(0).values
    
    # Normalizar
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    feature_time = (datetime.now() - start).total_seconds()
    print(f"✅ {feature_time:.1f}s")
    
    # 3. Split
    print(f"[3/5] 📊 Split train/test... [{datetime.now().strftime('%H:%M:%S')}]", end=" ", flush=True)
    start = datetime.now()
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
    split_time = (datetime.now() - start).total_seconds()
    print(f" ✅ {split_time:.1f}s ({len(X_train):,} / {len(X_test):,})")
    
    # 4. Entrenar modelos
    print(f"\n[4/5] 🤖 Entrenando modelos... [{datetime.now().strftime('%H:%M:%S')}]")
    print("-"*80)
    
    models = {}
    times = {}
    
    # Isolation Forest
    print(f"  🌲 Isolation Forest [{datetime.now().strftime('%H:%M:%S')}]...", end=" ", flush=True)
    start = datetime.now()
    if_model = IsolationForest(
        n_estimators=100,
        max_samples='auto',
        contamination=0.1,
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    if_model.fit(X_train)
    if_time = (datetime.now() - start).total_seconds()
    times['isolation_forest'] = if_time
    print(f"✅ {if_time:.1f}s")
    
    # Local Outlier Factor
    print(f"  🎯 Local Outlier Factor [{datetime.now().strftime('%H:%M:%S')}]...", end=" ", flush=True)
    start = datetime.now()
    lof_model = LocalOutlierFactor(
        n_neighbors=25,
        contamination=0.1,
        novelty=True,
        n_jobs=-1
    )
    lof_model.fit(X_train)
    lof_time = (datetime.now() - start).total_seconds()
    times['lof'] = lof_time
    print(f"✅ {lof_time:.1f}s")
    
    # XGBoost (omitido - sin GPU en Windows pip)
    print(f"  ⚠️  XGBoost GPU no disponible en esta instalación")
    xgb_time = 0
    
    # Usar solo IF + LOF es suficiente para detección de anomalías
    
    # 5. Resultados
    print("\n[5/5] 📈 Resumen")
    print("="*80)
    
    total_time = load_time + feature_time + split_time + sum(times.values())
    
    print(f"Muestra:          {sample_size:,} registros")
    print(f"Tiempo total:     {total_time:.1f}s ({total_time/60:.2f} min)")
    print(f"  - Carga:        {load_time:.1f}s")
    print(f"  - Features:     {feature_time:.1f}s")
    print(f"  - Split:        {split_time:.1f}s")
    print(f"  - IF:           {if_time:.1f}s")
    print(f"  - LOF:          {lof_time:.1f}s")
    
    # Proyección para dataset completo
    full_size = 30_903_248
    scale_factor = full_size / sample_size
    
    # Tiempos de entrenamiento escalan aproximadamente O(n log n)
    training_scale = scale_factor * np.log(scale_factor)
    
    estimated_if = if_time * training_scale
    estimated_lof = lof_time * training_scale
    estimated_total = load_time * scale_factor + feature_time * scale_factor + estimated_if + estimated_lof
    
    print(f"\n📊 PROYECCIÓN PARA {full_size:,} REGISTROS:")
    print(f"  - IF estimado:    {estimated_if/60:.1f} min")
    print(f"  - LOF estimado:   {estimated_lof/60:.1f} min")
    print(f"  - Total estimado: {estimated_total/60:.1f} min")
    print("="*80)
    
    return times, total_time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--sample', type=int, default=100000)
    parser.add_argument('--output', default='./ml/models')
    
    args = parser.parse_args()
    
    train_with_sample(args.input, args.sample, args.output)

if __name__ == '__main__':
    main()
