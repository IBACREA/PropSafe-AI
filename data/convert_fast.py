#!/usr/bin/env python3
"""Convertir CSV a Parquet por chunks SIN cargar todo en memoria"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq

print("="*80)
print("CSV → PARQUET (Optimized)")
print("="*80)

input_path = Path("D:/projects/datos/data/raw/datos.csv")
output_path = Path("D:/projects/datos/data/processed/datos.parquet")
output_path.parent.mkdir(parents=True, exist_ok=True)

batch_size = 50000  # Chunks más grandes
start_time = datetime.now()
total_rows = 0

# Primera pasada: detectar schema
print("Detectando schema...")
sample = pd.read_csv(input_path, nrows=10000, low_memory=False)

# Forzar TODAS las columnas a string primero
print(f"Columnas totales: {len(sample.columns)}")

# Segunda pasada: convertir por chunks
print("\nProcesando chunks...")
writer = None
schema = None

try:
    reader = pd.read_csv(
        input_path,
        chunksize=batch_size,
        dtype=str,  # Todo como string primero
        low_memory=False
    )
    
    for i, chunk in enumerate(reader):
        chunk_start = datetime.now()
        
        # Convertir columnas numéricas conocidas
        numeric_cols = ['valor_acto', 'area_terreno', 'area_construida', 
                       'numero_intervinientes', 'count_a', 'count_de', 'ORIP']
        for col in numeric_cols:
            if col in chunk.columns:
                # Limpiar separadores de miles y convertir
                chunk[col] = chunk[col].str.replace(',', '', regex=False) if chunk[col].dtype == 'object' else chunk[col]
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce')
        
        # Convertir fechas
        date_cols = ['fecha_radicacion', 'fecha_acto']
        for col in date_cols:
            if col in chunk.columns:
                chunk[col] = pd.to_datetime(chunk[col], errors='coerce')
        
        # Normalizar texto
        text_cols = ['departamento', 'municipio', 'tipo_acto', 'nombre_natujur', 
                    'tipo_predio', 'estado_folio', 'matricula']
        for col in text_cols:
            if col in chunk.columns:
                chunk[col] = chunk[col].str.upper().str.strip()
                chunk[col] = chunk[col].replace('NAN', None)
        
        # Convertir a PyArrow
        table = pa.Table.from_pandas(chunk)
        
        # Primera vez: crear writer con schema
        if writer is None:
            schema = table.schema
            writer = pq.ParquetWriter(output_path, schema, compression='snappy')
        else:
            # Adaptar schema del chunk al schema original
            table = table.cast(schema)
        
        # Escribir chunk
        writer.write_table(table)
        
        total_rows += len(chunk)
        elapsed = (datetime.now() - chunk_start).total_seconds()
        rows_per_sec = len(chunk) / elapsed if elapsed > 0 else 0
        
        print(f"Chunk {i+1:,}: {len(chunk):,} rows | "
              f"{rows_per_sec:,.0f} rows/sec | "
              f"Total: {total_rows:,}")
    
    # Cerrar writer
    if writer:
        writer.close()
    
    # Stats finales
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    input_size_gb = input_path.stat().st_size / (1024**3)
    output_size_gb = output_path.stat().st_size / (1024**3)
    compression_ratio = input_size_gb / output_size_gb
    
    print("\n" + "="*80)
    print("✅ CONVERSION COMPLETED")
    print("="*80)
    print(f"Duration:     {duration:.2f}s ({duration/60:.2f} min)")
    print(f"Throughput:   {total_rows/duration:,.0f} rows/sec")
    print(f"Total rows:   {total_rows:,}")
    print(f"Input size:   {input_size_gb:.2f} GB")
    print(f"Output size:  {output_size_gb:.2f} GB")
    print(f"Compression:  {compression_ratio:.1f}x")
    print(f"Output:       {output_path}")
    print("="*80)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
