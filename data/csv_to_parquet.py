#!/usr/bin/env python3
"""
Convertir CSV grande a Parquet con validación y limpieza

Usage:
    python csv_to_parquet.py --input data/raw/datos.csv --output data/processed/datos.parquet
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

def clean_text(text):
    """Limpiar texto: uppercase, strip"""
    if pd.isna(text):
        return None
    return str(text).strip().upper()

def validate_numeric(value, min_val=0, max_val=None):
    """Validar valores numéricos"""
    if pd.isna(value):
        return None
    try:
        val = float(value)
        if val < min_val:
            return None
        if max_val and val > max_val:
            return max_val
        return val
    except:
        return None

def process_chunk(chunk):
    """Procesar chunk de datos"""
    # Limpieza de texto
    text_cols = ['departamento', 'municipio', 'tipo_acto', 'tipo_predio', 
                 'estado_folio', 'nombre_natujur']
    for col in text_cols:
        if col in chunk.columns:
            chunk[col] = chunk[col].apply(clean_text)
    
    # Validación de valores numéricos
    numeric_cols = {
        'valor_acto': (0, 1e12),
        'area_terreno': (0, 1e8),
        'area_construida': (0, 1e8),
        'numero_intervinientes': (1, 100),
        'count_a': (0, 100),
        'count_de': (0, 100),
        'ORIP': (0, 10000)
    }
    
    for col, (min_val, max_val) in numeric_cols.items():
        if col in chunk.columns:
            chunk[col] = chunk[col].apply(
                lambda x: validate_numeric(x, min_val=min_val, max_val=max_val)
            )
    
    # Validar fechas
    date_cols = ['fecha_radicacion', 'fecha_acto']
    for col in date_cols:
        if col in chunk.columns:
            chunk[col] = pd.to_datetime(chunk[col], errors='coerce')
    
    return chunk

def convert_csv_to_parquet(input_path: str, output_path: str, batch_size: int = 10000):
    """Convertir CSV a Parquet con procesamiento por chunks"""
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("CSV → PARQUET CONVERSION")
    print("="*80)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print(f"Batch:  {batch_size:,} rows")
    print("="*80)
    
    start_time = datetime.now()
    
    # Leer CSV en chunks
    chunks_processed = []
    total_rows = 0
    rejected_rows = 0
    
    try:
        reader = pd.read_csv(
            input_file,
            chunksize=batch_size,
            encoding='utf-8',
            low_memory=False
        )
        
        for i, chunk in enumerate(reader):
            chunk_start = datetime.now()
            
            # Procesar chunk
            original_count = len(chunk)
            processed_chunk = process_chunk(chunk)
            
            # Eliminar filas completamente nulas
            processed_chunk = processed_chunk.dropna(how='all')
            valid_count = len(processed_chunk)
            rejected_rows += (original_count - valid_count)
            
            chunks_processed.append(processed_chunk)
            total_rows += valid_count
            
            # Progress
            elapsed = (datetime.now() - chunk_start).total_seconds()
            rows_per_sec = valid_count / elapsed if elapsed > 0 else 0
            
            print(f"Chunk {i+1:,}: {valid_count:,} rows | "
                  f"{rows_per_sec:,.0f} rows/sec | "
                  f"Total: {total_rows:,}")
            
    except Exception as e:
        print(f"\n❌ Error reading CSV: {e}")
        sys.exit(1)
    
    # Combinar todos los chunks
    print("\n" + "="*80)
    print("Combining chunks and saving...")
    print("="*80)
    
    try:
        df_final = pd.concat(chunks_processed, ignore_index=True)
        
        # Guardar como Parquet
        df_final.to_parquet(
            output_file,
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        
        # Stats
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Tamaños de archivo
        input_size_gb = input_file.stat().st_size / (1024**3)
        output_size_gb = output_file.stat().st_size / (1024**3)
        compression_ratio = input_size_gb / output_size_gb if output_size_gb > 0 else 0
        
        print("\n" + "="*80)
        print("✅ CONVERSION COMPLETED")
        print("="*80)
        print(f"Duration:     {duration:.2f} seconds ({duration/60:.2f} minutes)")
        print(f"Throughput:   {total_rows/duration:,.0f} rows/sec")
        print(f"Total rows:   {total_rows:,}")
        print(f"Rejected:     {rejected_rows:,} ({rejected_rows/(total_rows+rejected_rows)*100:.2f}%)")
        print(f"Input size:   {input_size_gb:.2f} GB")
        print(f"Output size:  {output_size_gb:.2f} GB")
        print(f"Compression:  {compression_ratio:.1f}x")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error saving Parquet: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Convert CSV to Parquet')
    parser.add_argument('--input', type=str, required=True,
                       help='Path to input CSV file')
    parser.add_argument('--output', type=str, required=True,
                       help='Path to output Parquet file')
    parser.add_argument('--batch-size', type=int, default=10000,
                       help='Number of rows per batch (default: 10000)')
    
    args = parser.parse_args()
    
    # Check input exists
    if not Path(args.input).exists():
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)
    
    # Run conversion
    convert_csv_to_parquet(args.input, args.output, args.batch_size)

if __name__ == '__main__':
    main()
