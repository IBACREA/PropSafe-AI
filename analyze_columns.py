"""
Análisis detallado de columnas del dataset de transacciones inmobiliarias
"""
import pandas as pd
import numpy as np

# Cargar datos
df = pd.read_parquet('data/processed/datos.parquet')

print('=' * 100)
print('ANÁLISIS DETALLADO DE CAMPOS - TRANSACCIONES INMOBILIARIAS COLOMBIA')
print('=' * 100)
print(f'\nTotal registros: {len(df):,}')
print(f'Total columnas: {len(df.columns)}')

print('\n' + '=' * 100)
print('ANÁLISIS POR CAMPO:')
print('=' * 100)

for col in df.columns:
    dtype = df[col].dtype
    nulls = df[col].isna().sum()
    null_pct = (nulls / len(df)) * 100
    unique = df[col].nunique()
    
    print(f'\n📊 {col}')
    print(f'   Tipo: {dtype}')
    print(f'   Nulos: {nulls:,} ({null_pct:.1f}%)')
    print(f'   Valores únicos: {unique:,}')
    
    # Para categóricas con pocos valores
    if dtype == 'object' and unique <= 50:
        print(f'   Top valores:')
        for val, count in df[col].value_counts().head(5).items():
            print(f'      - {val}: {count:,} ({count/len(df)*100:.1f}%)')
    
    # Para numéricas
    elif dtype in ['int64', 'float64'] and col != 'PK':
        if nulls < len(df):  # Si no todo es nulo
            non_null = df[col].dropna()
            print(f'   Min: {non_null.min():.2f}')
            print(f'   Max: {non_null.max():.2f}')
            print(f'   Media: {non_null.mean():.2f}')
            print(f'   Mediana: {non_null.median():.2f}')

print('\n' + '=' * 100)
print('ANÁLISIS ESPECIAL: VALOR (Variable Objetivo)')
print('=' * 100)

# Análisis detallado de VALOR
print(f'\nValores totales: {len(df):,}')
print(f'Valores con VALOR: {df["VALOR"].notna().sum():,} ({df["VALOR"].notna().sum()/len(df)*100:.1f}%)')
print(f'Valores sin VALOR: {df["VALOR"].isna().sum():,} ({df["VALOR"].isna().sum()/len(df)*100:.1f}%)')

valor_non_null = df[df["VALOR"].notna()].copy()
if len(valor_non_null) > 0:
    # Convertir VALOR a numérico (puede tener comas o formato texto)
    valor_non_null['VALOR_NUM'] = pd.to_numeric(valor_non_null["VALOR"].astype(str).str.replace(',', ''), errors='coerce')
    valor_non_null = valor_non_null[valor_non_null['VALOR_NUM'].notna()]
    
    print(f'\nEstadísticas de VALOR (cuando existe y es numérico):')
    print(f'   Registros con VALOR numérico: {len(valor_non_null):,}')
    print(f'   Min: ${valor_non_null["VALOR_NUM"].min():,.0f} COP')
    print(f'   Max: ${valor_non_null["VALOR_NUM"].max():,.0f} COP')
    print(f'   Media: ${valor_non_null["VALOR_NUM"].mean():,.0f} COP')
    print(f'   Mediana: ${valor_non_null["VALOR_NUM"].median():,.0f} COP')
    
    # Distribución por rangos
    print(f'\n   Distribución por rangos:')
    bins = [0, 10_000_000, 50_000_000, 100_000_000, 500_000_000, float('inf')]
    labels = ['< 10M', '10M-50M', '50M-100M', '100M-500M', '> 500M']
    valor_non_null['rango'] = pd.cut(valor_non_null["VALOR_NUM"], bins=bins, labels=labels)
    for rango, count in valor_non_null['rango'].value_counts().sort_index().items():
        print(f'      {rango}: {count:,} ({count/len(valor_non_null)*100:.1f}%)')

print('\n' + '=' * 100)
print('ANÁLISIS: Dinámica_Inmobiliaria (Filtro de mercado)')
print('=' * 100)

print(f'\nDinámica_Inmobiliaria = 1 (mercado): {(df["Dinámica_Inmobiliaria"]==1).sum():,} ({(df["Dinámica_Inmobiliaria"]==1).sum()/len(df)*100:.1f}%)')
print(f'Dinámica_Inmobiliaria = 0 (no mercado): {(df["Dinámica_Inmobiliaria"]==0).sum():,} ({(df["Dinámica_Inmobiliaria"]==0).sum()/len(df)*100:.1f}%)')

# Cuántos tienen VALOR en mercado vs no mercado
mercado = df[df["Dinámica_Inmobiliaria"] == 1]
no_mercado = df[df["Dinámica_Inmobiliaria"] == 0]

print(f'\nEn Dinámica_Inmobiliaria = 1:')
print(f'   Con VALOR: {mercado["VALOR"].notna().sum():,} ({mercado["VALOR"].notna().sum()/len(mercado)*100:.1f}%)')
print(f'   Sin VALOR: {mercado["VALOR"].isna().sum():,} ({mercado["VALOR"].isna().sum()/len(mercado)*100:.1f}%)')

print(f'\nEn Dinámica_Inmobiliaria = 0:')
print(f'   Con VALOR: {no_mercado["VALOR"].notna().sum():,} ({no_mercado["VALOR"].notna().sum()/len(no_mercado)*100:.1f}%)')
print(f'   Sin VALOR: {no_mercado["VALOR"].isna().sum():,} ({no_mercado["VALOR"].isna().sum()/len(no_mercado)*100:.1f}%)')

print('\n' + '=' * 100)
print('ANÁLISIS GEOGRÁFICO')
print('=' * 100)

print(f'\nDepartamentos únicos: {df["DEPARTAMENTO"].nunique()}')
print(f'Municipios únicos: {df["MUNICIPIO"].nunique()}')

print(f'\nTop 10 departamentos por transacciones:')
for dept, count in df["DEPARTAMENTO"].value_counts().head(10).items():
    print(f'   {dept}: {count:,} ({count/len(df)*100:.1f}%)')

print(f'\nTop 10 municipios por transacciones:')
for mun, count in df["MUNICIPIO"].value_counts().head(10).items():
    print(f'   {mun}: {count:,} ({count/len(df)*100:.1f}%)')

print('\n' + '=' * 100)
print('ANÁLISIS TEMPORAL')
print('=' * 100)

print(f'\nAños únicos: {df["YEAR_RADICA"].nunique()}')
print(f'Rango: {df["YEAR_RADICA"].min()} - {df["YEAR_RADICA"].max()}')

print(f'\nDistribución por año:')
for year, count in df["YEAR_RADICA"].value_counts().sort_index().items():
    print(f'   {int(year)}: {count:,} ({count/len(df)*100:.1f}%)')

print('\n' + '=' * 100)
print('RECOMENDACIONES PARA FEATURE ENGINEERING')
print('=' * 100)

print("""
✅ CAMPOS ALTAMENTE ÚTILES (USAR SIEMPRE):

1. VALOR - Variable objetivo principal (detección de anomalías en precios)
2. DEPARTAMENTO - Contexto geográfico crítico (precios varían por región)
3. MUNICIPIO - Granularidad geográfica fina (Bogotá ≠ pueblo pequeño)
4. YEAR_RADICA - Tendencias temporales, inflación, ciclos mercado
5. TIPO_PREDIO_ZONA - Urbano/Rural afecta dramáticamente precios
6. Dinámica_Inmobiliaria - FILTRO CRÍTICO (1 = transacciones reales mercado)

✅ CAMPOS ÚTILES (INCLUIR SI DISPONIBLES):

7. CATEGORIA_RURALIDAD - Refina clasificación urbano/rural
8. COUNT_A, COUNT_DE - Volumen transacciones (puede indicar fraude)
9. PREDIOS_NUEVOS - Construcciones nuevas vs usadas
10. TIENE_VALOR, TIENE_MAS_DE_UN_VALOR - Flags de validación
11. COD_NATUJUR - Naturaleza jurídica (persona natural vs jurídica, puede indicar patrones)

⚠️ CAMPOS DE DUDOSA UTILIDAD (EVALUAR):

12. ORIP - Código oficina, geografía implícita pero ya tenemos DEPTO/MUNICIPIO
13. DIVIPOLA - Código geográfico redundante con DEPTO/MUNICIPIO
14. ESTADO_FOLIO - Podría ser útil si "cancelado" indica fraude
15. NUM_ANOTACION - ID secuencial, sin valor predictivo directo
16. NUMERO_CATASTRAL, NUMERO_CATASTRAL_ANTIGUO - Identificadores, no features

❌ CAMPOS NO ÚTILES (EXCLUIR):

17. PK - ID autoincremental sin significado
18. MATRICULA - Identificador único del predio
19. FECHA_RADICA_TEXTO, FECHA_APERTURA_TEXTO - Redundantes con YEAR_RADICA
20. FOLIOS_DERIVADOS - Metadata interna
21. DOCUMENTO_JUSTIFICATIVO - Texto libre sin valor predictivo
22. NOMBRE_NATUJUR - Texto, redundante con COD_NATUJUR

💡 ESTRATEGIA RECOMENDADA:

FASE 1 - FEATURES CORE (6-8 features):
- VALOR (normalizado por región/año)
- DEPARTAMENTO (label encoding o one-hot top 10)
- MUNICIPIO (label encoding o one-hot top 20)
- YEAR_RADICA (normalizado, + features derivados: años_desde_2000, es_reciente)
- TIPO_PREDIO_ZONA (one-hot: urbano/rural/mixto)
- CATEGORIA_RURALIDAD (one-hot si disponible)
- Ratio: VALOR / mediana_valor_departamento_año (detecta outliers)
- Ratio: VALOR / mediana_valor_municipio_año (granularidad fina)

FASE 2 - FEATURES AGREGADOS (10-15 features adicionales):
- Media VALOR por DEPARTAMENTO + YEAR_RADICA
- Mediana VALOR por MUNICIPIO + YEAR_RADICA
- Desviación estándar VALOR por región
- COUNT_A, COUNT_DE (frecuencia transacciones)
- PREDIOS_NUEVOS (flag booleano)
- COD_NATUJUR (encoding simplificado)
- Interacciones: DEPARTAMENTO × YEAR_RADICA
- Z-score de VALOR dentro de su grupo (DEPTO + AÑO + TIPO_PREDIO)

FILTROS PREVIOS:
1. Dinámica_Inmobiliaria == 1 (OBLIGATORIO)
2. VALOR IS NOT NULL (OBLIGATORIO para entrenamiento)
3. YEAR_RADICA >= 2010 (opcional, si años antiguos tienen calidad dudosa)

RESULTADO ESPERADO: 15-25 features bien construidos que capturen:
- Valor absoluto y relativo
- Contexto geográfico (región + ciudad)
- Contexto temporal (año + tendencias)
- Tipo de propiedad
- Patrones de transacción
""")
