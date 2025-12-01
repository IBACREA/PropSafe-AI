"""
Script para exportar datos limpios a PostgreSQL/SQL Server
Incluye creación de tablas, índices y vistas agregadas
"""
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from pathlib import Path
import logging
from typing import Literal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseExporter:
    """Exportar datos limpios a base de datos SQL"""
    
    def __init__(self, db_type: Literal['postgresql', 'sqlserver'], connection_string: str):
        self.db_type = db_type
        self.engine = create_engine(connection_string)
        logger.info(f"Conectado a base de datos: {db_type}")
    
    def crear_tablas(self):
        """Crear estructura de tablas"""
        logger.info("Creando estructura de tablas...")
        
        # Tabla principal: transacciones
        create_transacciones = """
        CREATE TABLE IF NOT EXISTS transacciones (
            pk VARCHAR(50) PRIMARY KEY,
            matricula VARCHAR(50),
            fecha_radica_texto VARCHAR(50),
            fecha_apertura_texto VARCHAR(50),
            year_radica INTEGER,
            orip FLOAT,
            divipola VARCHAR(20),
            departamento VARCHAR(100),
            municipio VARCHAR(100),
            tipo_predio_zona VARCHAR(50),
            categoria_ruralidad VARCHAR(100),
            num_anotacion VARCHAR(50),
            estado_folio VARCHAR(50),
            folios_derivados TEXT,
            dinamica_inmobiliaria INTEGER,
            cod_natujur VARCHAR(50),
            nombre_natujur VARCHAR(200),
            numero_catastral VARCHAR(100),
            numero_catastral_antiguo VARCHAR(100),
            documento_justificativo TEXT,
            count_a INTEGER,
            count_de INTEGER,
            predios_nuevos INTEGER,
            tiene_valor INTEGER,
            tiene_mas_de_un_valor INTEGER,
            valor FLOAT,
            calidad_datos VARCHAR(20),
            tipo_error VARCHAR(50),
            es_mercado_valido BOOLEAN,
            valor_valido BOOLEAN,
            fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Tabla: estadísticas por departamento-año
        create_stats_dept = """
        CREATE TABLE IF NOT EXISTS stats_departamento_year (
            id SERIAL PRIMARY KEY,
            departamento VARCHAR(100),
            year INTEGER,
            transacciones INTEGER,
            valor_medio FLOAT,
            valor_mediano FLOAT,
            valor_std FLOAT,
            valor_min FLOAT,
            valor_max FLOAT,
            total_registros INTEGER,
            fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(departamento, year)
        );
        """
        
        # Tabla: estadísticas por municipio-año
        create_stats_mun = """
        CREATE TABLE IF NOT EXISTS stats_municipio_year (
            id SERIAL PRIMARY KEY,
            municipio VARCHAR(100),
            departamento VARCHAR(100),
            year INTEGER,
            transacciones INTEGER,
            valor_medio FLOAT,
            valor_mediano FLOAT,
            valor_std FLOAT,
            total_registros INTEGER,
            fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(municipio, departamento, year)
        );
        """
        
        # Tabla: errores y advertencias (para revisión manual)
        create_revisiones = """
        CREATE TABLE IF NOT EXISTS transacciones_revision (
            pk VARCHAR(50) PRIMARY KEY,
            departamento VARCHAR(100),
            municipio VARCHAR(100),
            year_radica INTEGER,
            valor FLOAT,
            tipo_predio_zona VARCHAR(50),
            calidad_datos VARCHAR(20),
            tipo_error VARCHAR(50),
            dinamica_inmobiliaria INTEGER,
            fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado_revision VARCHAR(50) DEFAULT 'PENDIENTE',
            comentario_revision TEXT,
            revisado_por VARCHAR(100),
            fecha_revision TIMESTAMP
        );
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(create_transacciones))
            conn.execute(text(create_stats_dept))
            conn.execute(text(create_stats_mun))
            conn.execute(text(create_revisiones))
            conn.commit()
        
        logger.info("✅ Tablas creadas exitosamente")
    
    def crear_indices(self):
        """Crear índices para optimizar consultas"""
        logger.info("Creando índices...")
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_trans_dept_year ON transacciones(departamento, year_radica);",
            "CREATE INDEX IF NOT EXISTS idx_trans_mun_year ON transacciones(municipio, year_radica);",
            "CREATE INDEX IF NOT EXISTS idx_trans_valor ON transacciones(valor) WHERE valor IS NOT NULL;",
            "CREATE INDEX IF NOT EXISTS idx_trans_calidad ON transacciones(calidad_datos);",
            "CREATE INDEX IF NOT EXISTS idx_trans_mercado ON transacciones(es_mercado_valido) WHERE es_mercado_valido = TRUE;",
            "CREATE INDEX IF NOT EXISTS idx_rev_estado ON transacciones_revision(estado_revision);",
            "CREATE INDEX IF NOT EXISTS idx_rev_tipo ON transacciones_revision(tipo_error);"
        ]
        
        with self.engine.connect() as conn:
            for idx in indices:
                conn.execute(text(idx))
            conn.commit()
        
        logger.info("✅ Índices creados exitosamente")
    
    def crear_vistas(self):
        """Crear vistas agregadas para dashboard"""
        logger.info("Creando vistas agregadas...")
        
        # Vista: Resumen por departamento (últimos 5 años)
        view_resumen_dept = """
        CREATE OR REPLACE VIEW vista_resumen_departamento AS
        SELECT 
            departamento,
            COUNT(*) as total_transacciones,
            SUM(CASE WHEN es_mercado_valido = TRUE THEN 1 ELSE 0 END) as transacciones_mercado,
            SUM(CASE WHEN valor_valido = TRUE THEN 1 ELSE 0 END) as transacciones_valor_valido,
            SUM(CASE WHEN calidad_datos = 'ERROR' THEN 1 ELSE 0 END) as registros_error,
            SUM(CASE WHEN calidad_datos = 'ADVERTENCIA' THEN 1 ELSE 0 END) as registros_advertencia,
            AVG(CASE WHEN valor_valido = TRUE THEN valor ELSE NULL END) as valor_promedio,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor) 
                FILTER (WHERE valor_valido = TRUE) as valor_mediano
        FROM transacciones
        WHERE year_radica >= EXTRACT(YEAR FROM CURRENT_DATE) - 5
        GROUP BY departamento
        ORDER BY total_transacciones DESC;
        """
        
        # Vista: Tendencia anual por departamento
        view_tendencia = """
        CREATE OR REPLACE VIEW vista_tendencia_anual AS
        SELECT 
            departamento,
            year_radica,
            COUNT(*) as transacciones,
            AVG(CASE WHEN valor_valido = TRUE THEN valor ELSE NULL END) as valor_promedio,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor) 
                FILTER (WHERE valor_valido = TRUE) as valor_mediano
        FROM transacciones
        WHERE es_mercado_valido = TRUE AND valor_valido = TRUE
        GROUP BY departamento, year_radica
        ORDER BY departamento, year_radica;
        """
        
        # Vista: Errores por tipo (para dashboard de calidad)
        view_errores = """
        CREATE OR REPLACE VIEW vista_errores_tipo AS
        SELECT 
            tipo_error,
            calidad_datos,
            COUNT(*) as cantidad,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as porcentaje
        FROM transacciones
        WHERE tipo_error IS NOT NULL
        GROUP BY tipo_error, calidad_datos
        ORDER BY cantidad DESC;
        """
        
        # Vista: Transacciones para revisión manual
        view_revision = """
        CREATE OR REPLACE VIEW vista_pendientes_revision AS
        SELECT 
            r.pk,
            r.departamento,
            r.municipio,
            r.year_radica,
            r.valor,
            r.tipo_error,
            r.calidad_datos,
            r.estado_revision,
            r.fecha_carga
        FROM transacciones_revision r
        WHERE r.estado_revision = 'PENDIENTE'
        ORDER BY r.fecha_carga DESC;
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(view_resumen_dept))
            conn.execute(text(view_tendencia))
            conn.execute(text(view_errores))
            conn.execute(text(view_revision))
            conn.commit()
        
        logger.info("✅ Vistas creadas exitosamente")
    
    def cargar_datos(self, data_dir: str):
        """Cargar datos desde parquet a SQL"""
        logger.info(f"Cargando datos desde {data_dir}...")
        data_path = Path(data_dir)
        
        # 1. Cargar dataset completo a tabla principal
        logger.info("  - Cargando tabla transacciones...")
        df_completo = pd.read_parquet(data_path / "completo.parquet")
        
        # Renombrar columnas para SQL (lowercase, sin espacios)
        df_completo.columns = [col.lower().replace(' ', '_') for col in df_completo.columns]
        
        # Cargar en chunks (para datasets grandes)
        chunk_size = 50000
        total_chunks = len(df_completo) // chunk_size + 1
        
        for i in range(0, len(df_completo), chunk_size):
            chunk = df_completo.iloc[i:i+chunk_size]
            chunk.to_sql(
                'transacciones', 
                self.engine, 
                if_exists='append' if i > 0 else 'replace',
                index=False,
                method='multi',
                chunksize=1000
            )
            logger.info(f"    Chunk {i//chunk_size + 1}/{total_chunks} cargado")
        
        logger.info(f"✅ Tabla transacciones: {len(df_completo):,} registros")
        
        # 2. Cargar estadísticas
        logger.info("  - Cargando estadísticas...")
        
        stats_files = {
            'stats_por_departamento_año.parquet': 'stats_departamento_year',
            'stats_por_municipio_año.parquet': 'stats_municipio_year'
        }
        
        for file_name, table_name in stats_files.items():
            if (data_path / file_name).exists():
                df_stats = pd.read_parquet(data_path / file_name)
                df_stats.columns = [col.lower().replace(' ', '_') for col in df_stats.columns]
                df_stats.to_sql(table_name, self.engine, if_exists='replace', index=False)
                logger.info(f"✅ Tabla {table_name}: {len(df_stats):,} registros")
        
        # 3. Cargar registros para revisión
        logger.info("  - Cargando registros para revisión...")
        
        df_errores = pd.read_parquet(data_path / "errores.parquet")
        df_advertencias = pd.read_parquet(data_path / "advertencias.parquet")
        df_revision = pd.concat([df_errores, df_advertencias], ignore_index=True)
        
        # Seleccionar solo columnas relevantes
        cols_revision = [
            'pk', 'departamento', 'municipio', 'year_radica', 'valor',
            'tipo_predio_zona', 'calidad_datos', 'tipo_error', 'dinamica_inmobiliaria'
        ]
        df_revision = df_revision[[col.lower() for col in cols_revision if col.lower() in df_revision.columns]]
        
        df_revision.to_sql('transacciones_revision', self.engine, if_exists='replace', index=False)
        logger.info(f"✅ Tabla transacciones_revision: {len(df_revision):,} registros")
    
    def setup_database(self, data_dir: str):
        """Setup completo: crear estructura y cargar datos"""
        logger.info("=" * 80)
        logger.info("INICIANDO SETUP DE BASE DE DATOS")
        logger.info("=" * 80)
        
        self.crear_tablas()
        self.crear_indices()
        self.cargar_datos(data_dir)
        self.crear_vistas()
        
        logger.info("=" * 80)
        logger.info("✅ SETUP COMPLETADO EXITOSAMENTE")
        logger.info("=" * 80)


if __name__ == "__main__":
    # Configuración para PostgreSQL
    # CONNECTION_STRING = "postgresql://usuario:password@localhost:5432/inmobiliario"
    
    # Configuración para SQL Server
    # CONNECTION_STRING = "mssql+pyodbc://usuario:password@localhost/inmobiliario?driver=ODBC+Driver+17+for+SQL+Server"
    
    # Por defecto usamos SQLite para pruebas
    CONNECTION_STRING = "sqlite:///data/clean/inmobiliario.db"
    
    # Ejecutar setup
    exporter = DatabaseExporter('postgresql', CONNECTION_STRING)
    exporter.setup_database('data/clean')
    
    print("\n✅ Base de datos configurada!")
    print("\nTablas creadas:")
    print("  - transacciones (datos completos)")
    print("  - stats_departamento_year (agregados por depto)")
    print("  - stats_municipio_year (agregados por municipio)")
    print("  - transacciones_revision (errores/advertencias)")
    print("\nVistas creadas:")
    print("  - vista_resumen_departamento")
    print("  - vista_tendencia_anual")
    print("  - vista_errores_tipo")
    print("  - vista_pendientes_revision")
