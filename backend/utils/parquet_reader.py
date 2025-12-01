import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from typing import Iterator, Optional
from datetime import datetime

from core.logger import get_logger
from core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class ParquetReader:
    """
    Memory-efficient Parquet file reader with chunking support.
    
    Handles large datasets by processing in configurable chunks.
    """
    
    def __init__(self, chunk_size: int = None):
        """
        Initialize Parquet reader.
        
        Args:
            chunk_size: Number of rows per chunk (default from settings)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        logger.info("parquet_reader_initialized", chunk_size=self.chunk_size)
    
    def read_chunks(
        self, 
        file_path: str, 
        columns: Optional[list] = None,
        filters: Optional[list] = None
    ) -> Iterator[pd.DataFrame]:
        """
        Read Parquet file in chunks.
        
        Args:
            file_path: Path to Parquet file
            columns: List of columns to read (None = all)
            filters: Pyarrow filters for predicate pushdown
            
        Yields:
            DataFrame chunks
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info("reading_parquet", file=str(path), chunk_size=self.chunk_size)
            
            # Open Parquet file
            parquet_file = pq.ParquetFile(path)
            
            # Read in batches
            for batch in parquet_file.iter_batches(
                batch_size=self.chunk_size,
                columns=columns,
                use_threads=True
            ):
                df = batch.to_pandas()
                
                logger.debug("chunk_read", rows=len(df))
                yield df
                
        except Exception as e:
            logger.error("parquet_read_error", error=str(e), file=file_path)
            raise
    
    def read_full(
        self, 
        file_path: str,
        columns: Optional[list] = None
    ) -> pd.DataFrame:
        """
        Read entire Parquet file into memory.
        
        Warning: Use only for small files or when necessary.
        
        Args:
            file_path: Path to Parquet file
            columns: List of columns to read (None = all)
            
        Returns:
            Complete DataFrame
        """
        try:
            path = Path(file_path)
            logger.info("reading_full_parquet", file=str(path))
            
            df = pd.read_parquet(path, columns=columns)
            
            logger.info("parquet_loaded", rows=len(df), cols=len(df.columns))
            return df
            
        except Exception as e:
            logger.error("parquet_read_error", error=str(e), file=file_path)
            raise
    
    def get_metadata(self, file_path: str) -> dict:
        """
        Get Parquet file metadata without reading data.
        
        Args:
            file_path: Path to Parquet file
            
        Returns:
            Dictionary with metadata information
        """
        try:
            path = Path(file_path)
            parquet_file = pq.ParquetFile(path)
            
            metadata = {
                "num_rows": parquet_file.metadata.num_rows,
                "num_columns": parquet_file.metadata.num_columns,
                "num_row_groups": parquet_file.num_row_groups,
                "columns": [col.name for col in parquet_file.schema],
                "file_size_mb": path.stat().st_size / (1024 * 1024),
                "created": datetime.fromtimestamp(path.stat().st_ctime).isoformat()
            }
            
            logger.info("parquet_metadata", **metadata)
            return metadata
            
        except Exception as e:
            logger.error("metadata_error", error=str(e), file=file_path)
            raise


class CSVReader:
    """
    Memory-efficient CSV file reader with chunking support.
    """
    
    def __init__(self, chunk_size: int = None):
        """Initialize CSV reader."""
        self.chunk_size = chunk_size or settings.chunk_size
        logger.info("csv_reader_initialized", chunk_size=self.chunk_size)
    
    def read_chunks(
        self,
        file_path: str,
        columns: Optional[list] = None,
        **kwargs
    ) -> Iterator[pd.DataFrame]:
        """
        Read CSV file in chunks.
        
        Args:
            file_path: Path to CSV file
            columns: List of columns to read (None = all)
            **kwargs: Additional arguments for pd.read_csv
            
        Yields:
            DataFrame chunks
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info("reading_csv", file=str(path), chunk_size=self.chunk_size)
            
            # Default CSV parameters
            csv_params = {
                'chunksize': self.chunk_size,
                'low_memory': False,
                'usecols': columns
            }
            csv_params.update(kwargs)
            
            # Read in chunks
            for chunk in pd.read_csv(path, **csv_params):
                logger.debug("chunk_read", rows=len(chunk))
                yield chunk
                
        except Exception as e:
            logger.error("csv_read_error", error=str(e), file=file_path)
            raise
    
    def read_full(
        self,
        file_path: str,
        columns: Optional[list] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Read entire CSV file into memory.
        
        Args:
            file_path: Path to CSV file
            columns: List of columns to read
            **kwargs: Additional arguments for pd.read_csv
            
        Returns:
            Complete DataFrame
        """
        try:
            path = Path(file_path)
            logger.info("reading_full_csv", file=str(path))
            
            csv_params = {'usecols': columns}
            csv_params.update(kwargs)
            
            df = pd.read_csv(path, **csv_params)
            
            logger.info("csv_loaded", rows=len(df), cols=len(df.columns))
            return df
            
        except Exception as e:
            logger.error("csv_read_error", error=str(e), file=file_path)
            raise
