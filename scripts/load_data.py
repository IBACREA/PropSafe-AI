"""
Load processed data into PostgreSQL database
Optimized for t3.small instance (2GB RAM)
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'propsafe_db'),
    'user': os.getenv('DB_USER', 'propsafe_user'),
    'password': os.getenv('DB_PASSWORD', 'change_in_production')
}

# Data file path
DATA_FILE = os.getenv('DATA_FILE', '/app/data/completo.parquet')
CHUNK_SIZE = 50000  # Process 50k rows at a time


def get_db_connection():
    """Create database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)


def prepare_row(row):
    """Prepare a row for insertion, handling NaN values."""
    return tuple(
        None if pd.isna(val) else val
        for val in row
    )


def load_data_chunked(file_path: str):
    """Load data from parquet file in chunks and insert into database."""
    
    if not os.path.exists(file_path):
        logger.error(f"Data file not found: {file_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {file_path}")
    
    # Get total row count
    df_info = pd.read_parquet(file_path, columns=['transaction_id'])
    total_rows = len(df_info)
    logger.info(f"Total rows to load: {total_rows:,}")
    del df_info
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Define columns to load
    columns = [
        'transaction_id', 'divipola', 'departamento', 'municipio', 'codigo_orip',
        'numero_matricula', 'numero_predial', 'tipo_predio', 'area_terreno', 'area_construida',
        'numero_anotacion', 'codigo_naturaleza_juridica', 'descripcion_naturaleza_juridica',
        'dinamica_mercado', 'tipo_acto', 'fecha_acto', 'year_radica', 'valor_acto',
        'numero_intervinientes', 'tipo_zona', 'latitud', 'longitud',
        'calidad_datos', 'tiene_valor_nulo', 'tiene_area_cero',
        'flag_actividad_excesiva', 'anotaciones_por_anio', 'flag_discrepancia_geografica'
    ]
    
    # SQL insert statement
    insert_sql = f"""
        INSERT INTO transactions ({', '.join(columns)})
        VALUES %s
        ON CONFLICT (transaction_id) DO NOTHING
    """
    
    # Process in chunks
    loaded_rows = 0
    start_time = datetime.now()
    
    try:
        # Read parquet in chunks
        for chunk_num, df_chunk in enumerate(pd.read_parquet(file_path, chunksize=CHUNK_SIZE)):
            
            # Select only needed columns
            df_chunk = df_chunk[columns]
            
            # Prepare data for insertion
            values = [prepare_row(row) for row in df_chunk.values]
            
            # Insert chunk
            execute_values(cursor, insert_sql, values, page_size=1000)
            conn.commit()
            
            loaded_rows += len(df_chunk)
            progress = (loaded_rows / total_rows) * 100
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = loaded_rows / elapsed if elapsed > 0 else 0
            
            logger.info(
                f"Chunk {chunk_num + 1} loaded: {loaded_rows:,}/{total_rows:,} "
                f"({progress:.1f}%) - Rate: {rate:.0f} rows/sec"
            )
        
        # Create statistics after load
        logger.info("Generating statistics...")
        cursor.execute("""
            INSERT INTO statistics (metric_name, metric_value, metric_date)
            SELECT 
                'total_transactions',
                COUNT(*),
                CURRENT_DATE
            FROM transactions
            ON CONFLICT DO NOTHING
        """)
        
        cursor.execute("""
            INSERT INTO statistics (metric_name, metric_value, departamento, metric_date)
            SELECT 
                'transactions_by_dept',
                COUNT(*),
                departamento,
                CURRENT_DATE
            FROM transactions
            WHERE departamento IS NOT NULL
            GROUP BY departamento
            ON CONFLICT DO NOTHING
        """)
        
        cursor.execute("""
            INSERT INTO statistics (metric_name, metric_value, municipio, metric_date)
            SELECT 
                'avg_transaction_value',
                AVG(valor_acto),
                municipio,
                CURRENT_DATE
            FROM transactions
            WHERE valor_acto IS NOT NULL AND municipio IS NOT NULL
            GROUP BY municipio
            ON CONFLICT DO NOTHING
        """)
        
        conn.commit()
        logger.info("Statistics generated")
        
        # Vacuum and analyze
        logger.info("Running VACUUM ANALYZE...")
        old_isolation = conn.isolation_level
        conn.set_isolation_level(0)
        cursor.execute("VACUUM ANALYZE transactions")
        conn.set_isolation_level(old_isolation)
        logger.info("VACUUM ANALYZE completed")
        
        # Final stats
        elapsed_total = (datetime.now() - start_time).total_seconds()
        logger.info(f"""
        ==========================================
        Data Load Complete!
        ==========================================
        Total rows loaded: {loaded_rows:,}
        Total time: {elapsed_total:.1f} seconds
        Average rate: {loaded_rows/elapsed_total:.0f} rows/sec
        ==========================================
        """)
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load data into PostgreSQL')
    parser.add_argument('--file', default=DATA_FILE, help='Path to parquet file')
    args = parser.parse_args()
    
    load_data_chunked(args.file)
