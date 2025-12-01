# Arquitectura del Sistema de Detección de Anomalías Inmobiliarias

## Fecha: 28 de noviembre de 2025

## 📋 Resumen Ejecutivo

Sistema profesional para detectar anomalías en transacciones inmobiliarias colombianas usando enfoque híbrido: **ETL + Estadística + Machine Learning + Dashboard**.

### Flujo General:
```
Datos Crudos (30.9M) 
  → ETL Limpieza 
  → Base de Datos SQL (5.7M limpios)
  → 2 Caminos Paralelos:
     ├─ Estadística: Detección reglas de negocio + Dashboard
     └─ ML: Modelo anomalías avanzadas
```

---

## 🏗️ Componentes del Sistema

### 1. ETL Pipeline (✅ IMPLEMENTADO)

**Archivo**: `etl/clean_and_transform.py`

**Funciones**:
- ✅ Validación y tipado de datos
- ✅ Clasificación de calidad (OK, ADVERTENCIA, ERROR)
- ✅ Generación de múltiples datasets:
  - `completo.parquet` - Todos tipados (30.9M)
  - `limpio.parquet` - Solo OK
  - `mercado.parquet` - Dinámica=1
  - `ml_training.parquet` - Listo para ML (5.7M)
  - `errores.parquet` - Revisión manual
  - `advertencias.parquet` - Revisión manual

**Reglas de Limpieza**:
```python
1. Dinámica_Inmobiliaria == '1' (solo mercado)
2. VALOR IS NOT NULL
3. VALOR numérico (no texto)
4. VALOR >= 1,000,000 COP (mín $250 USD)
5. VALOR <= 10,000,000,000 COP (máx $2.5M USD)
6. YEAR_RADICA entre 2000-2025
7. DEPARTAMENTO y MUNICIPIO válidos
```

**Output**: `data/clean/` con 6 datasets + estadísticas

---

### 2. Base de Datos SQL (✅ IMPLEMENTADO)

**Archivo**: `etl/export_to_database.py`

**Estructura**:

#### Tablas Principales:
1. **`transacciones`** - Datos completos (30.9M registros)
   - Todos los campos tipados correctamente
   - Columnas adicionales: `calidad_datos`, `tipo_error`, `es_mercado_valido`, `valor_valido`
   
2. **`stats_departamento_year`** - Agregados por departamento/año
   - Campos: transacciones, valor_medio, valor_mediano, valor_std, valor_min, valor_max
   
3. **`stats_municipio_year`** - Agregados por municipio/año (top 50)
   - Similar a departamento pero granularidad fina
   
4. **`transacciones_revision`** - Errores y advertencias
   - Para revisión manual en dashboard
   - Campos: estado_revision, comentario_revision, revisado_por, fecha_revision

#### Vistas (para dashboard):
- `vista_resumen_departamento` - KPIs por departamento
- `vista_tendencia_anual` - Series temporales
- `vista_errores_tipo` - Distribución de errores
- `vista_pendientes_revision` - Cola de revisión manual

#### Índices (optimización):
- Por departamento + año
- Por municipio + año  
- Por valor
- Por calidad
- Por mercado válido

**Soporte**: PostgreSQL, SQL Server, SQLite

---

### 3. Detección Estadística de Errores (🔄 PENDIENTE)

**Archivo**: `estadistica/detectar_errores_obvios.py` (a crear)

**Reglas de Negocio**:

```sql
-- Error 1: Valor muy bajo para tipo urbano
SELECT * FROM transacciones
WHERE tipo_predio_zona = 'URBANO' 
  AND municipio IN (top 10 ciudades)
  AND valor < 10_000_000  -- < $2,500 USD en Bogotá = ERROR

-- Error 2: Valor extremo vs mediana regional
SELECT * FROM transacciones t
JOIN stats_departamento_year s 
  ON t.departamento = s.departamento 
  AND t.year_radica = s.year
WHERE t.valor > s.valor_mediano * 50  -- 50x mediana = SOSPECHOSO

-- Error 3: Propiedad rural más cara que urbana
SELECT * FROM transacciones
WHERE tipo_predio_zona = 'RURAL'
  AND valor > (
    SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY valor)
    FROM transacciones
    WHERE tipo_predio_zona = 'URBANO' 
      AND departamento = t.departamento
  )

-- Error 4: Transacción múltiple sospechosa
SELECT matricula, COUNT(*) as veces, SUM(valor) as total
FROM transacciones
WHERE year_radica = CURRENT_YEAR
GROUP BY matricula
HAVING COUNT(*) > 10  -- más de 10 transacciones/año = fraude posible

-- Error 5: Valor constante repetido (copiar-pegar)
SELECT valor, COUNT(*) as repeticiones,
       ARRAY_AGG(municipio) as municipios
FROM transacciones
WHERE valor IS NOT NULL
GROUP BY valor
HAVING COUNT(*) > 100 AND COUNT(DISTINCT municipio) > 10
```

**Output**: 
- Tabla `anomalias_estadisticas` con score de severidad
- CSV para revisión: `errores_estadisticos_YYYY-MM-DD.csv`

---

### 4. Machine Learning - Detección Avanzada (🔄 PENDIENTE)

**Archivo**: `ml/train_anomaly_detector.py` (actualizar)

**Pipeline ML**:

#### Feature Engineering (20-25 features):
```python
FEATURES_CORE = [
    # Valor
    'valor',                    # Original
    'log_valor',                # Log-transform
    
    # Geográficos
    'departamento_encoded',     # Label encoding (33 valores)
    'municipio_encoded',        # Label encoding top 100 + 'OTROS'
    'es_ciudad_grande',         # Top 10 municipios
    'es_departamento_top5',     # Top 5 departamentos
    
    # Temporales
    'year_radica',              # 2015-2023
    'años_desde_2015',          # Normalizado
    
    # Tipo propiedad
    'es_urbano',                # Boolean
    'es_rural',                 # Boolean
    'es_ciudad_aglomeracion',   # Categoría ruralidad
    
    # Transacción
    'predios_nuevos',           # 0/1
    'count_a',                  # Frecuencia transacciones
    'count_de',                 # Frecuencia
]

FEATURES_AGREGADOS = [
    # Ratios vs mercado local
    'valor_vs_mediana_dept_year',   # valor / mediana_departamento_año
    'valor_vs_mediana_mun_year',    # valor / mediana_municipio_año
    'zscore_valor_grupo',           # Z-score dentro grupo (dept+año+tipo)
    
    # Contexto mercado
    'mediana_dept_year',            # Mediana del grupo
    'std_dept_year',                # Volatilidad del grupo
    'percentil_valor_dept',         # Percentil dentro grupo
]

TOTAL: ~20 features
```

#### Modelo Híbrido:
1. **Isolation Forest** (sklearn, CPU multi-core)
   - n_estimators=200
   - contamination=0.05 (esperamos 5% anomalías reales)
   - Fast screening: 25-30 min para 5.7M registros

2. **Autoencoder** (PyTorch, CPU/GPU)
   - Architecture: [20] → 64 → 32 → 16 → 32 → 64 → [20]
   - Entrena solo en datos "normales" (95%)
   - Detecta outliers por reconstruction error
   - Tiempo: 45-60 min CPU, 15-20 min GPU

3. **Ensemble**:
   - Confirmed: IF + AE ambos detectan (alta confianza)
   - Suspects: Solo uno detecta (media confianza)
   - Score final: weighted average

**Outputs**:
- `ml/models/isolation_forest.joblib`
- `ml/models/autoencoder.pth`
- `ml/models/feature_scaler.joblib`
- `ml/models/label_encoders.joblib`
- `data/results/anomalias_ml_YYYY-MM-DD.parquet` con scores

---

### 5. Dashboard & API (🔄 PENDIENTE)

**Tecnologías**: FastAPI + React + Plotly

#### API Backend (`api/main.py`):

```python
@app.get("/api/stats/resumen")
def get_resumen_general():
    """KPIs generales del sistema"""
    return {
        "total_registros": 30_903_248,
        "registros_limpios": 5_702_742,
        "errores_detectados": 2_345_678,
        "anomalias_ml": 285_137,
        "pendientes_revision": 45_123
    }

@app.get("/api/stats/departamento/{nombre}")
def get_stats_departamento(nombre: str, year: int = None):
    """Estadísticas por departamento"""
    # Query a vista_resumen_departamento
    
@app.get("/api/anomalias/estadisticas")
def get_anomalias_estadisticas(
    tipo: str = None,
    severidad: str = None,
    limit: int = 100
):
    """Anomalías detectadas por reglas de negocio"""
    
@app.get("/api/anomalias/ml")
def get_anomalias_ml(
    score_min: float = 0.7,
    departamento: str = None,
    limit: int = 100
):
    """Anomalías detectadas por ML"""
    
@app.post("/api/revision/marcar")
def marcar_revision(pk: str, estado: str, comentario: str):
    """Marcar registro como revisado"""
    # UPDATE transacciones_revision
```

#### Frontend Dashboard:

**Páginas**:
1. **Overview** - KPIs globales, gráficos resumen
2. **Exploración** - Filtros por depto/mun/año, tablas interactivas
3. **Anomalías Estadísticas** - Lista de errores obvios
4. **Anomalías ML** - Lista con scores, ordenable
5. **Revisión Manual** - Interface para marcar/comentar registros
6. **Reportes** - Exportar CSV/Excel filtrados

**Visualizaciones**:
- Mapa coroplético: anomalías por departamento
- Serie temporal: tendencia precios por región
- Box plots: distribución valores por tipo predio
- Scatter plot: valor vs mediana regional (outliers destacados)
- Tabla paginada: registros para revisión

---

## 📊 Flujo de Datos Completo

```
┌─────────────────────────────────────────────────────────────┐
│                   DATOS CRUDOS (30.9M)                      │
│                     datos.parquet                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ETL: clean_and_transform.py                     │
│  • Tipado correcto (VALOR float, YEAR int, etc.)           │
│  • Clasificación calidad (OK/ADVERTENCIA/ERROR)            │
│  • Filtros: Dinámica=1, Valor 1M-10B COP                   │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌──────────────────────┐    ┌──────────────────────┐
│  DATASET COMPLETO    │    │   DATASET ML_TRAIN   │
│   (30.9M tipados)    │    │   (5.7M limpios)     │
└──────────┬───────────┘    └──────────┬───────────┘
           │                           │
           ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│           BASE DE DATOS SQL (PostgreSQL)                    │
│  Tablas:                                                     │
│    • transacciones (30.9M)                                  │
│    • stats_departamento_year                                │
│    • stats_municipio_year                                   │
│    • transacciones_revision (errores + advertencias)        │
│  Vistas:                                                     │
│    • vista_resumen_departamento                             │
│    • vista_tendencia_anual                                  │
│    • vista_errores_tipo                                     │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
    ┌────────▼────────┐         ┌───────▼────────┐
    │  ESTADÍSTICA    │         │   MACHINE      │
    │  (Reglas SQL)   │         │   LEARNING     │
    │                 │         │  (IF + AE)     │
    │ • Valor vs      │         │                │
    │   mediana >50x  │         │ • 20 features  │
    │ • Urbano < 10M  │         │ • Ensemble     │
    │ • Rural > P95   │         │ • Scores 0-1   │
    │ • Frecuencia    │         │                │
    │   sospechosa    │         │                │
    └────────┬────────┘         └───────┬────────┘
             │                          │
             │      ┌───────────────────┘
             │      │
             ▼      ▼
┌─────────────────────────────────────────────────────────────┐
│                 TABLA: anomalias_detectadas                  │
│  Columnas:                                                   │
│    • pk, departamento, municipio, year, valor               │
│    • tipo_deteccion (ESTADISTICA / ML)                      │
│    • score_severidad (0-1)                                  │
│    • regla_violada / ml_score                               │
│    • estado_revision (PENDIENTE / REVISADO / CONFIRMADO)    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              API + DASHBOARD (FastAPI + React)               │
│  Endpoints:                                                  │
│    • GET /api/stats/resumen                                 │
│    • GET /api/anomalias/estadisticas                        │
│    • GET /api/anomalias/ml                                  │
│    • POST /api/revision/marcar                              │
│  UI:                                                         │
│    • Tablas interactivas con filtros                        │
│    • Visualizaciones (mapas, gráficos)                      │
│    • Interface revisión manual                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Próximos Pasos

### Fase 1: ETL + Base de Datos (✅ Completado ~70%)
- [x] Pipeline ETL con clasificación calidad
- [x] Esquema SQL con tablas y vistas
- [ ] Ejecutar ETL en dataset completo
- [ ] Cargar a PostgreSQL
- [ ] Validar integridad datos en SQL

### Fase 2: Detección Estadística (⏳ Siguiente)
- [ ] Implementar 10 reglas de negocio clave
- [ ] Generar tabla `anomalias_estadisticas`
- [ ] Probar queries de detección
- [ ] Calcular tasas de falsos positivos

### Fase 3: Machine Learning (⏳ Pendiente)
- [ ] Feature engineering completo (20 features)
- [ ] Entrenar Isolation Forest
- [ ] Entrenar Autoencoder
- [ ] Validar con datos conocidos
- [ ] Generar scores para 5.7M registros

### Fase 4: API + Dashboard (⏳ Pendiente)
- [ ] API FastAPI con endpoints básicos
- [ ] Frontend React con páginas principales
- [ ] Integración SQL queries
- [ ] Interface revisión manual
- [ ] Deploy

---

## 📈 Métricas Esperadas

### ETL:
- **Input**: 30,903,248 registros
- **Output ML**: 5,702,742 registros limpios (18.5%)
- **Errores**: ~2.3M (7.5%)
- **Advertencias**: ~10.7M (34.6%)

### Detección Estadística:
- **Errores obvios esperados**: ~500k (10% del limpio)
- **Ejemplos**:
  - Valor urbano < 1M en Bogotá: ~50k
  - Valor > 50x mediana: ~10k
  - Frecuencia sospechosa: ~5k

### Machine Learning:
- **Anomalías ML esperadas**: ~285k (5% contamination)
- **Tiempo entrenamiento**: 90-120 min (CPU)
- **Precisión esperada**: 85-90%
- **Recall esperado**: 70-80%

### Dashboard:
- **Usuarios concurrentes**: 5-10
- **Queries/seg**: < 100ms (con índices)
- **Revisiones/día**: 100-500 registros

---

## 🔧 Requisitos Técnicos

### Software:
- Python 3.10+
- PostgreSQL 14+ (o SQL Server 2019+)
- Node.js 18+ (para frontend)

### Librerías Python:
```
pandas>=2.0
pyarrow>=12.0
sqlalchemy>=2.0
psycopg2>=2.9  # PostgreSQL
scikit-learn>=1.3
torch>=2.0
fastapi>=0.100
uvicorn>=0.23
```

### Hardware Recomendado:
- **ETL**: 16GB RAM, CPU 4+ cores
- **ML Training**: 16GB RAM, GPU opcional (acelera 3-4x)
- **Base de Datos**: 50GB disk, 8GB RAM
- **Dashboard**: 2GB RAM, CPU 2+ cores

---

## 📝 Notas Finales

Este sistema implementa **3 capas de calidad**:

1. **ETL**: Limpieza básica, tipado, filtros rango
2. **Estadística**: Reglas de negocio específicas del dominio
3. **ML**: Patrones complejos no capturables con reglas

**Ventajas**:
- ETL elimina 80% de basura automáticamente
- Estadística detecta errores obvios rápido (SQL queries)
- ML encuentra anomalías sutiles (valores razonables pero sospechosos)
- Dashboard permite revisión manual expertos

**Resultado**: Sistema robusto, escalable, con múltiples niveles de detección.
