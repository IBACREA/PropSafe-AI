"""
ETL Pipeline - Limpieza y Transformación de Datos Inmobiliarios
Paso 1: Validación de tipos, limpieza de valores, clasificación
"""
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from pathlib import Path
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InmobiliarioETL:
    """Pipeline ETL para datos de transacciones inmobiliarias"""
    
    def __init__(self, input_path: str, output_dir: str):
        self.input_path = input_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Contadores para reporte
        self.stats = {
            'registros_entrada': 0,
            'registros_salida': 0,
            'registros_descartados': 0,
            'registros_con_errores': 0,
            'registros_sospechosos': 0
        }
        
    def load_data(self, sample_size: int = None) -> pd.DataFrame:
        """Cargar datos del parquet (con opción de muestreo para pruebas)"""
        logger.info(f"Cargando datos desde {self.input_path}")
        
        if sample_size:
            logger.info(f"Modo muestra: cargando {sample_size:,} registros")
            # Cargar muestra usando ParquetFile
            parquet_file = pq.ParquetFile(self.input_path)
            chunks = []
            rows_read = 0
            
            for batch in parquet_file.iter_batches(batch_size=100000):
                df_batch = batch.to_pandas()
                chunks.append(df_batch)
                rows_read += len(df_batch)
                
                if rows_read >= sample_size:
                    break
            
            df = pd.concat(chunks, ignore_index=True).head(sample_size)
        else:
            # Cargar todo usando ParquetFile por batches
            logger.info("Cargando en modo chunks (optimizado memoria)...")
            parquet_file = pq.ParquetFile(self.input_path)
            chunks = []
            batch_num = 0
            
            for batch in parquet_file.iter_batches(batch_size=500000):
                batch_num += 1
                df_batch = batch.to_pandas()
                chunks.append(df_batch)
                logger.info(f"  Batch {batch_num} cargado: {len(df_batch):,} registros")
            
            df = pd.concat(chunks, ignore_index=True)
        
        self.stats['registros_entrada'] = len(df)
        logger.info(f"Total datos cargados: {len(df):,} registros")
        return df
    
    def crear_composite_key(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crear identificador único de transacción (composite key)"""
        logger.info("Creando composite transaction key...")
        
        # Composite Key: DIVIPOLA + NUM_MATRICULA + NUM_ANOTACION + COD_NATUJUR + AÑO
        df['transaction_id'] = (
            df['DIVIPOLA'].astype(str).fillna('UNK') + '_' +
            df['MATRICULA'].astype(str).fillna('UNK') + '_' +
            df['NUM_ANOTACION'].astype(str).fillna('0') + '_' +
            df['COD_NATUJUR'].astype(str).fillna('UNK') + '_' +
            df['YEAR_RADICA'].astype(str).fillna('0')
        )
        
        logger.info(f"  - Composite keys creadas: {df['transaction_id'].nunique():,} únicas")
        return df
    
    def validar_y_tipar(self, df: pd.DataFrame) -> pd.DataFrame:
        """Paso 1: Validar tipos de datos y convertir correctamente"""
        logger.info("Validando y tipando columnas...")
        
        # 1. YEAR_RADICA - debe ser entero
        logger.info("  - Convirtiendo YEAR_RADICA a int")
        df['YEAR_RADICA'] = pd.to_numeric(df['YEAR_RADICA'], errors='coerce').astype('Int64')
        
        # 2. Dinámica_Inmobiliaria - convertir a int (0 o 1)
        logger.info("  - Convirtiendo Dinámica_Inmobiliaria a int")
        df['Dinámica_Inmobiliaria'] = df['Dinámica_Inmobiliaria'].map({'1': 1, '0': 0, 1: 1, 0: 0})
        
        # 3. VALOR - limpiar y convertir a float
        logger.info("  - Limpiando y convirtiendo VALOR a float")
        df['VALOR'] = pd.to_numeric(
            df['VALOR'].astype(str).str.replace(',', ''), 
            errors='coerce'
        )
        
        # 4. COUNT_A, COUNT_DE - convertir a int
        logger.info("  - Convirtiendo COUNT_A y COUNT_DE a int")
        df['COUNT_A'] = pd.to_numeric(df['COUNT_A'], errors='coerce').astype('Int64')
        df['COUNT_DE'] = pd.to_numeric(df['COUNT_DE'], errors='coerce').astype('Int64')
        
        # 5. PREDIOS_NUEVOS - convertir a int (0 o 1)
        logger.info("  - Convirtiendo PREDIOS_NUEVOS a int")
        df['PREDIOS_NUEVOS'] = df['PREDIOS_NUEVOS'].map({'1': 1, '0': 0, 1: 1, 0: 0})
        
        # 6. TIENE_VALOR, TIENE_MAS_DE_UN_VALOR - convertir a int (0 o 1)
        logger.info("  - Convirtiendo flags booleanos")
        df['TIENE_VALOR'] = df['TIENE_VALOR'].map({'1': 1, '0': 0, 1: 1, 0: 0})
        df['TIENE_MAS_DE_UN_VALOR'] = df['TIENE_MAS_DE_UN_VALOR'].map({'1': 1, '0': 0, 1: 1, 0: 0})
        
        # 7. Categorías - limpiar strings (mayúsculas, trim)
        logger.info("  - Limpiando campos categóricos")
        cat_cols = ['DEPARTAMENTO', 'MUNICIPIO', 'TIPO_PREDIO_ZONA', 
                    'CATEGORIA_RURALIDAD', 'ESTADO_FOLIO']
        for col in cat_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
                df[col] = df[col].replace('NONE', np.nan)
        
        # 8. ORIP - ya es float, validar rango
        logger.info("  - Validando ORIP")
        df.loc[(df['ORIP'] < 1) | (df['ORIP'] > 999), 'ORIP'] = np.nan
        
        return df
    
    def clasificar_calidad(self, df: pd.DataFrame) -> pd.DataFrame:
        """Paso 2: Clasificar registros por calidad de datos (CONTEXTUAL según cod_naturaleza)"""
        logger.info("Clasificando calidad de registros (reglas de negocio)...")
        
        # Inicializar columnas de clasificación
        df['calidad_datos'] = 'OK'  # OK, ADVERTENCIA, ERROR
        df['tipo_error'] = None
        df['es_mercado_valido'] = False
        df['valor_valido'] = False
        
        # REGLA 1: Dinámica_Inmobiliaria debe ser válido
        mask_din_invalido = df['Dinámica_Inmobiliaria'].isna()
        df.loc[mask_din_invalido, 'calidad_datos'] = 'ERROR'
        df.loc[mask_din_invalido, 'tipo_error'] = 'DINAMICA_INVALIDA'
        
        # REGLA 2: YEAR_RADICA en rango válido (2000-2025)
        mask_year_invalido = (df['YEAR_RADICA'] < 2000) | (df['YEAR_RADICA'] > 2025)
        df.loc[mask_year_invalido, 'calidad_datos'] = 'ERROR'
        df.loc[mask_year_invalido, 'tipo_error'] = 'YEAR_INVALIDO'
        
        # REGLA 3: DEPARTAMENTO y MUNICIPIO requeridos
        mask_geo_invalido = df['DEPARTAMENTO'].isna() | df['MUNICIPIO'].isna()
        df.loc[mask_geo_invalido, 'calidad_datos'] = 'ERROR'
        df.loc[mask_geo_invalido, 'tipo_error'] = 'GEOGRAFIA_INVALIDA'
        
        # REGLA 4: Marcar registros de mercado válidos (Dinámica=1)
        df['es_mercado_valido'] = (df['Dinámica_Inmobiliaria'] == 1)
        
        # REGLA 5: CLASIFICACIÓN CONTEXTUAL DE VALOR (según tipo de acto)
        # Actos que REQUIEREN valor (compraventas, hipotecas, etc.)
        actos_con_valor = df['NOMBRE_NATUJUR'].str.contains(
            'COMPRAVENTA|HIPOTECA|VENTA|MUTUO', 
            case=False, 
            na=False
        )
        
        # ERROR: Actos de mercado (Dinámica=1) SIN valor -> Anomalía de Calidad
        mask_mercado_sin_valor = (
            (df['es_mercado_valido'] == True) & 
            (df['VALOR'].isna() | (df['VALOR'] == 0))
        )
        df.loc[mask_mercado_sin_valor, 'calidad_datos'] = 'ERROR'
        df.loc[mask_mercado_sin_valor, 'tipo_error'] = 'MERCADO_SIN_VALOR'
        
        # OK: Actos administrativos (Dinámica=0) con valor=0 -> CORRECTO
        mask_admin_cero = (
            (df['Dinámica_Inmobiliaria'] == 0) & 
            (df['VALOR'] == 0)
        )
        # No marcar como error (es correcto)
        
        # ADVERTENCIA: Compraventas con valores irrisorios (< 1M COP)
        mask_compraventa_irrisiorio = (
            actos_con_valor & 
            (df['VALOR'] > 0) & 
            (df['VALOR'] < 1_000_000) &
            (df['calidad_datos'] == 'OK')
        )
        df.loc[mask_compraventa_irrisiorio, 'calidad_datos'] = 'ADVERTENCIA'
        df.loc[mask_compraventa_irrisiorio, 'tipo_error'] = 'VALOR_IRRISIORIO'
        
        # ERROR: VALOR extremo (> 10B COP) - probable error de digitación
        mask_valor_extremo = (df['VALOR'] > 10_000_000_000)
        df.loc[mask_valor_extremo, 'calidad_datos'] = 'ERROR'
        df.loc[mask_valor_extremo, 'tipo_error'] = 'VALOR_EXTREMO_DIGITACION'
        
        # VALOR válido para ML: 1M - 10B COP (solo para mercado)
        mask_valor_valido = (
            (df['VALOR'] >= 1_000_000) & 
            (df['VALOR'] <= 10_000_000_000) &
            (df['es_mercado_valido'] == True)
        )
        df['valor_valido'] = mask_valor_valido
        
        # REGLA 6: TIPO_PREDIO_ZONA - PRESERVAR "SIN INFORMACION" (Indeterminado)
        # Es una categoría VÁLIDA (fallo de georreferenciación)
        valores_validos_tipo = ['URBANO', 'RURAL', 'SIN INFORMACION', 'MIXTO']
        mask_tipo_invalido = ~df['TIPO_PREDIO_ZONA'].isin(valores_validos_tipo)
        df.loc[mask_tipo_invalido & (df['calidad_datos'] == 'OK'), 'calidad_datos'] = 'ADVERTENCIA'
        df.loc[mask_tipo_invalido & (df['tipo_error'].isna()), 'tipo_error'] = 'TIPO_PREDIO_INVALIDO'
        
        # Contar estadísticas
        self.stats['registros_con_errores'] = (df['calidad_datos'] == 'ERROR').sum()
        self.stats['registros_sospechosos'] = (df['calidad_datos'] == 'ADVERTENCIA').sum()
        
        logger.info(f"  - Registros OK: {(df['calidad_datos'] == 'OK').sum():,}")
        logger.info(f"  - Registros con ADVERTENCIA: {self.stats['registros_sospechosos']:,}")
        logger.info(f"  - Registros con ERROR: {self.stats['registros_con_errores']:,}")
        
        return df
    
    def detectar_anomalias_negocio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Paso 2b: Detectar anomalías de patrones de negocio"""
        logger.info("Detectando anomalías de negocio...")
        
        # Inicializar flags de anomalías
        df['flag_actividad_excesiva'] = False
        df['flag_geo_discrepancia'] = False
        df['anotaciones_por_anio'] = 0
        
        # ANOMALÍA 1: Número excesivo de anotaciones por matrícula en un año (>150)
        logger.info("  - Detectando actividad excesiva...")
        anotaciones_count = df.groupby(['MATRICULA', 'YEAR_RADICA']).size()
        
        # Crear mapping de tuplas sin copiar el DataFrame
        anotaciones_dict = anotaciones_count.to_dict()
        
        # Vectorizar usando zip (más rápido que apply)
        logger.info("    - Aplicando conteo de anotaciones...")
        keys = list(zip(df['MATRICULA'], df['YEAR_RADICA']))
        df['anotaciones_por_anio'] = [anotaciones_dict.get(k, 0) for k in keys]
        df['flag_actividad_excesiva'] = df['anotaciones_por_anio'] > 150
        
        actividad_excesiva = df['flag_actividad_excesiva'].sum()
        logger.info(f"    * {actividad_excesiva:,} transacciones con actividad excesiva (>150 anotaciones/año)")
        
        # ANOMALÍA 2: Discrepancia geográfica ORIP vs DIVIPOLA
        # Crear mapeo ORIP -> Departamento más común (el esperado para esa ORIP)
        logger.info("  - Detectando discrepancias geográficas...")
        
        # Mapeo ORIP -> Departamento esperado (el más frecuente para cada ORIP)
        orip_dept_esperado = df.groupby('ORIP')['DEPARTAMENTO'].agg(
            lambda x: x.value_counts().index[0] if len(x) > 0 else None
        ).to_dict()
        
        df['depto_esperado_orip'] = df['ORIP'].map(orip_dept_esperado)
        
        # Flag si el departamento real (DIVIPOLA) NO coincide con el esperado (ORIP)
        # NOTA: Esto es POSIBLE (jurisdicción cruzada), pero si es diferente puede ser error
        df['flag_geo_discrepancia'] = (
            (df['DEPARTAMENTO'] != df['depto_esperado_orip']) &
            df['DEPARTAMENTO'].notna() &
            df['depto_esperado_orip'].notna()
        )
        
        geo_discrepancia = df['flag_geo_discrepancia'].sum()
        geo_total = len(df)
        logger.info(f"    * {geo_discrepancia:,} transacciones con discrepancia geográfica ({geo_discrepancia/geo_total*100:.1f}%)")
        
        # ANOMALÍA 3: Marcar registros con múltiples flags
        df['total_flags_anomalia'] = (
            df['flag_actividad_excesiva'].astype(int) +
            df['flag_geo_discrepancia'].astype(int)
        )
        
        return df
    
    def crear_datasets(self, df: pd.DataFrame) -> dict:
        """Paso 3: Guardar datasets directamente sin copias intermedias (optimizado para memoria)"""
        logger.info("Creando datasets especializados...")
        
        output_dir = self.output_dir
        counts = {}
        
        # 1. Dataset COMPLETO (todos los registros con tipado correcto)
        logger.info("  - Guardando dataset COMPLETO...")
        df.to_parquet(output_dir / 'completo.parquet', compression='snappy', index=False)
        counts['completo'] = len(df)
        logger.info(f"    ✓ {counts['completo']:,} registros guardados")
        
        # 2. Dataset LIMPIO (solo calidad OK)
        logger.info("  - Guardando dataset LIMPIO...")
        mask_limpio = df['calidad_datos'] == 'OK'
        df[mask_limpio].to_parquet(output_dir / 'limpio.parquet', compression='snappy', index=False)
        counts['limpio'] = mask_limpio.sum()
        logger.info(f"    ✓ {counts['limpio']:,} registros guardados")
        
        # 3. Dataset MERCADO (Dinámica=1, sin errores)
        logger.info("  - Guardando dataset MERCADO...")
        mask_mercado = (df['es_mercado_valido'] == True) & (df['calidad_datos'] != 'ERROR')
        df[mask_mercado].to_parquet(output_dir / 'mercado.parquet', compression='snappy', index=False)
        counts['mercado'] = mask_mercado.sum()
        logger.info(f"    ✓ {counts['mercado']:,} registros guardados")
        
        # 4. Dataset ML_TRAINING (mercado + valor válido)
        logger.info("  - Guardando dataset ML_TRAINING...")
        mask_ml = (df['es_mercado_valido'] == True) & (df['valor_valido'] == True) & (df['calidad_datos'] == 'OK')
        df[mask_ml].to_parquet(output_dir / 'ml_training.parquet', compression='snappy', index=False)
        counts['ml_training'] = mask_ml.sum()
        logger.info(f"    ✓ {counts['ml_training']:,} registros guardados")
        
        # 5. Dataset ERRORES (para revisión manual)
        logger.info("  - Guardando dataset ERRORES...")
        mask_error = df['calidad_datos'] == 'ERROR'
        df[mask_error].to_parquet(output_dir / 'errores.parquet', compression='snappy', index=False)
        counts['errores'] = mask_error.sum()
        logger.info(f"    ✓ {counts['errores']:,} registros guardados")
        
        # 6. Dataset ADVERTENCIAS (para revisión manual)
        logger.info("  - Guardando dataset ADVERTENCIAS...")
        mask_adv = df['calidad_datos'] == 'ADVERTENCIA'
        df[mask_adv].to_parquet(output_dir / 'advertencias.parquet', compression='snappy', index=False)
        counts['advertencias'] = mask_adv.sum()
        logger.info(f"    ✓ {counts['advertencias']:,} registros guardados")
        
        self.stats['registros_salida'] = counts['ml_training']
        self.stats['registros_descartados'] = self.stats['registros_entrada'] - counts['ml_training']
        
        return counts
    
    def generar_estadisticas(self, counts: dict) -> pd.DataFrame:
        """Paso 4: Generar estadísticas agregadas para dashboard"""
        logger.info("Generando estadísticas agregadas...")
        
        # Cargar solo el dataset ML para estadísticas (más eficiente)
        df_ml = pd.read_parquet(self.output_dir / 'ml_training.parquet')
        
        # Estadísticas por DEPARTAMENTO + AÑO
        stats_dept_year = df_ml.groupby(['DEPARTAMENTO', 'YEAR_RADICA']).agg({
            'VALOR': ['count', 'mean', 'median', 'std', 'min', 'max'],
            'PK': 'count'
        }).reset_index()
        stats_dept_year.columns = [
            'departamento', 'year', 
            'transacciones', 'valor_medio', 'valor_mediano', 'valor_std', 'valor_min', 'valor_max',
            'total_registros'
        ]
        
        # Estadísticas por MUNICIPIO + AÑO (top 50 municipios)
        top_municipios = df_ml['MUNICIPIO'].value_counts().head(50).index
        df_top_mun = df_ml[df_ml['MUNICIPIO'].isin(top_municipios)]
        
        stats_mun_year = df_top_mun.groupby(['MUNICIPIO', 'DEPARTAMENTO', 'YEAR_RADICA']).agg({
            'VALOR': ['count', 'mean', 'median', 'std'],
            'PK': 'count'
        }).reset_index()
        stats_mun_year.columns = [
            'municipio', 'departamento', 'year',
            'transacciones', 'valor_medio', 'valor_mediano', 'valor_std',
            'total_registros'
        ]
        
        # Estadísticas por TIPO_PREDIO
        stats_tipo = df_ml.groupby(['TIPO_PREDIO_ZONA', 'YEAR_RADICA']).agg({
            'VALOR': ['count', 'mean', 'median'],
            'PK': 'count'
        }).reset_index()
        stats_tipo.columns = [
            'tipo_predio', 'year',
            'transacciones', 'valor_medio', 'valor_mediano',
            'total_registros'
        ]
        
        return {
            'por_departamento_año': stats_dept_year,
            'por_municipio_año': stats_mun_year,
            'por_tipo_predio': stats_tipo
        }
    
    def guardar_estadisticas(self, stats: dict):
        """Paso 5: Guardar estadísticas agregadas"""
        logger.info("Guardando estadísticas...")
        
        # Guardar estadísticas
        for nombre, df_stats in stats.items():
            output_path = self.output_dir / f"stats_{nombre}.parquet"
            df_stats.to_parquet(output_path, index=False, compression='snappy')
            logger.info(f"  - Guardado: {output_path}")
        
        # Guardar reporte de ETL
        reporte = pd.DataFrame([self.stats])
        reporte['fecha_proceso'] = datetime.now()
        reporte_path = self.output_dir / "etl_report.csv"
        reporte.to_csv(reporte_path, index=False)
        logger.info(f"  - Reporte guardado: {reporte_path}")
    
    def run(self, sample_size: int = None):
        """Ejecutar pipeline completo"""
        logger.info("=" * 80)
        logger.info("INICIANDO PIPELINE ETL - Análisis de Transacciones")
        logger.info("=" * 80)
        
        # Paso 1: Cargar
        df = self.load_data(sample_size)
        
        # Paso 2: Crear composite key (transaction_id)
        df = self.crear_composite_key(df)
        
        # Paso 3: Validar y tipar
        df = self.validar_y_tipar(df)
        
        # Paso 4: Clasificar calidad (contextual según código naturaleza)
        df = self.clasificar_calidad(df)
        
        # Paso 5: Detectar anomalías de negocio
        df = self.detectar_anomalias_negocio(df)
        
        # Paso 6: Crear y guardar datasets (sin copias en memoria)
        counts = self.crear_datasets(df)
        
        # Liberar memoria del DataFrame principal
        del df
        import gc
        gc.collect()
        logger.info("Memoria liberada después de guardar datasets")
        
        # Paso 7: Generar estadísticas
        stats = self.generar_estadisticas(counts)
        
        # Paso 8: Guardar estadísticas
        self.guardar_estadisticas(stats)
        
        logger.info("=" * 80)
        logger.info("REPORTE FINAL ETL")
        logger.info("=" * 80)
        logger.info(f"Registros entrada: {self.stats['registros_entrada']:,}")
        logger.info(f"Registros para ML: {self.stats['registros_salida']:,}")
        logger.info(f"Registros descartados: {self.stats['registros_descartados']:,}")
        logger.info(f"Registros con errores: {self.stats['registros_con_errores']:,}")
        logger.info(f"Registros sospechosos: {self.stats['registros_sospechosos']:,}")
        logger.info(f"Tasa aprovechamiento: {self.stats['registros_salida']/self.stats['registros_entrada']*100:.1f}%")
        logger.info("=" * 80)
        logger.info("Datasets generados:")
        for nombre, count in counts.items():
            logger.info(f"  - {nombre}.parquet: {count:,} registros")
        logger.info("=" * 80)
        
        return counts, stats


if __name__ == "__main__":
    import sys
    
    # Configuración
    INPUT_PATH = "data/processed/datos.parquet"
    OUTPUT_DIR = "data/clean"
    
    # Permitir sample_size como argumento
    sample_size = None
    if len(sys.argv) > 1:
        sample_size = int(sys.argv[1])
        logger.info(f"Modo prueba: procesando {sample_size:,} registros")
    
    # Ejecutar ETL
    etl = InmobiliarioETL(INPUT_PATH, OUTPUT_DIR)
    counts, stats = etl.run(sample_size)
    
    print("\n✅ ETL completado exitosamente!")
    print(f"   Datasets guardados en: {OUTPUT_DIR}")
    print(f"\nDatasets generados en: {OUTPUT_DIR}/")
    print("  - completo.parquet (todos los registros tipados)")
    print("  - limpio.parquet (solo calidad OK)")
    print("  - mercado.parquet (Dinámica=1, sin errores)")
    print("  - ml_training.parquet (listo para ML)")
    print("  - errores.parquet (revisión manual)")
    print("  - advertencias.parquet (revisión manual)")
    print("\nEstadísticas generadas:")
    print("  - stats_por_departamento_año.parquet")
    print("  - stats_por_municipio_año.parquet")
    print("  - stats_por_tipo_predio.parquet")

