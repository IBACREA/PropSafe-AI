"""
Verificar lógica de discrepancia geográfica ORIP vs DIVIPOLA
"""
import pandas as pd
import pyarrow.parquet as pq

# Cargar muestra
print("Cargando muestra...")
parquet_file = pq.ParquetFile("data/processed/datos.parquet")
batch = next(parquet_file.iter_batches(batch_size=10000))
df = batch.to_pandas()

print(f"\nMuestra: {len(df):,} registros")
print("\n=== Estructura ORIP ===")
print(df['ORIP'].describe())
print("\nEjemplos ORIP:")
print(df['ORIP'].head(20))

print("\n=== Estructura DIVIPOLA ===")
print(df['DIVIPOLA'].describe())
print("\nEjemplos DIVIPOLA:")
print(df['DIVIPOLA'].head(20))
print(f"\nTipo: {df['DIVIPOLA'].dtype}")

# Ver combinaciones reales
print("\n=== Combinaciones ORIP + DIVIPOLA (primeras 20) ===")
sample = df[['ORIP', 'DIVIPOLA', 'DEPARTAMENTO', 'MUNICIPIO']].head(20)
print(sample.to_string())

# Análisis de estructura
print("\n=== Análisis Códigos ===")
df_analyze = df.copy()
df_analyze['orip_int'] = df_analyze['ORIP'].astype('Int64')
df_analyze['divipola_len'] = df_analyze['DIVIPOLA'].astype(str).str.len()
df_analyze['divipola_depto'] = df_analyze['DIVIPOLA'].astype(str).str[:2]

print("\nLongitud DIVIPOLA:")
print(df_analyze['divipola_len'].value_counts())

print("\nPrimeros 2 dígitos DIVIPOLA (código departamento):")
print(df_analyze['divipola_depto'].value_counts().head(10))

print("\nORIP únicos:")
print(f"Total: {df_analyze['orip_int'].nunique()}")
print("\nMás comunes:")
print(df_analyze['orip_int'].value_counts().head(10))

print("\n=== Mapeo ORIP -> Departamento Real ===")
orip_depto = df_analyze.groupby('orip_int')['DEPARTAMENTO'].agg(lambda x: x.value_counts().index[0] if len(x) > 0 else None)
print(orip_depto.head(20))
