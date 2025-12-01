# Real Estate Risk Platform - ETL & ML Pipeline

## 🚀 Quick Start Guide

Este guide te lleva paso a paso desde tu CSV de 8GB hasta tener la plataforma completa funcionando con IA.

---

## 📋 Pre-requisitos

### 1. Instalar PostgreSQL

**Windows:**
```powershell
# Descargar e instalar desde https://www.postgresql.org/download/windows/
# O usar Chocolatey:
choco install postgresql

# Iniciar servicio
Start-Service postgresql
```

**Crear base de datos:**
```powershell
psql -U postgres
CREATE DATABASE real_estate_risk;
\q
```

### 2. Instalar Dependencias Python

```powershell
# Activar entorno virtual
& .venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🔧 Paso 1: Configurar Base de Datos

### 1.1 Crear archivo .env

```powershell
# Copiar ejemplo
cp .env.example .env

# Editar .env con tus credenciales:
# DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/real_estate_risk
```

### 1.2 Inicializar tablas

```powershell
python scripts/setup_database.py
```

**Output esperado:**
```
==================================================
DATABASE SETUP
==================================================

1. Testing database connection...
✅ Database connection successful

2. Creating database tables...
✅ Tables created successfully

📊 Created 2 tables:
   - transactions
   - model_metadata

3. Creating indexes...
✅ Indexes created successfully

✅ DATABASE SETUP COMPLETED SUCCESSFULLY
```

---

## 📊 Paso 2: Ejecutar Pipeline ETL

### 2.1 Procesar tu CSV de 8GB

```powershell
python data/etl_pipeline.py --input "C:/ruta/a/tu/archivo-8gb.csv" --batch-size 10000
```

**Parámetros:**
- `--input`: Ruta a tu archivo CSV
- `--batch-size`: Número de registros por lote (10000 recomendado para 8GB, 5000 si tienes poca RAM)

**Output esperado:**
```
================================================================================
🚀 STARTING ETL PIPELINE
================================================================================
Input file: C:/ruta/a/tu/archivo-8gb.csv
Batch size: 10,000
Started at: 2025-11-28T10:30:00
================================================================================

📂 Extracting data from: C:/ruta/a/tu/archivo-8gb.csv
📦 Chunk 1: 10,000 rows (Total: 10,000)
🔄 Transforming 10,000 rows...
💾 Loading 10,000 rows to database...
  ✅ Loaded 10,000 rows successfully
📊 Progress: 10,000 rows loaded, 50 rejected

[... proceso continúa ...]

================================================================================
✅ ETL PIPELINE COMPLETED
================================================================================
Total rows read:      8,234,567
Total rows loaded:    8,156,234
Total rows rejected:  78,333
Batches processed:    823
Processing time:      1,234.56 seconds (20.58 minutes)
Throughput:           6,604 rows/second
================================================================================
```

### 2.2 Verificar datos cargados

```powershell
# Contar registros
psql -U postgres -d real_estate_risk -c "SELECT COUNT(*) FROM transactions;"

# Ver primeros registros
psql -U postgres -d real_estate_risk -c "SELECT * FROM transactions LIMIT 5;"

# Estadísticas por departamento
psql -U postgres -d real_estate_risk -c "SELECT departamento, COUNT(*) as total FROM transactions GROUP BY departamento ORDER BY total DESC LIMIT 10;"
```

---

## 🧠 Paso 3: Entrenar Modelos de IA

### 3.1 Entrenar con muestra (recomendado primero)

```powershell
# Entrenar con 100,000 registros (más rápido para pruebas)
python ml/train_from_db.py --sample-size 100000 --output ml/models
```

### 3.2 Entrenar con todos los datos

```powershell
# Entrenar con todos los datos (puede tomar 30-60 minutos)
python ml/train_from_db.py --output ml/models
```

**Output esperado:**
```
================================================================================
🚀 MACHINE LEARNING MODEL TRAINING
================================================================================
Started at: 2025-11-28T11:00:00
Output directory: D:\projects\datos\ml\models
================================================================================

📂 Loading data from PostgreSQL...
  ✅ Loaded 100,000 transactions

🔧 Performing feature engineering...
  ✅ Created 34 features
  💾 Feature engineer saved to: ml/models/feature_engineer.joblib

📊 Train: 80,000 | Test: 20,000

================================================================================
TRAINING MODELS
================================================================================

🌲 Training Isolation Forest...
  ✓ Anomalies in test: 2,134 (10.7%)
  💾 Saved to: ml/models/isolation_forest.joblib

🎯 Training Local Outlier Factor...
  ✓ Anomalies in test: 1,987 (9.9%)
  💾 Saved to: ml/models/local_outlier_factor.joblib

================================================================================
ENSEMBLE MODEL
================================================================================

  High Risk: 1,456 (7.3%)
  Suspicious: 3,234 (16.2%)
  Normal: 15,310 (76.5%)

📊 Calculating feature importance...
  Top 10 features:
    valor_acto_por_area           : 0.7823
    valor_acto_normalizado        : 0.6912
    count_total_intervinientes    : 0.5634
    valor_acto_log                : 0.5123
    ...

💾 Saving model metadata to database...
  ✅ Metadata saved to database

================================================================================
✅ TRAINING COMPLETED SUCCESSFULLY
================================================================================
Duration: 387.45 seconds (6.46 minutes)
Summary saved to: ml/models/training_summary.json
================================================================================
```

### 3.3 Aplicar modelos a TODA la base de datos

```powershell
# Aplicar scores de anomalía a todas las transacciones
python ml/apply_models.py --batch-size 5000
```

**Output esperado:**
```
================================================================================
🎯 APPLYING ML MODELS TO DATABASE
================================================================================
Started at: 2025-11-28T11:15:00
Batch size: 5,000
================================================================================

📦 Loading trained models...
  ✅ Feature engineer loaded
  ✅ Isolation Forest loaded
  ✅ Local Outlier Factor loaded

📊 Total transactions in database: 8,156,234

📦 Processing batch 0 - 5,000
  ✅ Updated 5,000 records
  🚨 Anomalies in batch: 487 (9.7%)
  📈 Progress: 5,000/8,156,234 (0.1%)

[... proceso continúa ...]

================================================================================
✅ MODEL APPLICATION COMPLETED
================================================================================
Total processed: 8,156,234
Anomalies found: 815,623 (10.0%)
Duration: 1,843.21 seconds (30.72 minutes)
Throughput: 4,426 records/second
================================================================================
```

---

## 🚀 Paso 4: Iniciar la Aplicación

### 4.1 Backend con PostgreSQL

```powershell
# Actualizar main_simple.py para usar property_db
cd backend
& D:\projects\datos\.venv\Scripts\python.exe -m uvicorn main_simple:app --reload --port 8080
```

### 4.2 Frontend

```powershell
cd frontend
npm run dev
```

### 4.3 Probar el sistema

Abrir navegador en `http://localhost:3001/property-search`

Buscar cualquier matrícula de tu base de datos.

---

## 📊 Verificación de Resultados

### Ver estadísticas en PostgreSQL

```sql
-- Total de anomalías
SELECT 
    risk_classification, 
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transactions), 2) as percentage
FROM transactions
WHERE anomaly_score IS NOT NULL
GROUP BY risk_classification
ORDER BY total DESC;

-- Departamentos con más anomalías
SELECT 
    departamento,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomalies,
    ROUND(SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as anomaly_rate
FROM transactions
GROUP BY departamento
ORDER BY anomaly_rate DESC
LIMIT 10;

-- Distribución de scores de anomalía
SELECT 
    CASE 
        WHEN anomaly_score < 0.2 THEN '0.0-0.2'
        WHEN anomaly_score < 0.4 THEN '0.2-0.4'
        WHEN anomaly_score < 0.6 THEN '0.4-0.6'
        WHEN anomaly_score < 0.8 THEN '0.6-0.8'
        ELSE '0.8-1.0'
    END as score_range,
    COUNT(*) as count
FROM transactions
WHERE anomaly_score IS NOT NULL
GROUP BY score_range
ORDER BY score_range;
```

---

## 🔄 Flujo Completo (Resumen)

```
CSV 8GB
   ↓
[ETL Pipeline] → PostgreSQL (transactions table)
   ↓
[Train Models] → ML Models (Isolation Forest + LOF)
   ↓
[Apply Models] → PostgreSQL (actualiza anomaly_score, is_anomaly)
   ↓
[Backend API] → FastAPI con PostgreSQL
   ↓
[Frontend] → React (búsqueda de propiedades)
```

---

## 🎯 Próximos Pasos

1. **Optimizar consultas:**
   ```sql
   CREATE INDEX idx_anomaly_score_high ON transactions(anomaly_score) 
   WHERE anomaly_score >= 0.7;
   ```

2. **Actualizar modelos periódicamente:**
   ```powershell
   # Cada semana/mes
   python ml/train_from_db.py --sample-size 200000
   python ml/apply_models.py --batch-size 5000
   ```

3. **Monitoreo:**
   ```powershell
   # Ver logs en tiempo real
   tail -f logs/etl.log
   ```

4. **Backup:**
   ```powershell
   # Backup de base de datos
   pg_dump -U postgres real_estate_risk > backup_$(date +%Y%m%d).sql
   ```

---

## 🐛 Troubleshooting

### Error: "Cannot connect to database"
```powershell
# Verificar que PostgreSQL está corriendo
Get-Service postgresql

# Iniciar servicio si está detenido
Start-Service postgresql

# Probar conexión
psql -U postgres -d real_estate_risk -c "SELECT 1;"
```

### Error: "Out of memory" durante ETL
```powershell
# Reducir batch size
python data/etl_pipeline.py --input file.csv --batch-size 5000
```

### Error: "Models not found"
```powershell
# Verificar que existen los modelos
ls ml/models/

# Si no existen, entrenar primero
python ml/train_from_db.py
```

### Performance lento en búsquedas
```sql
-- Crear índices adicionales
CREATE INDEX CONCURRENTLY idx_matricula_upper ON transactions(UPPER(matricula));
CREATE INDEX CONCURRENTLY idx_fecha_desc ON transactions(fecha_radicacion DESC);
```

---

## 📞 Soporte

Si encuentras problemas:

1. Revisar logs: `logs/`
2. Verificar .env: `DATABASE_URL` correcto
3. Verificar PostgreSQL: `psql -U postgres -l`
4. Verificar modelos: `ls ml/models/`

---

**¡Listo! Tu plataforma de detección de fraude inmobiliario con IA está completa** 🎉
