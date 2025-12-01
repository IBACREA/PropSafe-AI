#!/usr/bin/env python3
"""
Data ingestion script for real estate transactions.

Processes CSV and Parquet files, validates data, and prepares for ML training.

Usage:
    python ingest.py --input data/raw/transactions.csv --output data/processed/
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.utils.parquet_reader import CSVReader, ParquetReader
from backend.core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


class DataIngestor:
    """Data ingestion and preprocessing pipeline."""
    
    def __init__(self, chunk_size: int = 50000):
        """Initialize data ingestor."""
        self.chunk_size = chunk_size
        self.csv_reader = CSVReader(chunk_size=chunk_size)
        self.parquet_reader = ParquetReader(chunk_size=chunk_size)
        self.stats = {
            'total_rows': 0,
            'valid_rows': 0,
            'invalid_rows': 0,
            'processing_time': 0
        }
    
    def ingest(
        self,
        input_path: str,
        output_path: str,
        validate: bool = True,
        sample_size: Optional[int] = None
    ) -> dict:
        """
        Ingest data from input file to output location.
        
        Args:
            input_path: Path to input file (CSV or Parquet)
            output_path: Path to output directory
            validate: Whether to validate data
            sample_size: Optional sample size for testing
            
        Returns:
            Dictionary with ingestion statistics
        """
        start_time = datetime.now()
        
        logger.info("ingestion_started", input=input_path, output=output_path)
        
        # Determine file type
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Create output directory
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process data in chunks
        all_chunks = []
        
        if input_file.suffix == '.csv':
            reader = self.csv_reader.read_chunks(str(input_file))
        elif input_file.suffix == '.parquet':
            reader = self.parquet_reader.read_chunks(str(input_file))
        else:
            raise ValueError(f"Unsupported file type: {input_file.suffix}")
        
        for i, chunk in enumerate(reader):
            logger.info(f"processing_chunk", chunk_num=i+1, rows=len(chunk))
            
            # Validate if requested
            if validate:
                chunk = self._validate_chunk(chunk)
            
            # Clean data
            chunk = self._clean_chunk(chunk)
            
            all_chunks.append(chunk)
            
            self.stats['total_rows'] += len(chunk)
            
            # Stop if sample size reached
            if sample_size and self.stats['total_rows'] >= sample_size:
                logger.info("sample_size_reached", rows=self.stats['total_rows'])
                break
        
        # Combine all chunks
        if all_chunks:
            df_combined = pd.concat(all_chunks, ignore_index=True)
            
            # Save to parquet
            output_file = output_dir / f"processed_{input_file.stem}.parquet"
            df_combined.to_parquet(output_file, index=False)
            
            logger.info("data_saved", output=str(output_file), rows=len(df_combined))
            
            # Generate statistics
            self._generate_statistics(df_combined, output_dir)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        self.stats['processing_time'] = processing_time
        
        logger.info("ingestion_completed", **self.stats)
        
        return self.stats
    
    def _validate_chunk(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate chunk data."""
        initial_count = len(df)
        
        # Required columns
        required_cols = [
            'valor_acto', 'tipo_acto', 'fecha_acto',
            'departamento', 'municipio', 'tipo_predio',
            'numero_intervinientes', 'estado_folio'
        ]
        
        # Check required columns exist
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning("missing_columns", columns=missing_cols)
        
        # Remove rows with missing required values
        df = df.dropna(subset=[col for col in required_cols if col in df.columns])
        
        # Validate valor_acto
        df = df[df['valor_acto'] > 0]
        df = df[df['valor_acto'] < 100_000_000_000]  # < 100B COP
        
        # Validate numero_intervinientes
        if 'numero_intervinientes' in df.columns:
            df = df[df['numero_intervinientes'] > 0]
            df = df[df['numero_intervinientes'] < 100]
        
        # Validate dates
        if 'fecha_acto' in df.columns:
            df['fecha_acto'] = pd.to_datetime(df['fecha_acto'], errors='coerce')
            df = df[df['fecha_acto'].notna()]
            df = df[df['fecha_acto'] <= datetime.now()]
            df = df[df['fecha_acto'].dt.year >= 1990]
        
        removed_count = initial_count - len(df)
        self.stats['valid_rows'] += len(df)
        self.stats['invalid_rows'] += removed_count
        
        if removed_count > 0:
            logger.info("validation_removed", removed=removed_count)
        
        return df
    
    def _clean_chunk(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize chunk data."""
        
        # Normalize text columns
        text_columns = ['departamento', 'municipio', 'tipo_acto', 'tipo_predio', 'estado_folio']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].str.strip().str.upper()
        
        # Fill missing numerical values
        numerical_cols = ['area_terreno', 'area_construida']
        for col in numerical_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates()
        duplicates_removed = initial_count - len(df)
        
        if duplicates_removed > 0:
            logger.info("duplicates_removed", count=duplicates_removed)
        
        return df
    
    def _generate_statistics(self, df: pd.DataFrame, output_dir: Path):
        """Generate and save data statistics."""
        stats = {
            'total_records': len(df),
            'date_range': {
                'min': df['fecha_acto'].min().isoformat() if 'fecha_acto' in df.columns else None,
                'max': df['fecha_acto'].max().isoformat() if 'fecha_acto' in df.columns else None
            },
            'valor_acto': {
                'mean': float(df['valor_acto'].mean()) if 'valor_acto' in df.columns else None,
                'median': float(df['valor_acto'].median()) if 'valor_acto' in df.columns else None,
                'min': float(df['valor_acto'].min()) if 'valor_acto' in df.columns else None,
                'max': float(df['valor_acto'].max()) if 'valor_acto' in df.columns else None
            },
            'departamentos': df['departamento'].nunique() if 'departamento' in df.columns else 0,
            'municipios': df['municipio'].nunique() if 'municipio' in df.columns else 0,
            'tipos_acto': df['tipo_acto'].value_counts().to_dict() if 'tipo_acto' in df.columns else {}
        }
        
        # Save statistics
        import json
        stats_file = output_dir / 'data_statistics.json'
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info("statistics_saved", file=str(stats_file))


def main():
    """Main ingestion function."""
    parser = argparse.ArgumentParser(
        description='Ingest and process real estate transaction data'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input file path (CSV or Parquet)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='./data/processed',
        help='Output directory path'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        default=True,
        help='Validate data during ingestion'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help='Process only a sample of records'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=50000,
        help='Chunk size for processing'
    )
    
    args = parser.parse_args()
    
    try:
        print("=" * 70)
        print("REAL ESTATE DATA INGESTION")
        print("=" * 70)
        print(f"Input: {args.input}")
        print(f"Output: {args.output}")
        print(f"Validation: {'Enabled' if args.validate else 'Disabled'}")
        if args.sample:
            print(f"Sample size: {args.sample:,} records")
        print()
        
        ingestor = DataIngestor(chunk_size=args.chunk_size)
        stats = ingestor.ingest(
            input_path=args.input,
            output_path=args.output,
            validate=args.validate,
            sample_size=args.sample
        )
        
        print("\n" + "=" * 70)
        print("INGESTION COMPLETED")
        print("=" * 70)
        print(f"Total rows processed: {stats['total_rows']:,}")
        print(f"Valid rows: {stats['valid_rows']:,}")
        print(f"Invalid rows: {stats['invalid_rows']:,}")
        print(f"Processing time: {stats['processing_time']:.2f} seconds")
        print()
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n✗ Error during ingestion: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
