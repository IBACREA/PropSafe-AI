"""
Calcular espacio necesario en SQL para los datos
"""
import pandas as pd
import os
from pathlib import Path

print('=' * 80)
print('CÁLCULO DE ESPACIO NECESARIO PARA SQL')
print('=' * 80)

# Verificar si ya se procesaron los datos
clean_dir = Path('data/clean')

if clean_dir.exists() and list(clean_dir.glob('*.parquet')):
    print('\n📁 Archivos Parquet procesados:')
    print('-' * 80)
    
    files = list(clean_dir.glob('*.parquet'))
    total_parquet = 0
    
    for f in sorted(files):
        size_bytes = f.stat().st_size
        size_mb = size_bytes / 1024 / 1024
        total_parquet += size_bytes
        
        if size_mb > 1:  # Solo detallar archivos > 1MB
            df = pd.read_parquet(f)
            rows = len(df)
            cols = len(df.columns)
            row_size = size_bytes / rows if rows > 0 else 0
            print(f'  {f.name:45} {size_mb:8.2f} MB  {rows:12,} rows  {cols:3} cols  ~{row_size:.0f} bytes/row')
        else:
            print(f'  {f.name:45} {size_mb:8.2f} MB')
    
    print('-' * 80)
    print(f'  TOTAL PARQUET: {total_parquet/1024/1024:.2f} MB ({total_parquet/1024/1024/1024:.2f} GB)')
    
    # Estimación SQL
    print(f'\n📊 Estimación espacio SQL:')
    print('-' * 80)
    
    # Factor de expansión Parquet -> SQL
    sql_factor = 1.3  # SQL ocupa ~30% más que Parquet (sin compresión)
    sql_size_mb = (total_parquet / 1024 / 1024) * sql_factor
    print(f'  Datos (tablas):           {sql_size_mb:8.2f} MB  (factor {sql_factor}x vs Parquet)')
    
    # Índices
    indices_size = sql_size_mb * 0.20  # ~20% del tamaño de datos
    print(f'  Índices:                  {indices_size:8.2f} MB  (~20% de datos)')
    
    # Logs y overhead
    logs_size = 100
    print(f'  Logs transaccionales:     {logs_size:8.2f} MB  (estimado)')
    
    overhead = sql_size_mb * 0.1  # 10% overhead sistema
    print(f'  Overhead PostgreSQL:      {overhead:8.2f} MB  (~10% sistema)')
    
    total_sql = sql_size_mb + indices_size + logs_size + overhead
    print('-' * 80)
    print(f'  TOTAL SQL:                {total_sql:8.2f} MB  ({total_sql/1024:.2f} GB)')

else:
    print('\n⚠️  Carpeta data/clean no contiene datos procesados.')
    print('   Estimando basado en dataset original...\n')
    
    orig_path = Path('data/processed/datos.parquet')
    if orig_path.exists():
        orig_size_bytes = orig_path.stat().st_size
        orig_size_mb = orig_size_bytes / 1024 / 1024
        
        print(f'📁 Archivo original:')
        print(f'  datos.parquet:            {orig_size_mb:8.2f} MB  ({orig_size_mb/1024:.2f} GB)')
        
        # Estimación basada en que procesaremos todo el dataset
        print(f'\n📊 Estimación espacio SQL (dataset completo):')
        print('-' * 80)
        
        # Dataset completo en SQL
        sql_factor = 1.3
        sql_size_mb = orig_size_mb * sql_factor
        print(f'  Datos (tablas):           {sql_size_mb:8.2f} MB  (factor {sql_factor}x)')
        
        # Índices
        indices_size = sql_size_mb * 0.20
        print(f'  Índices:                  {indices_size:8.2f} MB  (~20%)')
        
        # Stats tables (agregados por depto/mun)
        stats_size = 10  # Pequeño, solo agregados
        print(f'  Tablas estadísticas:      {stats_size:8.2f} MB  (agregados)')
        
        # Logs
        logs_size = 150
        print(f'  Logs transaccionales:     {logs_size:8.2f} MB')
        
        # Overhead
        overhead = sql_size_mb * 0.1
        print(f'  Overhead PostgreSQL:      {overhead:8.2f} MB  (~10%)')
        
        total_sql = sql_size_mb + indices_size + stats_size + logs_size + overhead
        print('-' * 80)
        print(f'  TOTAL SQL:                {total_sql:8.2f} MB  ({total_sql/1024:.2f} GB)')
    else:
        print('ERROR: No se encuentra datos.parquet')
        exit(1)

# Recomendaciones
print(f'\n💾 Recomendaciones espacio disco:')
print('=' * 80)

print(f'  Mínimo funcional:         {total_sql/1024:.1f} GB  (justo para datos)')
print(f'  Recomendado producción:   {total_sql*2/1024:.1f} GB  (2x para crecimiento + vacuuming)')
print(f'  Ideal con backups:        {total_sql*3/1024:.1f} GB  (3x incluye backups + temp)')

print(f'\n📝 Desglose recomendado (producción):')
print('-' * 80)
print(f'  Base de datos:            {total_sql/1024:.1f} GB')
print(f'  Crecimiento (1 año):      {total_sql*0.5/1024:.1f} GB  (50% más datos)')
print(f'  WAL + temp files:         {total_sql*0.3/1024:.1f} GB  (30% para operaciones)')
print(f'  Backups automáticos:      {total_sql*1.0/1024:.1f} GB  (1x para pg_dump)')
print('-' * 80)
print(f'  TOTAL RECOMENDADO:        {total_sql*2.8/1024:.1f} GB')

print(f'\n⚡ Configuración PostgreSQL recomendada:')
print('=' * 80)
print(f'  shared_buffers:           {max(128, int(total_sql/1024 * 0.25 * 1024))} MB  (25% de datos)')
print(f'  effective_cache_size:     {max(512, int(total_sql/1024 * 0.75 * 1024))} MB  (75% de datos)')
print(f'  work_mem:                 16 MB')
print(f'  maintenance_work_mem:     {max(64, int(total_sql/1024 * 0.1 * 1024))} MB')

print(f'\n💡 Alternativas si espacio es limitado:')
print('=' * 80)
print('  1. Usar solo dataset ml_training (5.7M registros) en vez de completo (30.9M)')
print('     Ahorro: ~70% de espacio')
print('  2. Particionamiento por año (solo últimos 3-5 años en "hot" storage)')
print('     Ahorro: ~50% de espacio activo')
print('  3. Comprimir columnas de texto (TOAST en PostgreSQL)')
print('     Ahorro: ~15-20% adicional')
print('  4. Usar tablespaces separados (SSD para datos, HDD para backups)')
print('     Costo: Medio, rendimiento óptimo')

print('\n✅ Resumen ejecutivo:')
print('=' * 80)
print(f'  Para PostgreSQL/SQL Server con dataset completo:')
print(f'    - Espacio mínimo: {total_sql/1024:.1f} GB')
print(f'    - Espacio recomendado: {total_sql*2/1024:.1f} GB')
print(f'    - Con backups: {total_sql*3/1024:.1f} GB')
print(f'\n  Si usas SQLite (desarrollo):')
print(f'    - Espacio: {total_sql*0.8/1024:.1f} GB (más eficiente)')
print('=' * 80)
