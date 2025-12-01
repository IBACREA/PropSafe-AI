"""Test rápido de búsqueda de propiedades"""
import sys
sys.path.insert(0, 'D:/projects/datos')

import pandas as pd
from pathlib import Path

# Path al dataset
data_path = Path('D:/projects/datos/data/processed/snr_synthetic.parquet')

print(f"Dataset existe: {data_path.exists()}")

if data_path.exists():
    df = pd.read_parquet(data_path)
    print(f"\nTotal registros: {len(df)}")
    print(f"Columnas: {df.columns.tolist()}")
    
    # Probar búsqueda
    matricula_test = "110814602"
    result = df[df['matricula'] == matricula_test]
    
    print(f"\nBuscando matrícula: {matricula_test}")
    print(f"Encontrados: {len(result)}")
    
    if len(result) > 0:
        print("\nPrimeros resultados:")
        print(result[['matricula', 'municipio', 'valor_acto', 'nombre_natujur']].to_string())
