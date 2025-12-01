"""
Generador de datos sintéticos para entrenamiento
Genera 100k transacciones realistas basadas en patrones colombianos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Semilla para reproducibilidad
np.random.seed(42)
random.seed(42)

# Municipios principales de Colombia
MUNICIPIOS = [
    ('BOGOTA', 'CUNDINAMARCA', 15000000, 450000000),
    ('MEDELLIN', 'ANTIOQUIA', 12000000, 380000000),
    ('CALI', 'VALLE DEL CAUCA', 10000000, 320000000),
    ('BARRANQUILLA', 'ATLANTICO', 9000000, 280000000),
    ('CARTAGENA', 'BOLIVAR', 11000000, 350000000),
    ('CUCUTA', 'NORTE DE SANTANDER', 7000000, 220000000),
    ('BUCARAMANGA', 'SANTANDER', 8500000, 260000000),
    ('PEREIRA', 'RISARALDA', 8000000, 240000000),
    ('IBAGUE', 'TOLIMA', 7500000, 230000000),
    ('MANIZALES', 'CALDAS', 8000000, 250000000),
]

TIPOS_ACTO = ['compraventa', 'hipoteca', 'donacion', 'permuta', 'otro']
TIPOS_PREDIO = ['urbano', 'rural', 'mixto']
ESTADOS_FOLIO = ['activo', 'cancelado', 'cerrado', 'suspendido']

def generate_transaction(municipio, departamento, precio_min, precio_max):
    """Genera una transacción sintética realista"""
    
    # Tipo de acto (80% compraventa)
    tipo_acto = random.choices(
        TIPOS_ACTO, 
        weights=[0.8, 0.1, 0.05, 0.03, 0.02]
    )[0]
    
    # Tipo de predio (70% urbano)
    tipo_predio = random.choices(
        TIPOS_PREDIO,
        weights=[0.7, 0.25, 0.05]
    )[0]
    
    # Estado folio (90% activo)
    estado_folio = random.choices(
        ESTADOS_FOLIO,
        weights=[0.9, 0.05, 0.03, 0.02]
    )[0]
    
    # Precio con distribución log-normal
    precio_base = np.random.lognormal(
        mean=np.log((precio_min + precio_max) / 2),
        sigma=0.5
    )
    
    # Ajustar según tipo de predio
    if tipo_predio == 'rural':
        precio_base *= 0.6
    elif tipo_predio == 'mixto':
        precio_base *= 0.8
    
    # Ajustar según tipo de acto
    if tipo_acto == 'donacion':
        precio_base *= 0.3  # Donaciones suelen tener valor catastral bajo
    elif tipo_acto == 'hipoteca':
        precio_base *= 0.7
    
    precio_final = max(precio_min * 0.3, min(precio_base, precio_max * 1.5))
    
    # Áreas según tipo de predio
    if tipo_predio == 'urbano':
        area_construida = np.random.uniform(40, 200)
        area_terreno = area_construida * np.random.uniform(1.0, 1.5)
    elif tipo_predio == 'rural':
        area_terreno = np.random.uniform(500, 50000)
        area_construida = np.random.uniform(50, 300)
    else:  # mixto
        area_terreno = np.random.uniform(200, 5000)
        area_construida = np.random.uniform(80, 400)
    
    # Número de intervinientes
    numero_intervinientes = random.choices([1, 2, 3, 4, 5], weights=[0.1, 0.6, 0.2, 0.07, 0.03])[0]
    
    # Fecha aleatoria entre 2020 y 2025
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 11, 28)
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    fecha_acto = start_date + timedelta(days=random_days)
    
    return {
        'valor_acto': precio_final,
        'tipo_acto': tipo_acto,
        'fecha_acto': fecha_acto.strftime('%Y-%m-%d'),
        'departamento': departamento,
        'municipio': municipio,
        'tipo_predio': tipo_predio,
        'numero_intervinientes': numero_intervinientes,
        'estado_folio': estado_folio,
        'area_terreno': area_terreno,
        'area_construida': area_construida,
    }

def generate_dataset(n_samples=100000):
    """Genera dataset sintético de transacciones"""
    print(f"Generando {n_samples:,} transacciones sintéticas...")
    
    transactions = []
    
    # Distribución de transacciones por municipio (Bogotá tiene más)
    weights = [0.35, 0.20, 0.15, 0.08, 0.07, 0.04, 0.04, 0.03, 0.02, 0.02]
    
    for i in range(n_samples):
        if i % 10000 == 0:
            print(f"Progreso: {i:,}/{n_samples:,}")
        
        # Seleccionar municipio aleatorio
        municipio, departamento, precio_min, precio_max = random.choices(
            MUNICIPIOS, weights=weights
        )[0]
        
        transaction = generate_transaction(municipio, departamento, precio_min, precio_max)
        transactions.append(transaction)
    
    df = pd.DataFrame(transactions)
    
    # Agregar algunas anomalías intencionales (5%)
    n_anomalies = int(n_samples * 0.05)
    anomaly_indices = np.random.choice(len(df), n_anomalies, replace=False)
    
    print(f"\nAgregando {n_anomalies:,} anomalías intencionales...")
    
    for idx in anomaly_indices:
        anomaly_type = random.choice(['precio_bajo', 'precio_alto', 'area_extraña'])
        
        if anomaly_type == 'precio_bajo':
            # Precio muy bajo (posible fraude)
            df.loc[idx, 'valor_acto'] *= 0.3
        elif anomaly_type == 'precio_alto':
            # Precio muy alto (posible error)
            df.loc[idx, 'valor_acto'] *= 3.0
        elif anomaly_type == 'area_extraña':
            # Áreas inconsistentes
            df.loc[idx, 'area_construida'] = df.loc[idx, 'area_terreno'] * 2
    
    print(f"\n✅ Dataset generado: {len(df):,} transacciones")
    print(f"\nEstadísticas:")
    print(f"  Precio promedio: ${df['valor_acto'].mean():,.0f}")
    print(f"  Precio mediano: ${df['valor_acto'].median():,.0f}")
    print(f"  Precio mínimo: ${df['valor_acto'].min():,.0f}")
    print(f"  Precio máximo: ${df['valor_acto'].max():,.0f}")
    print(f"\nDistribución por municipio:")
    print(df['municipio'].value_counts())
    
    return df

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generar datos sintéticos')
    parser.add_argument('--samples', type=int, default=100000, help='Número de transacciones')
    parser.add_argument('--output', type=str, default='data/processed/synthetic_100k.parquet', 
                        help='Archivo de salida')
    
    args = parser.parse_args()
    
    # Generar dataset
    df = generate_dataset(args.samples)
    
    # Guardar
    from pathlib import Path
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    print(f"\n💾 Guardado en: {output_path}")
    print(f"Tamaño: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
