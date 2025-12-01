"""
Entrenamiento con datos reales de SNR Colombia
Mapea las columnas oficiales y entrena el modelo de predicción de precios
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from price_prediction import PricePredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapeo de columnas SNR a nuestro modelo
COLUMN_MAPPING = {
    # Identificadores
    'PK': 'pk',
    'MATRICULA': 'matricula',
    
    # Fechas
    'FECHA_RADICA_TEXTO': 'fecha_radicacion',
    'FECHA_APERTURA_TEXTO': 'fecha_apertura',
    'YEAR_RADICA': 'year_radica',
    
    # Ubicación
    'ORIP': 'orip',
    'DIVIPOLA': 'divipola',
    'DEPARTAMENTO': 'departamento',
    'MUNICIPIO': 'municipio',
    'TIPO_PREDIO_ZONA': 'tipo_predio',
    'CATEGORIA_RURALIDAD': 'categoria_ruralidad',
    
    # Registro
    'NUM_ANOTACION': 'num_anotacion',
    'ESTADO_FOLIO': 'estado_folio',
    'FOLIOS_DERIVADOS': 'folios_derivados',
    
    # Tipo de acto
    'COD_NATUJUR': 'cod_natujur',
    'NOMBRE_NATUJUR': 'nombre_natujur',
    
    # Catastro
    'NUMERO_CATASTRAL': 'numero_catastral',
    'NUMERO_CATASTRAL_ANTIGUO': 'numero_catastral_antiguo',
    
    # Documento
    'DOCUMENTO_JUSTIFICATIVO': 'documento_justificativo',
    
    # Intervinientes
    'COUNT_A': 'count_a',  # Receptores
    'COUNT_DE': 'count_de',  # Otorgantes
    
    # Indicadores
    'PREDIOS_NUEVOS': 'predios_nuevos',
    'TIENE_VALOR': 'tiene_valor',
    'TIENE_MAS_DE_UN_VALOR': 'tiene_mas_de_un_valor',
    'Dinámica_Inmobiliaria': 'dinamica_inmobiliaria',
    
    # Valor
    'VALOR': 'valor_acto',
}

# Features importantes para el modelo
MODEL_FEATURES = [
    'departamento',
    'municipio',
    'tipo_predio',
    'nombre_natujur',  # Tipo de acto jurídico
    'estado_folio',
    'count_a',  # Número de receptores
    'count_de',  # Número de otorgantes
    'predios_nuevos',  # Si es predio nuevo
    'categoria_ruralidad',
    'dinamica_inmobiliaria',
]

def load_and_prepare_snr_data(file_path, sample_size=None):
    """
    Carga y prepara datos reales de SNR
    
    Args:
        file_path: Ruta al archivo CSV/Parquet de SNR
        sample_size: Número de registros a usar (None = todos)
    
    Returns:
        DataFrame preparado
    """
    logger.info(f"Cargando datos desde: {file_path}")
    
    file_path = Path(file_path)
    
    # Leer según el formato
    if file_path.suffix == '.parquet':
        df = pd.read_parquet(file_path)
    elif file_path.suffix == '.csv':
        df = pd.read_csv(file_path, low_memory=False)
    else:
        raise ValueError(f"Formato no soportado: {file_path.suffix}")
    
    logger.info(f"Datos cargados: {len(df):,} registros, {len(df.columns)} columnas")
    
    # Renombrar columnas según mapeo
    df_renamed = df.rename(columns=COLUMN_MAPPING)
    
    # Filtrar solo transacciones con valor
    df_with_value = df_renamed[
        (df_renamed['tiene_valor'] == 1) & 
        (df_renamed['valor_acto'].notna()) &
        (df_renamed['valor_acto'] > 0)
    ].copy()
    
    logger.info(f"Registros con valor: {len(df_with_value):,} ({len(df_with_value)/len(df)*100:.1f}%)")
    
    # Filtrar por dinámica inmobiliaria (solo actos relevantes para mercado)
    if 'dinamica_inmobiliaria' in df_with_value.columns:
        df_market = df_with_value[df_with_value['dinamica_inmobiliaria'] == 1].copy()
        logger.info(f"Actos de mercado inmobiliario: {len(df_market):,} ({len(df_market)/len(df_with_value)*100:.1f}%)")
    else:
        df_market = df_with_value
    
    # Normalizar texto (mayúsculas, sin espacios extras)
    text_columns = ['departamento', 'municipio', 'tipo_predio', 'nombre_natujur', 'estado_folio']
    for col in text_columns:
        if col in df_market.columns:
            df_market[col] = df_market[col].str.upper().str.strip()
    
    # Convertir fechas
    if 'fecha_radicacion' in df_market.columns:
        df_market['fecha_radicacion'] = pd.to_datetime(
            df_market['fecha_radicacion'], 
            errors='coerce'
        )
        df_market['year'] = df_market['fecha_radicacion'].dt.year
        df_market['month'] = df_market['fecha_radicacion'].dt.month
        df_market['quarter'] = df_market['fecha_radicacion'].dt.quarter
    
    # Muestreo si se especifica
    if sample_size and len(df_market) > sample_size:
        df_market = df_market.sample(n=sample_size, random_state=42)
        logger.info(f"Muestra aleatoria de {sample_size:,} registros")
    
    # Verificar features necesarios
    available_features = [f for f in MODEL_FEATURES if f in df_market.columns]
    missing_features = [f for f in MODEL_FEATURES if f not in df_market.columns]
    
    logger.info(f"Features disponibles: {len(available_features)}/{len(MODEL_FEATURES)}")
    if missing_features:
        logger.warning(f"Features faltantes: {missing_features}")
    
    return df_market

def train_model_with_snr_data(data_path, output_dir='ml/models', sample_size=None):
    """
    Entrena el modelo con datos reales de SNR
    
    Args:
        data_path: Ruta al archivo de datos SNR
        output_dir: Directorio para guardar modelos
        sample_size: Número de registros a usar (None = todos)
    """
    logger.info("=" * 60)
    logger.info("ENTRENAMIENTO CON DATOS REALES SNR")
    logger.info("=" * 60)
    
    # Cargar datos
    df = load_and_prepare_snr_data(data_path, sample_size)
    
    # Estadísticas previas
    logger.info("\n📊 Estadísticas de los datos:")
    logger.info(f"Total registros: {len(df):,}")
    logger.info(f"Valor promedio: ${df['valor_acto'].mean():,.0f}")
    logger.info(f"Valor mediano: ${df['valor_acto'].median():,.0f}")
    logger.info(f"Valor mínimo: ${df['valor_acto'].min():,.0f}")
    logger.info(f"Valor máximo: ${df['valor_acto'].max():,.0f}")
    
    logger.info("\n📍 Distribución por departamento:")
    dept_counts = df['departamento'].value_counts().head(10)
    for dept, count in dept_counts.items():
        logger.info(f"  {dept}: {count:,} ({count/len(df)*100:.1f}%)")
    
    logger.info("\n🏢 Distribución por tipo de predio:")
    tipo_counts = df['tipo_predio'].value_counts()
    for tipo, count in tipo_counts.items():
        logger.info(f"  {tipo}: {count:,} ({count/len(df)*100:.1f}%)")
    
    logger.info("\n📝 Actos jurídicos más frecuentes:")
    acto_counts = df['nombre_natujur'].value_counts().head(10)
    for acto, count in acto_counts.items():
        logger.info(f"  {acto}: {count:,} ({count/len(df)*100:.1f}%)")
    
    # Entrenar modelo
    logger.info("\n🤖 Entrenando modelo de predicción...")
    predictor = PricePredictor()
    results = predictor.train(df)
    
    # Guardar modelo
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    predictor.save(output_path)
    logger.info(f"\n✅ Modelo guardado en: {output_path}")
    
    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN DEL ENTRENAMIENTO")
    logger.info("=" * 60)
    logger.info(f"Registros entrenamiento: {results['n_train']:,}")
    logger.info(f"Registros prueba: {results['n_test']:,}")
    logger.info(f"MAE (Test): ${results['mae']:,.0f}")
    logger.info(f"R² (Test): {results['r2']:.3f}")
    logger.info(f"RMSE (Test): ${results['rmse']:,.0f}")
    logger.info("\n🎯 Top 10 features importantes:")
    for feature, importance in results['feature_importance'][:10]:
        logger.info(f"  {feature}: {importance:.4f}")
    
    return predictor, results

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Entrenar modelo con datos reales SNR')
    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Ruta al archivo de datos SNR (CSV o Parquet)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ml/models',
        help='Directorio para guardar modelos (default: ml/models)'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help='Número de registros a usar (default: todos)'
    )
    
    args = parser.parse_args()
    
    try:
        predictor, results = train_model_with_snr_data(
            args.data,
            args.output,
            args.sample
        )
        logger.info("\n✅ Entrenamiento completado exitosamente")
    except Exception as e:
        logger.error(f"\n❌ Error durante entrenamiento: {e}", exc_info=True)
        exit(1)
