#!/usr/bin/env python3
"""
ETL Pipeline for Real Estate Transactions

Procesa CSV de gran tamaño (8GB+) con:
- Lectura por chunks para eficiencia de memoria
- Validación de datos
- Transformación y limpieza
- Carga a PostgreSQL
- Generación de estadísticas

Usage:
    python etl_pipeline.py --input data/raw/transactions.csv --batch-size 10000
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.core.database import engine, SessionLocal, init_db
from backend.models.db_models import Transaction
from backend.core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


class ETLPipeline:
    """ETL Pipeline for processing large CSV files"""
    
    def __init__(self, batch_size: int = 10000):
        """
        Initialize ETL pipeline
        
        Args:
            batch_size: Number of rows to process per batch
        """
        self.batch_size = batch_size
        self.stats = {
            'total_rows_read': 0,
            'total_rows_loaded': 0,
            'total_rows_rejected': 0,
            'batches_processed': 0,
            'errors': []
        }
        
    def extract(self, file_path: str) -> pd.DataFrame:
        """
        Extract data from CSV in chunks
        
        Args:
            file_path: Path to CSV file
            
        Yields:
            DataFrame chunks
        """
        logger.info(f"📂 Extracting data from: {file_path}")
        
        try:
            # Expected SNR columns (Colombian real estate registry)
            expected_columns = [
                'pk', 'matricula', 'fecha_radicacion', 'fecha_apertura', 
                'year_radica', 'orip', 'divipola', 'departamento', 'municipio',
                'tipo_predio', 'nombre_natujur', 'valor_acto', 'tiene_valor',
                'count_a', 'count_de', 'estado_folio', 'numero_catastral',
                'matricula_inmobiliaria', 'area_terreno', 'area_construida'
            ]
            
            chunk_iterator = pd.read_csv(
                file_path,
                chunksize=self.batch_size,
                dtype={
                    'pk': 'Int64',
                    'matricula': str,
                    'departamento': str,
                    'municipio': str,
                    'tipo_predio': str,
                    'nombre_natujur': str,
                    'valor_acto': 'float64',
                    'tiene_valor': bool,
                    'count_a': 'Int64',
                    'count_de': 'Int64',
                    'orip': str,
                    'divipola': str,
                    'estado_folio': str,
                    'year_radica': 'Int64'
                },
                parse_dates=['fecha_radicacion', 'fecha_apertura'],
                low_memory=False
            )
            
            for chunk_num, chunk in enumerate(chunk_iterator, 1):
                self.stats['total_rows_read'] += len(chunk)
                logger.info(f"📦 Chunk {chunk_num}: {len(chunk)} rows (Total: {self.stats['total_rows_read']:,})")
                yield chunk
                
        except Exception as e:
            logger.error(f"❌ Error extracting data: {e}", exc_info=True)
            raise
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform and clean data
        
        Args:
            df: Raw DataFrame chunk
            
        Returns:
            Cleaned DataFrame
        """
        logger.info(f"🔄 Transforming {len(df)} rows...")
        
        # Make a copy to avoid modifying original
        df_clean = df.copy()
        
        # 1. Clean text fields - uppercase and strip
        text_columns = ['matricula', 'departamento', 'municipio', 'tipo_predio', 
                       'nombre_natujur', 'estado_folio']
        for col in text_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.upper().str.strip()
                df_clean[col] = df_clean[col].replace('NAN', None)
        
        # 2. Validate and clean numeric fields
        if 'valor_acto' in df_clean.columns:
            # Remove negative values
            df_clean.loc[df_clean['valor_acto'] < 0, 'valor_acto'] = None
            # Cap extreme values (> 1 trillion COP is unrealistic)
            df_clean.loc[df_clean['valor_acto'] > 1e12, 'valor_acto'] = None
        
        # 3. Clean area fields
        for area_col in ['area_terreno', 'area_construida']:
            if area_col in df_clean.columns:
                df_clean.loc[df_clean[area_col] < 0, area_col] = None
                df_clean.loc[df_clean[area_col] > 1e8, area_col] = None  # Cap at 100M m²
        
        # 4. Validate dates
        if 'fecha_radicacion' in df_clean.columns:
            # Remove future dates
            df_clean.loc[df_clean['fecha_radicacion'] > pd.Timestamp.now(), 'fecha_radicacion'] = None
            # Remove very old dates (before 1900)
            df_clean.loc[df_clean['fecha_radicacion'] < pd.Timestamp('1900-01-01'), 'fecha_radicacion'] = None
        
        # 5. Ensure matricula exists (required field)
        df_clean = df_clean[df_clean['matricula'].notna()]
        df_clean = df_clean[df_clean['matricula'] != 'NONE']
        df_clean = df_clean[df_clean['matricula'] != '']
        
        # 6. Add tiene_valor flag if not present
        if 'tiene_valor' not in df_clean.columns and 'valor_acto' in df_clean.columns:
            df_clean['tiene_valor'] = df_clean['valor_acto'].notna() & (df_clean['valor_acto'] > 0)
        
        rows_removed = len(df) - len(df_clean)
        if rows_removed > 0:
            logger.info(f"⚠️  Removed {rows_removed} invalid rows")
            self.stats['total_rows_rejected'] += rows_removed
        
        return df_clean
    
    def load(self, df: pd.DataFrame, db: Session):
        """
        Load data into PostgreSQL
        
        Args:
            df: Cleaned DataFrame
            db: Database session
        """
        logger.info(f"💾 Loading {len(df)} rows to database...")
        
        try:
            # Convert DataFrame to dict records
            records = df.to_dict('records')
            
            # Bulk insert using SQLAlchemy ORM
            db.bulk_insert_mappings(Transaction, records)
            db.commit()
            
            self.stats['total_rows_loaded'] += len(df)
            self.stats['batches_processed'] += 1
            logger.info(f"✅ Loaded {len(df)} rows successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error loading data: {e}", exc_info=True)
            self.stats['errors'].append(str(e))
            raise
    
    def run(self, input_file: str):
        """
        Run complete ETL pipeline
        
        Args:
            input_file: Path to input CSV file
        """
        start_time = datetime.now()
        
        logger.info("=" * 80)
        logger.info("🚀 STARTING ETL PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Input file: {input_file}")
        logger.info(f"Batch size: {self.batch_size:,}")
        logger.info(f"Started at: {start_time.isoformat()}")
        logger.info("=" * 80)
        
        # Initialize database
        logger.info("🔧 Initializing database...")
        init_db()
        
        # Clear existing data (optional - comment out to append)
        # logger.info("🗑️  Clearing existing data...")
        # with engine.connect() as conn:
        #     conn.execute(text("TRUNCATE TABLE transactions CASCADE"))
        #     conn.commit()
        
        # Process data in chunks
        db = SessionLocal()
        try:
            for chunk in self.extract(input_file):
                # Transform
                chunk_clean = self.transform(chunk)
                
                # Load
                if len(chunk_clean) > 0:
                    self.load(chunk_clean, db)
                else:
                    logger.warning("⚠️  Chunk resulted in 0 valid rows after transformation")
                
                # Progress update
                logger.info(f"📊 Progress: {self.stats['total_rows_loaded']:,} rows loaded, "
                           f"{self.stats['total_rows_rejected']:,} rejected")
        
        finally:
            db.close()
        
        # Final statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info("✅ ETL PIPELINE COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Total rows read:      {self.stats['total_rows_read']:,}")
        logger.info(f"Total rows loaded:    {self.stats['total_rows_loaded']:,}")
        logger.info(f"Total rows rejected:  {self.stats['total_rows_rejected']:,}")
        logger.info(f"Batches processed:    {self.stats['batches_processed']:,}")
        logger.info(f"Processing time:      {duration:.2f} seconds ({duration/60:.2f} minutes)")
        logger.info(f"Throughput:           {self.stats['total_rows_loaded']/duration:.0f} rows/second")
        
        if self.stats['errors']:
            logger.warning(f"⚠️  {len(self.stats['errors'])} errors occurred")
        
        logger.info("=" * 80)
        
        return self.stats


def main():
    parser = argparse.ArgumentParser(description='ETL Pipeline for Real Estate Transactions')
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--batch-size', type=int, default=10000, 
                       help='Number of rows per batch (default: 10000)')
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"❌ Input file not found: {args.input}")
        sys.exit(1)
    
    # Run pipeline
    pipeline = ETLPipeline(batch_size=args.batch_size)
    stats = pipeline.run(str(input_path))
    
    # Exit with error code if there were errors
    if stats['errors']:
        sys.exit(1)


if __name__ == "__main__":
    main()
