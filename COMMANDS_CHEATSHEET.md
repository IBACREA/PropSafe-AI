# Quick Commands Cheat Sheet

## 🚀 Inicio Rápido

```powershell
# Setup completo en un comando
.\quickstart.ps1

# O manual:
python scripts/setup_database.py                           # 1. Setup DB
python data/etl_pipeline.py --input tu-csv.csv            # 2. ETL
python ml/train_from_db.py --sample-size 100000           # 3. Train ML
python ml/apply_models.py                                  # 4. Apply ML
cd backend; uvicorn main_simple:app --reload --port 8080  # 5. Backend
cd frontend; npm run dev                                   # 6. Frontend
```

---

## 📊 ETL Pipeline

```powershell
# Procesar CSV de 8GB
python data/etl_pipeline.py --input C:/ruta/datos.csv --batch-size 10000

# Con batch más pequeño (si hay problemas de memoria)
python data/etl_pipeline.py --input C:/ruta/datos.csv --batch-size 5000

# Ver progreso en tiempo real
tail -f logs/etl.log
```

---

## 🧠 Machine Learning

```powershell
# Entrenar con muestra (rápido, para pruebas)
python ml/train_from_db.py --sample-size 100000

# Entrenar con todos los datos
python ml/train_from_db.py

# Aplicar modelos a base de datos
python ml/apply_models.py --batch-size 5000

# Ver resumen de entrenamiento
cat ml/models/training_summary.json | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

---

## 🗄️ PostgreSQL

```powershell
# Conectar
psql -U postgres -d real_estate_risk

# Verificar datos cargados
psql -U postgres -d real_estate_risk -c "SELECT COUNT(*) FROM transactions;"

# Ver anomalías
psql -U postgres -d real_estate_risk -c "
SELECT 
    risk_classification, 
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transactions), 2) as pct
FROM transactions
WHERE anomaly_score IS NOT NULL
GROUP BY risk_classification
ORDER BY total DESC;"

# Top 10 anomalías
psql -U postgres -d real_estate_risk -c "
SELECT matricula, departamento, anomaly_score, risk_classification
FROM transactions
WHERE is_anomaly = true
ORDER BY anomaly_score DESC
LIMIT 10;"

# Backup
pg_dump -U postgres real_estate_risk > backup_$(Get-Date -Format yyyyMMdd).sql

# Restore
psql -U postgres real_estate_risk < backup_20250101.sql
```

---

## 🚀 Backend

```powershell
# Iniciar backend
cd backend
& D:\projects\datos\.venv\Scripts\python.exe -m uvicorn main_simple:app --reload --port 8080

# Sin reload (producción)
& D:\projects\datos\.venv\Scripts\python.exe -m uvicorn main_simple:app --port 8080

# Con workers (producción)
& D:\projects\datos\.venv\Scripts\python.exe -m uvicorn main_simple:app --port 8080 --workers 4

# Health check
curl http://localhost:8080/health
curl http://localhost:8080/api/property/health

# Ver docs interactivas
start http://localhost:8080/docs
```

---

## 🎨 Frontend

```powershell
# Iniciar frontend
cd frontend
npm run dev

# Build para producción
npm run build

# Preview de build
npm run preview
```

---

## 🔍 Testing API

```powershell
# Health check
curl http://localhost:8080/api/property/health

# Buscar propiedad
$body = @{matricula="110814602"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/property/search" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Estadísticas
curl http://localhost:8080/api/property/stats

# Chat health
curl http://localhost:8080/api/chat/suggestions
```

---

## 🐛 Troubleshooting

```powershell
# Ver procesos Python
Get-Process | Where-Object {$_.ProcessName -eq "python"}

# Matar todos los Python
Get-Process python | Stop-Process -Force

# Ver qué usa el puerto 8080
Get-NetTCPConnection -LocalPort 8080

# Matar proceso en puerto 8080
Get-NetTCPConnection -LocalPort 8080 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }

# Verificar PostgreSQL corriendo
Get-Service postgresql

# Iniciar PostgreSQL
Start-Service postgresql

# Logs
tail -f logs/app.log
tail -f logs/etl.log
tail -f logs/ml.log

# Espacio en disco
Get-PSDrive C | Select-Object Used,Free

# Tamaño de base de datos
psql -U postgres -d real_estate_risk -c "
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'real_estate_risk';"
```

---

## 📈 Monitoreo

```powershell
# Ver registros procesados
psql -U postgres -d real_estate_risk -c "SELECT COUNT(*) as total FROM transactions;"

# Coverage de ML
psql -U postgres -d real_estate_risk -c "
SELECT 
    COUNT(*) as total,
    COUNT(anomaly_score) as con_scores,
    ROUND(COUNT(anomaly_score) * 100.0 / COUNT(*), 2) as coverage_pct
FROM transactions;"

# Distribución de scores
psql -U postgres -d real_estate_risk -c "
SELECT 
    CASE 
        WHEN anomaly_score < 0.2 THEN 'Muy bajo (0.0-0.2)'
        WHEN anomaly_score < 0.4 THEN 'Bajo (0.2-0.4)'
        WHEN anomaly_score < 0.6 THEN 'Medio (0.4-0.6)'
        WHEN anomaly_score < 0.8 THEN 'Alto (0.6-0.8)'
        ELSE 'Muy alto (0.8-1.0)'
    END as rango,
    COUNT(*) as cantidad
FROM transactions
WHERE anomaly_score IS NOT NULL
GROUP BY rango
ORDER BY rango;"

# Top departamentos con más anomalías
psql -U postgres -d real_estate_risk -c "
SELECT 
    departamento,
    COUNT(*) as total,
    SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomalias,
    ROUND(SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as tasa_pct
FROM transactions
GROUP BY departamento
ORDER BY tasa_pct DESC
LIMIT 10;"
```

---

## 🔧 Mantenimiento

```powershell
# Re-entrenar modelos (mensual)
python ml/train_from_db.py --sample-size 200000
python ml/apply_models.py

# Vacuum database (optimización)
psql -U postgres -d real_estate_risk -c "VACUUM ANALYZE transactions;"

# Reindexar
psql -U postgres -d real_estate_risk -c "REINDEX TABLE transactions;"

# Ver índices
psql -U postgres -d real_estate_risk -c "
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'transactions';"

# Crear índice adicional
psql -U postgres -d real_estate_risk -c "
CREATE INDEX CONCURRENTLY idx_custom 
ON transactions(campo1, campo2) 
WHERE condicion;"
```

---

## 📦 Deployment

```powershell
# Crear requirements.txt actualizado
pip freeze > requirements.txt

# Exportar schema de DB
pg_dump -U postgres -d real_estate_risk --schema-only > schema.sql

# Exportar solo datos de una tabla
pg_dump -U postgres -d real_estate_risk -t transactions --data-only > data.sql

# Build frontend
cd frontend
npm run build
# Los archivos están en frontend/dist/

# Docker (si aplica)
docker-compose up -d
docker-compose logs -f
```

---

## 🎯 Queries Útiles

```sql
-- Matrícula con más transacciones
SELECT matricula, COUNT(*) as total
FROM transactions
GROUP BY matricula
ORDER BY total DESC
LIMIT 10;

-- Transacciones más caras
SELECT matricula, departamento, municipio, valor_acto, nombre_natujur
FROM transactions
WHERE valor_acto IS NOT NULL
ORDER BY valor_acto DESC
LIMIT 10;

-- Actividad por año
SELECT year_radica, COUNT(*) as total
FROM transactions
WHERE year_radica IS NOT NULL
GROUP BY year_radica
ORDER BY year_radica DESC;

-- Tipos de acto más comunes
SELECT nombre_natujur, COUNT(*) as total
FROM transactions
GROUP BY nombre_natujur
ORDER BY total DESC
LIMIT 10;

-- Propiedades con transacciones sospechosas
SELECT 
    matricula,
    COUNT(*) as total_transacciones,
    SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomalias,
    AVG(anomaly_score) as avg_score
FROM transactions
GROUP BY matricula
HAVING SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) > 0
ORDER BY anomalias DESC, avg_score DESC
LIMIT 20;
```

---

## 💡 Tips

1. **ETL en producción:** Usar `--batch-size 5000` para ser más conservador con memoria

2. **Re-entrenamiento:** Entrenar con sample primero, validar métricas, luego aplicar a toda la DB

3. **Backup antes de apply_models:** Los scores se sobrescriben

4. **Índices:** Crearlos con `CONCURRENTLY` para no bloquear la tabla

5. **Logs:** Revisar `logs/` regularmente, rotar archivos grandes

6. **Monitoreo:** Configurar alertas si tasa de anomalías sube repentinamente
