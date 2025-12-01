"""
Análisis de valores problemáticos en el campo VALOR
"""
import pandas as pd
import numpy as np

# Cargar datos
df = pd.read_parquet('data/processed/datos.parquet')

# Filtrar solo registros con VALOR
df_valor = df[df['VALOR'].notna()].copy()
df_valor['VALOR_STR'] = df_valor['VALOR'].astype(str)

print('=' * 100)
print('ANÁLISIS DE VALORES PROBLEMÁTICOS EN CAMPO VALOR')
print('=' * 100)
print(f'\nTotal registros con VALOR no-nulo: {len(df_valor):,}')

# 1. VALORES IGUAL A CERO
print('\n' + '=' * 100)
print('1. VALORES IGUAL A CERO')
print('=' * 100)

ceros = df_valor[df_valor['VALOR_STR'].str.strip() == '0']
print(f'\nCount: {len(ceros):,} ({len(ceros)/len(df_valor)*100:.2f}%)')
print('\nMuestra de registros con valor = 0:')
print(ceros[['DEPARTAMENTO', 'MUNICIPIO', 'YEAR_RADICA', 'VALOR', 'TIPO_PREDIO_ZONA', 'Dinámica_Inmobiliaria']].head(15).to_string())

# 2. VALORES NO NUMÉRICOS
print('\n' + '=' * 100)
print('2. VALORES NO NUMÉRICOS (contienen letras, símbolos, etc.)')
print('=' * 100)

df_valor['VALOR_NUMERIC'] = pd.to_numeric(
    df_valor['VALOR_STR'].str.replace(',', ''), 
    errors='coerce'
)
no_numericos = df_valor[df_valor['VALOR_NUMERIC'].isna()]

print(f'\nCount: {len(no_numericos):,} ({len(no_numericos)/len(df_valor)*100:.2f}%)')

if len(no_numericos) > 0:
    print('\nMuestra de valores NO numéricos:')
    print(no_numericos[['DEPARTAMENTO', 'MUNICIPIO', 'YEAR_RADICA', 'VALOR', 'TIPO_PREDIO_ZONA']].head(25).to_string())
    
    print('\nValores únicos NO numéricos (primeros 50):')
    valores_unicos = no_numericos['VALOR'].value_counts().head(50)
    for valor, count in valores_unicos.items():
        print(f'   "{valor}": {count:,} veces')

# 3. VALORES EXTREMOS
print('\n' + '=' * 100)
print('3. VALORES EXTREMOS (> 10 mil millones COP)')
print('=' * 100)

numericos = df_valor[df_valor['VALOR_NUMERIC'].notna()]
extremos = numericos[numericos['VALOR_NUMERIC'] > 10_000_000_000]

print(f'\nCount: {len(extremos):,} ({len(extremos)/len(df_valor)*100:.2f}%)')
print('\nTop 30 valores más altos:')
print(extremos.nlargest(30, 'VALOR_NUMERIC')[
    ['DEPARTAMENTO', 'MUNICIPIO', 'YEAR_RADICA', 'VALOR', 'VALOR_NUMERIC', 'TIPO_PREDIO_ZONA']
].to_string())

# 4. VALORES MUY PEQUEÑOS (< 1 millón COP)
print('\n' + '=' * 100)
print('4. VALORES MUY PEQUEÑOS (< 1 millón COP)')
print('=' * 100)

pequenos = numericos[
    (numericos['VALOR_NUMERIC'] > 0) & 
    (numericos['VALOR_NUMERIC'] < 1_000_000)
]
print(f'\nCount: {len(pequenos):,} ({len(pequenos)/len(df_valor)*100:.2f}%)')
print('\nMuestra de valores muy pequeños:')
print(pequenos[['DEPARTAMENTO', 'MUNICIPIO', 'YEAR_RADICA', 'VALOR_NUMERIC', 'TIPO_PREDIO_ZONA']].head(20).to_string())

# 5. DISTRIBUCIÓN VALORES VÁLIDOS
print('\n' + '=' * 100)
print('5. DISTRIBUCIÓN VALORES VÁLIDOS (1M - 10B COP)')
print('=' * 100)

validos = numericos[
    (numericos['VALOR_NUMERIC'] >= 1_000_000) & 
    (numericos['VALOR_NUMERIC'] <= 10_000_000_000)
]

print(f'\nCount válidos: {len(validos):,} ({len(validos)/len(df_valor)*100:.2f}%)')
print(f'Media: ${validos["VALOR_NUMERIC"].mean():,.0f} COP')
print(f'Mediana: ${validos["VALOR_NUMERIC"].median():,.0f} COP')
print(f'Std Dev: ${validos["VALOR_NUMERIC"].std():,.0f} COP')

# Distribución por rangos
print('\nDistribución por rangos:')
bins = [
    1_000_000, 
    10_000_000, 
    50_000_000, 
    100_000_000, 
    500_000_000, 
    1_000_000_000,
    10_000_000_000
]
labels = [
    '1M-10M', 
    '10M-50M', 
    '50M-100M', 
    '100M-500M', 
    '500M-1B',
    '1B-10B'
]

validos['rango'] = pd.cut(validos['VALOR_NUMERIC'], bins=bins, labels=labels)
for rango, count in validos['rango'].value_counts().sort_index().items():
    print(f'   {rango}: {count:,} ({count/len(validos)*100:.1f}%)')

# 6. RESUMEN POR Dinámica_Inmobiliaria
print('\n' + '=' * 100)
print('6. COMPARACIÓN: Dinámica_Inmobiliaria = 1 vs 0')
print('=' * 100)

mercado = numericos[numericos['Dinámica_Inmobiliaria'] == '1']
no_mercado = numericos[numericos['Dinámica_Inmobiliaria'] == '0']

print(f'\nDinámica_Inmobiliaria = 1 (mercado):')
print(f'   Total: {len(mercado):,}')
print(f'   Ceros: {(mercado["VALOR_NUMERIC"] == 0).sum():,}')
print(f'   Válidos (1M-10B): {((mercado["VALOR_NUMERIC"] >= 1_000_000) & (mercado["VALOR_NUMERIC"] <= 10_000_000_000)).sum():,}')
print(f'   Media válidos: ${mercado[(mercado["VALOR_NUMERIC"] >= 1_000_000) & (mercado["VALOR_NUMERIC"] <= 10_000_000_000)]["VALOR_NUMERIC"].mean():,.0f}')

print(f'\nDinámica_Inmobiliaria = 0 (no mercado):')
print(f'   Total: {len(no_mercado):,}')
print(f'   Ceros: {(no_mercado["VALOR_NUMERIC"] == 0).sum():,}')
print(f'   Válidos (1M-10B): {((no_mercado["VALOR_NUMERIC"] >= 1_000_000) & (no_mercado["VALOR_NUMERIC"] <= 10_000_000_000)).sum():,}')
if len(no_mercado[(no_mercado["VALOR_NUMERIC"] >= 1_000_000) & (no_mercado["VALOR_NUMERIC"] <= 10_000_000_000)]) > 0:
    print(f'   Media válidos: ${no_mercado[(no_mercado["VALOR_NUMERIC"] >= 1_000_000) & (no_mercado["VALOR_NUMERIC"] <= 10_000_000_000)]["VALOR_NUMERIC"].mean():,.0f}')

print('\n' + '=' * 100)
print('RECOMENDACIÓN FINAL DE LIMPIEZA')
print('=' * 100)
print("""
Aplicar los siguientes filtros en orden:

1. Dinámica_Inmobiliaria == '1' (solo transacciones de mercado)
2. VALOR IS NOT NULL
3. VALOR es numérico (eliminar textos/símbolos)
4. VALOR >= 1,000,000 (mínimo 1 millón COP ~ $250 USD)
5. VALOR <= 10,000,000,000 (máximo 10 mil millones COP ~ $2.5M USD)

Registros esperados después de filtros:
""")

# Calcular registros finales
df_limpio = df[df['Dinámica_Inmobiliaria'] == '1'].copy()
print(f'   Paso 1 (Dinámica=1): {len(df_limpio):,}')

df_limpio = df_limpio[df_limpio['VALOR'].notna()]
print(f'   Paso 2 (VALOR no nulo): {len(df_limpio):,}')

df_limpio['VALOR_NUM'] = pd.to_numeric(
    df_limpio['VALOR'].astype(str).str.replace(',', ''), 
    errors='coerce'
)
df_limpio = df_limpio[df_limpio['VALOR_NUM'].notna()]
print(f'   Paso 3 (VALOR numérico): {len(df_limpio):,}')

df_limpio = df_limpio[
    (df_limpio['VALOR_NUM'] >= 1_000_000) & 
    (df_limpio['VALOR_NUM'] <= 10_000_000_000)
]
print(f'   Paso 4-5 (Rango válido): {len(df_limpio):,}')
print(f'\n✅ DATASET LIMPIO: {len(df_limpio):,} registros ({len(df_limpio)/len(df)*100:.1f}% del total)')
print(f'   Media: ${df_limpio["VALOR_NUM"].mean():,.0f} COP')
print(f'   Mediana: ${df_limpio["VALOR_NUM"].median():,.0f} COP')
