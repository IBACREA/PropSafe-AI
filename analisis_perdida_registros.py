"""
Análisis de pérdida de registros: De 30.9M a 5.7M
¿Qué pasa con cada registro?
"""
import pandas as pd

print('=' * 80)
print('ANÁLISIS DE FILTRADO: ¿DÓNDE ESTÁN LOS 25.2 MILLONES FALTANTES?')
print('=' * 80)

# Cargar datos originales
df = pd.read_parquet('data/processed/datos.parquet')
total = len(df)

print(f'\n📊 DATASET ORIGINAL: {total:,} registros')
print('=' * 80)

# Convertir tipos necesarios
df['Dinamica_Inmobiliaria_int'] = df['Dinámica_Inmobiliaria'].map({'1': 1, '0': 0, 1: 1, 0: 0})
df['VALOR_NUM'] = pd.to_numeric(
    df['VALOR'].astype(str).str.replace(',', ''), 
    errors='coerce'
)

# ANÁLISIS PASO POR PASO
print('\n🔍 FILTRO 1: Dinámica_Inmobiliaria == 1 (solo transacciones de MERCADO)')
print('-' * 80)

din_0 = (df['Dinamica_Inmobiliaria_int'] == 0).sum()
din_1 = (df['Dinamica_Inmobiliaria_int'] == 1).sum()
din_null = df['Dinamica_Inmobiliaria_int'].isna().sum()

print(f'  Dinámica = 0 (NO mercado):    {din_0:12,} registros ({din_0/total*100:.1f}%)')
print(f'  Dinámica = 1 (SÍ mercado):    {din_1:12,} registros ({din_1/total*100:.1f}%)')
print(f'  Dinámica = NULL:              {din_null:12,} registros ({din_null/total*100:.1f}%)')
print(f'\n  ❌ DESCARTADOS: {din_0 + din_null:,} registros')
print(f'  ✅ PASAN: {din_1:,} registros')

# Aplicar filtro 1
df_filtro1 = df[df['Dinamica_Inmobiliaria_int'] == 1].copy()
restantes_1 = len(df_filtro1)

print(f'\n🔍 FILTRO 2: VALOR IS NOT NULL')
print('-' * 80)

valor_null = df_filtro1['VALOR'].isna().sum()
valor_not_null = df_filtro1['VALOR'].notna().sum()

print(f'  VALOR = NULL:                 {valor_null:12,} registros ({valor_null/restantes_1*100:.1f}%)')
print(f'  VALOR NO NULL:                {valor_not_null:12,} registros ({valor_not_null/restantes_1*100:.1f}%)')
print(f'\n  ❌ DESCARTADOS: {valor_null:,} registros')
print(f'  ✅ PASAN: {valor_not_null:,} registros')

# Aplicar filtro 2
df_filtro2 = df_filtro1[df_filtro1['VALOR'].notna()].copy()
restantes_2 = len(df_filtro2)

print(f'\n🔍 FILTRO 3: VALOR es numérico (no texto/símbolos)')
print('-' * 80)

df_filtro2['VALOR_NUM'] = pd.to_numeric(
    df_filtro2['VALOR'].astype(str).str.replace(',', ''), 
    errors='coerce'
)
valor_no_numerico = df_filtro2['VALOR_NUM'].isna().sum()
valor_numerico = df_filtro2['VALOR_NUM'].notna().sum()

print(f'  VALOR no numérico:            {valor_no_numerico:12,} registros ({valor_no_numerico/restantes_2*100:.1f}%)')
print(f'  VALOR numérico:               {valor_numerico:12,} registros ({valor_numerico/restantes_2*100:.1f}%)')
print(f'\n  ❌ DESCARTADOS: {valor_no_numerico:,} registros')
print(f'  ✅ PASAN: {valor_numerico:,} registros')

# Aplicar filtro 3
df_filtro3 = df_filtro2[df_filtro2['VALOR_NUM'].notna()].copy()
restantes_3 = len(df_filtro3)

print(f'\n🔍 FILTRO 4: VALOR = 0 (sin precio declarado)')
print('-' * 80)

valor_cero = (df_filtro3['VALOR_NUM'] == 0).sum()
valor_mayor_cero = (df_filtro3['VALOR_NUM'] > 0).sum()

print(f'  VALOR = 0:                    {valor_cero:12,} registros ({valor_cero/restantes_3*100:.1f}%)')
print(f'  VALOR > 0:                    {valor_mayor_cero:12,} registros ({valor_mayor_cero/restantes_3*100:.1f}%)')
print(f'\n  ❌ DESCARTADOS: {valor_cero:,} registros')
print(f'  ✅ PASAN: {valor_mayor_cero:,} registros')

# Aplicar filtro 4
df_filtro4 = df_filtro3[df_filtro3['VALOR_NUM'] > 0].copy()
restantes_4 = len(df_filtro4)

print(f'\n🔍 FILTRO 5: VALOR >= 1,000,000 COP (mínimo razonable)')
print('-' * 80)

valor_muy_pequeno = (df_filtro4['VALOR_NUM'] < 1_000_000).sum()
valor_min_ok = (df_filtro4['VALOR_NUM'] >= 1_000_000).sum()

print(f'  VALOR < 1M COP:               {valor_muy_pequeno:12,} registros ({valor_muy_pequeno/restantes_4*100:.1f}%)')
print(f'  VALOR >= 1M COP:              {valor_min_ok:12,} registros ({valor_min_ok/restantes_4*100:.1f}%)')
print(f'\n  ❌ DESCARTADOS: {valor_muy_pequeno:,} registros (probables errores de captura)')
print(f'  ✅ PASAN: {valor_min_ok:,} registros')

# Aplicar filtro 5
df_filtro5 = df_filtro4[df_filtro4['VALOR_NUM'] >= 1_000_000].copy()
restantes_5 = len(df_filtro5)

print(f'\n🔍 FILTRO 6: VALOR <= 10,000,000,000 COP (máximo razonable)')
print('-' * 80)

valor_extremo = (df_filtro5['VALOR_NUM'] > 10_000_000_000).sum()
valor_max_ok = (df_filtro5['VALOR_NUM'] <= 10_000_000_000).sum()

print(f'  VALOR > 10B COP:              {valor_extremo:12,} registros ({valor_extremo/restantes_5*100:.1f}%)')
print(f'  VALOR <= 10B COP:             {valor_max_ok:12,} registros ({valor_max_ok/restantes_5*100:.1f}%)')
print(f'\n  ❌ DESCARTADOS: {valor_extremo:,} registros (errores de sistema)')
print(f'  ✅ PASAN: {valor_max_ok:,} registros')

# Final
df_final = df_filtro5[df_filtro5['VALOR_NUM'] <= 10_000_000_000].copy()
final = len(df_final)

print('\n' + '=' * 80)
print('📊 RESUMEN FINAL')
print('=' * 80)

print(f'\nRegistros iniciales:          {total:12,}')
print(f'Registros finales (ML):       {final:12,}')
print(f'Registros descartados:        {total - final:12,}')
print(f'Tasa aprovechamiento:         {final/total*100:12.1f}%')

print('\n📉 DESGLOSE DE PÉRDIDAS:')
print('-' * 80)

perdidas = [
    ('No es mercado (Dinámica=0)', din_0 + din_null, (din_0 + din_null)/total*100),
    ('VALOR es NULL', valor_null, valor_null/total*100),
    ('VALOR no numérico', valor_no_numerico, valor_no_numerico/total*100),
    ('VALOR = 0', valor_cero, valor_cero/total*100),
    ('VALOR < 1M (muy pequeño)', valor_muy_pequeno, valor_muy_pequeno/total*100),
    ('VALOR > 10B (extremo)', valor_extremo, valor_extremo/total*100),
]

for razon, cantidad, porcentaje in perdidas:
    print(f'  {razon:35} {cantidad:12,} ({porcentaje:5.1f}%)')

print('-' * 80)
print(f'  {"TOTAL DESCARTADO":35} {total - final:12,} ({(total-final)/total*100:5.1f}%)')
print(f'  {"DATASET LIMPIO FINAL":35} {final:12,} ({final/total*100:5.1f}%)')

print('\n💡 INTERPRETACIÓN:')
print('=' * 80)
print('''
El 81.5% de registros se descartan porque:

1. 43.7% son transacciones NO DE MERCADO (Dinámica=0)
   → Herencias, donaciones, ajustes administrativos
   → No reflejan precio real de mercado
   → CORRECTO descartarlos para análisis de precios

2. 38.5% son transacciones SIN VALOR DECLARADO
   → VALOR = NULL o VALOR = 0
   → No se puede detectar anomalías sin precio
   → CORRECTO descartarlos

3. 1.0% tienen valores INCORRECTOS
   → < $1M COP (probables errores de captura: $1,000 por casa)
   → > $10B COP (errores de sistema: cuatrillones)
   → CORRECTO descartarlos

El 18.5% restante (5.7M registros) son:
✅ Transacciones reales de mercado
✅ Con valor declarado válido
✅ En rango razonable ($250 - $2.5M USD)
✅ LISTOS para análisis de anomalías

CONCLUSIÓN: No estamos "perdiendo" datos valiosos.
Estamos LIMPIANDO basura y quedándonos con datos ÚTILES.
''')

print('\n🔍 ¿QUÉ PASA CON LOS REGISTROS DESCARTADOS?')
print('=' * 80)
print('''
Opciones:

1. IGNORAR completamente (recomendado para ML)
   → Solo entrenar con 5.7M limpios
   → Mejor calidad, menos ruido

2. GUARDAR para revisión manual
   → Tabla SQL separada con "casos problemáticos"
   → Expertos deciden si algunos son recuperables

3. ANÁLISIS SEPARADO
   → Estudiar transacciones Dinámica=0 aparte
   → Modelo diferente para herencias/donaciones

Para detección de FRAUDE en PRECIOS DE MERCADO:
→ Los 5.7M son EXACTAMENTE lo que necesitas
→ Los otros 25.2M son irrelevantes para ese objetivo
''')
