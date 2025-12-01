#!/usr/bin/env python3
"""
Pipeline Híbrido GPU para Detección de Anomalías
Fase 1: Isolation Forest (cuML GPU) - filtrado rápido
Fase 2: Autoencoder (PyTorch GPU) - refinamiento de candidatos
"""
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Verificar GPU disponible
CUDA_AVAILABLE = torch.cuda.is_available()
DEVICE = torch.device('cuda' if CUDA_AVAILABLE else 'cpu')

print(f"🎮 GPU PyTorch: {'✅ ' + torch.cuda.get_device_name(0) if CUDA_AVAILABLE else '❌ CPU'}")


class AnomalyAutoencoder(nn.Module):
    """Autoencoder para detección de anomalías"""
    def __init__(self, input_dim, encoding_dim=16):
        super(AnomalyAutoencoder, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, encoding_dim),
            nn.ReLU()
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, input_dim)
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


def load_data(input_path, sample_size=None):
    """Cargar datos desde Parquet"""
    print(f"\n[1/6] 📂 Cargando datos... [{datetime.now().strftime('%H:%M:%S')}]")
    start_time = datetime.now()
    
    df = pd.read_parquet(input_path)
    if sample_size:
        df = df.sample(n=min(sample_size, len(df)), random_state=42)
    
    print(f"  {len(df):,} registros")
    load_time = (datetime.now() - start_time).total_seconds()
    print(f"  ✅ {load_time:.1f}s")
    return df, load_time


def engineer_features(df):
    """Feature engineering básico"""
    print(f"\n[2/6] 🔧 Feature engineering... [{datetime.now().strftime('%H:%M:%S')}]")
    start_time = datetime.now()
    
    # Auto-detectar columnas numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in ['PK']]
    
    if not numeric_cols:
        raise ValueError("No se encontraron columnas numéricas")
    
    X = df[numeric_cols].fillna(0).values
    
    feature_time = (datetime.now() - start_time).total_seconds()
    print(f"  ({len(numeric_cols)} features) ✅ {feature_time:.1f}s")
    print(f"  Features: {', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''}")
    
    return X, numeric_cols, feature_time


def phase1_isolation_forest(X, contamination=0.1):
    """Fase 1: Filtrado rápido con Isolation Forest"""
    print(f"\n[3/6] 🌲 FASE 1: Isolation Forest (sklearn multi-core)... [{datetime.now().strftime('%H:%M:%S')}]")
    start_time = datetime.now()
    
    # Usar sklearn con n_jobs=-1 (multi-core en CPU)
    from sklearn.ensemble import IsolationForest
    
    if_model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    
    if_model.fit(X)
    if_scores = if_model.predict(X)
    if_anomalies = (if_scores == -1)
    
    if_time = (datetime.now() - start_time).total_seconds()
    n_anomalies = if_anomalies.sum()
    
    print(f"  ✅ {if_time:.1f}s")
    print(f"  Anomalías detectadas: {n_anomalies:,} ({n_anomalies/len(X)*100:.1f}%)")
    
    return if_model, if_anomalies, if_time


def phase2_autoencoder(X, if_anomalies, epochs=50, batch_size=256):
    """Fase 2: Refinamiento con Autoencoder en GPU"""
    print(f"\n[4/6] 🧠 FASE 2: Autoencoder PyTorch GPU... [{datetime.now().strftime('%H:%M:%S')}]")
    start_time = datetime.now()
    
    # Normalizar datos
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Solo entrenar con datos "normales" (no anomalías de IF)
    X_normal = X_scaled[~if_anomalies]
    print(f"  Entrenando con {len(X_normal):,} registros normales")
    
    # Preparar datos para PyTorch
    X_train, X_val = train_test_split(X_normal, test_size=0.2, random_state=42)
    
    train_tensor = torch.FloatTensor(X_train).to(DEVICE)
    val_tensor = torch.FloatTensor(X_val).to(DEVICE)
    
    train_dataset = TensorDataset(train_tensor, train_tensor)
    val_dataset = TensorDataset(val_tensor, val_tensor)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # Crear modelo
    input_dim = X_scaled.shape[1]
    model = AnomalyAutoencoder(input_dim).to(DEVICE)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    print(f"  Modelo en: {DEVICE}")
    print(f"  Épocas: {epochs}, Batch size: {batch_size}")
    
    # Entrenar
    best_val_loss = float('inf')
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        
        if (epoch + 1) % 10 == 0:
            print(f"  Época {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.6f}, Val Loss: {avg_val_loss:.6f}")
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
    
    # Evaluar todo el dataset
    model.eval()
    X_all_tensor = torch.FloatTensor(X_scaled).to(DEVICE)
    
    with torch.no_grad():
        reconstructed = model(X_all_tensor)
        mse = torch.mean((X_all_tensor - reconstructed) ** 2, dim=1)
        mse = mse.cpu().numpy()
    
    # Definir umbral (95 percentil del error en datos normales)
    threshold = np.percentile(mse[~if_anomalies], 95)
    ae_anomalies = mse > threshold
    
    ae_time = (datetime.now() - start_time).total_seconds()
    n_ae_anomalies = ae_anomalies.sum()
    
    print(f"  ✅ {ae_time:.1f}s ({ae_time/60:.1f} min)")
    print(f"  Umbral MSE: {threshold:.6f}")
    print(f"  Anomalías AE: {n_ae_anomalies:,} ({n_ae_anomalies/len(X)*100:.1f}%)")
    
    return model, scaler, ae_anomalies, mse, ae_time


def combine_results(if_anomalies, ae_anomalies):
    """Combinar resultados de ambas fases"""
    print(f"\n[5/6] 🔀 Combinando resultados... [{datetime.now().strftime('%H:%M:%S')}]")
    
    # Anomalías confirmadas: detectadas por ambos métodos
    confirmed = if_anomalies & ae_anomalies
    
    # Anomalías candidatas: detectadas por al menos uno
    candidates = if_anomalies | ae_anomalies
    
    print(f"  IF detectó: {if_anomalies.sum():,}")
    print(f"  AE detectó: {ae_anomalies.sum():,}")
    print(f"  Confirmadas (ambos): {confirmed.sum():,}")
    print(f"  Candidatas (al menos 1): {candidates.sum():,}")
    
    return confirmed, candidates


def save_models(if_model, ae_model, scaler, output_dir):
    """Guardar modelos entrenados"""
    print(f"\n[6/6] 💾 Guardando modelos... [{datetime.now().strftime('%H:%M:%S')}]")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Guardar IF
    joblib.dump(if_model, os.path.join(output_dir, 'isolation_forest.pkl'))
    
    # Guardar Autoencoder
    torch.save(ae_model.state_dict(), os.path.join(output_dir, 'autoencoder.pth'))
    
    # Guardar scaler
    joblib.dump(scaler, os.path.join(output_dir, 'scaler.pkl'))
    
    print(f"  ✅ Modelos guardados en: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Pipeline híbrido GPU para anomalías')
    parser.add_argument('--input', required=True, help='Ruta al archivo Parquet')
    parser.add_argument('--sample', type=int, help='Tamaño de muestra (opcional)')
    parser.add_argument('--output', default='./models', help='Directorio de salida')
    parser.add_argument('--contamination', type=float, default=0.1, help='% anomalías esperadas')
    parser.add_argument('--epochs', type=int, default=50, help='Épocas para Autoencoder')
    parser.add_argument('--batch-size', type=int, default=256, help='Batch size')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 PIPELINE HÍBRIDO GPU: ISOLATION FOREST + AUTOENCODER")
    print("=" * 80)
    print(f"GPU PyTorch: {DEVICE}")
    print(f"Contamination: {args.contamination}")
    
    total_start = datetime.now()
    
    # Cargar datos
    df, load_time = load_data(args.input, args.sample)
    
    # Feature engineering
    X, feature_names, feature_time = engineer_features(df)
    
    # Fase 1: Isolation Forest (filtrado rápido)
    if_model, if_anomalies, if_time = phase1_isolation_forest(X, args.contamination)
    
    # Fase 2: Autoencoder (refinamiento)
    ae_model, scaler, ae_anomalies, mse_scores, ae_time = phase2_autoencoder(
        X, if_anomalies, epochs=args.epochs, batch_size=args.batch_size
    )
    
    # Combinar resultados
    confirmed, candidates = combine_results(if_anomalies, ae_anomalies)
    
    # Guardar modelos
    save_models(if_model, ae_model, scaler, args.output)
    
    # Resumen final
    total_time = (datetime.now() - total_start).total_seconds()
    
    print("\n" + "=" * 80)
    print("✅ PIPELINE COMPLETADO")
    print("=" * 80)
    print(f"Total: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  - Carga:         {load_time:.1f}s")
    print(f"  - Features:      {feature_time:.1f}s")
    print(f"  - IF (Fase 1):   {if_time:.1f}s")
    print(f"  - AE (Fase 2):   {ae_time:.1f}s ({ae_time/60:.1f} min)")
    print(f"\nResultados:")
    print(f"  - Anomalías confirmadas: {confirmed.sum():,} ({confirmed.sum()/len(X)*100:.2f}%)")
    print(f"  - Anomalías candidatas:  {candidates.sum():,} ({candidates.sum()/len(X)*100:.2f}%)")
    print(f"\nModelos guardados en: {args.output}")


if __name__ == '__main__':
    main()
