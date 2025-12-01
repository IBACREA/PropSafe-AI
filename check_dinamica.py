"""
Verificar Dinámica_Inmobiliaria correctamente
"""
import pandas as pd

df = pd.read_parquet('data/processed/datos.parquet')

print('=' * 80)
print('ANÁLISIS CORRECTO DE Dinámica_Inmobiliaria')
print('=' * 80)

print(f'\nTipo de dato: {df["Dinámica_Inmobiliaria"].dtype}')

print(f'\nValores únicos y conteos:')
print(df['Dinámica_Inmobiliaria'].value_counts())

print(f'\nPrimeros 50 valores:')
print(df['Dinámica_Inmobiliaria'].head(50).tolist())

print(f'\n\nPRUEBA DE FILTROS:')
print('=' * 80)

# Probar diferentes tipos de filtro
filtro_str_1 = df[df['Dinámica_Inmobiliaria'] == '1']
print(f'\nFiltro con == "1" (string): {len(filtro_str_1):,} registros')

filtro_int_1 = df[df['Dinámica_Inmobiliaria'] == 1]
print(f'Filtro con == 1 (int): {len(filtro_int_1):,} registros')

filtro_str_0 = df[df['Dinámica_Inmobiliaria'] == '0']
print(f'Filtro con == "0" (string): {len(filtro_str_0):,} registros')

filtro_int_0 = df[df['Dinámica_Inmobiliaria'] == 0]
print(f'Filtro con == 0 (int): {len(filtro_int_0):,} registros')

print(f'\n\nMUESTRA DE DATOS CON DINÁMICA = 1:')
print('=' * 80)
muestra = df[df['Dinámica_Inmobiliaria'] == '1'].head(10)
print(muestra[['DEPARTAMENTO', 'MUNICIPIO', 'YEAR_RADICA', 'VALOR', 'TIPO_PREDIO_ZONA', 'Dinámica_Inmobiliaria']])

print(f'\n\nMUESTRA DE DATOS CON DINÁMICA = 0:')
print('=' * 80)
muestra0 = df[df['Dinámica_Inmobiliaria'] == '0'].head(10)
print(muestra0[['DEPARTAMENTO', 'MUNICIPIO', 'YEAR_RADICA', 'VALOR', 'TIPO_PREDIO_ZONA', 'Dinámica_Inmobiliaria']])

print(f'\n\nANÁLISIS DE VALOR POR DINÁMICA:')
print('=' * 80)

# Convertir VALOR a numérico
df_temp = df.copy()
df_temp['VALOR_NUM'] = pd.to_numeric(
    df_temp['VALOR'].astype(str).str.replace(',', ''), 
    errors='coerce'
)

# Análisis para Dinámica = '1'
din1 = df_temp[df_temp['Dinámica_Inmobiliaria'] == '1']
print(f'\nDinámica_Inmobiliaria = "1":')
print(f'   Total registros: {len(din1):,}')
print(f'   Con VALOR no nulo: {din1["VALOR"].notna().sum():,}')
print(f'   Con VALOR numérico: {din1["VALOR_NUM"].notna().sum():,}')
print(f'   VALOR = 0: {(din1["VALOR_NUM"] == 0).sum():,}')
print(f'   VALOR > 0: {(din1["VALOR_NUM"] > 0).sum():,}')
if (din1["VALOR_NUM"] > 0).sum() > 0:
    valores_validos = din1[din1["VALOR_NUM"] > 0]["VALOR_NUM"]
    print(f'   Media (excluyendo 0): ${valores_validos.mean():,.0f} COP')
    print(f'   Mediana (excluyendo 0): ${valores_validos.median():,.0f} COP')

# Análisis para Dinámica = '0'
din0 = df_temp[df_temp['Dinámica_Inmobiliaria'] == '0']
print(f'\nDinámica_Inmobiliaria = "0":')
print(f'   Total registros: {len(din0):,}')
print(f'   Con VALOR no nulo: {din0["VALOR"].notna().sum():,}')
print(f'   Con VALOR numérico: {din0["VALOR_NUM"].notna().sum():,}')
print(f'   VALOR = 0: {(din0["VALOR_NUM"] == 0).sum():,}')
print(f'   VALOR > 0: {(din0["VALOR_NUM"] > 0).sum():,}')
if (din0["VALOR_NUM"] > 0).sum() > 0:
    valores_validos = din0[din0["VALOR_NUM"] > 0]["VALOR_NUM"]
    print(f'   Media (excluyendo 0): ${valores_validos.mean():,.0f} COP')
    print(f'   Mediana (excluyendo 0): ${valores_validos.median():,.0f} COP')
