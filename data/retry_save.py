#!/usr/bin/env python3
"""Reintentar guardar CSV a Parquet con corrección de tipos"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

print("Leyendo CSV completo...")
df = pd.read_csv(
    "D:/projects/datos/data/raw/datos.csv",
    encoding='utf-8',
    low_memory=False
)

print(f"Total registros: {len(df):,}")
print(f"Columnas: {df.columns.tolist()}")

# Detectar columnas problemáticas
print("\nConvirtiendo tipos...")

# Columnas de texto
text_cols = ['departamento', 'municipio', 'tipo_acto', 'tipo_predio', 
             'estado_folio', 'nombre_natujur', 'matricula']
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()
        df[col] = df[col].replace('NAN', None)

# Columnas numéricas (forzar conversión)
numeric_cols = ['valor_acto', 'area_terreno', 'area_construida', 
                'numero_intervinientes', 'count_a', 'count_de', 'ORIP']
for col in numeric_cols:
    if col in df.columns:
        print(f"  Convirtiendo {col}...")
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Fechas
date_cols = ['fecha_radicacion', 'fecha_acto']
for col in date_cols:
    if col in df.columns:
        print(f"  Convirtiendo {col}...")
        df[col] = pd.to_datetime(df[col], errors='coerce')

print("\nGuardando Parquet...")
output_path = "D:/projects/datos/data/processed/datos.parquet"
df.to_parquet(
    output_path,
    engine='pyarrow',
    compression='snappy',
    index=False
)

# Stats
input_size = Path("D:/projects/datos/data/raw/datos.csv").stat().st_size / (1024**3)
output_size = Path(output_path).stat().st_size / (1024**3)
compression = input_size / output_size

print("\n" + "="*80)
print("✅ CONVERSION COMPLETED")
print("="*80)
print(f"Total rows:   {len(df):,}")
print(f"Input size:   {input_size:.2f} GB")
print(f"Output size:  {output_size:.2f} GB")
print(f"Compression:  {compression:.1f}x")
print(f"Output:       {output_path}")
print("="*80)
