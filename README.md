# Real Estate Risk Platform

**Sistema de Monitoreo y Detección de Anomalías en Transacciones Inmobiliarias de Colombia**

Plataforma completa de Machine Learning para el análisis automatizado de 34+ millones de registros inmobiliarios, diseñada para identificar riesgos operativos, financieros, patrones de fraude y problemas de calidad de datos en tiempo real.

---

## 🎯 Contexto del Reto

Colombia concentra **más de 34 millones de registros** de transacciones inmobiliarias únicas entre 2015 y 2025, distribuidas en **1.105 municipios**. Esta información es crítica para:

- Planeación territorial
- Análisis de mercado inmobiliario
- Supervisión operativa y financiera
- Evaluación de riesgos
- Control de calidad de datos

### Problemática

El **volumen masivo**, la **heterogeneidad** y las **posibles inconsistencias** de los datos generan limitaciones para:

- ❌ Detectar errores o anomalías en tiempo real
- ❌ Identificar patrones de fraude sofisticados
- ❌ Controlar riesgos operativos y financieros
- ❌ Validar la calidad y completitud de los datos
- ❌ Aprovechar la integración con otras fuentes públicas

---

## 🎯 Objetivos

### Objetivo General

> **Diseñar e implementar un sistema automatizado de monitoreo, análisis y detección de anomalías** en la dinámica inmobiliaria del país, que permita identificar riesgos operativos, financieros, de fraude y problemas de calidad de datos en tiempo real o mediante procesos periódicos.

### Objetivos Específicos

- **OE1**: Integrar y estandarizar los registros de transacciones inmobiliarias
- **OE2**: Construir modelos de detección de anomalías basados en estadísticas, reglas y machine learning
- **OE3**: Identificar patrones de fraude, valores atípicos, duplicidades y errores de anotación
- **OE4**: Desarrollar un tablero de monitoreo con indicadores clave de riesgo y calidad
- **OE5**: Integrar fuentes públicas complementarias (IGAC, DNP, mercado inmobiliario)
- **OE6**: Documentar la metodología, procesos y arquitectura de datos

---

## 💡 Impacto Esperado

✅ **Mejor control operativo** sobre registros inmobiliarios nacionales  
✅ **Identificación temprana** de fraude y anomalías  
✅ **Reducción de errores administrativos** en anotaciones  
✅ **Mayor confianza** en la calidad de los datos  
✅ **Fortalecimiento** de la planeación territorial  
✅ **Ahorro de tiempo y recursos** en supervisión manual  
✅ **Capacidad analítica** nacional y municipal para entender la dinámica inmobiliaria  

---

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [ETL y Feature Engineering](#etl-y-feature-engineering)
- [Entrenamiento del Modelo](#entrenamiento-del-modelo)
- [Despliegue en AWS](#despliegue-en-aws)
- [Estado del Proyecto](#estado-del-proyecto)

## 🚀 Características

### 📊 ETL Pipeline (OE1)
- ✅ **Procesamiento masivo**: 30.9M registros SNR/IGAC
- ✅ **5.7M registros ML-ready** (18.5% después de filtros de calidad)
- ✅ **Business rules**: Validación por contexto según código de naturaleza jurídica
- ✅ **Composite keys**: Identificación única de transacciones
- ✅ **Detección de anomalías**: Actividad excesiva y discrepancias geográficas
- ✅ **Optimizado para RAM limitada**: Procesamiento in-place sin copias

### 🤖 Machine Learning (OE2)
- ✅ **Ensemble de modelos**: Isolation Forest + Local Outlier Factor
- ✅ **Feature engineering avanzado**: 39 features derivadas de datos transaccionales
- ✅ **Entrenado con 5.7M registros** reales de transacciones inmobiliarias
- ✅ **Detección multi-nivel**: Normal (<0.4), Sospechoso (0.4-0.7), Alto Riesgo (>0.7)
- ✅ **Pipeline reproducible**: Scripts automatizados para entrenamiento
- ✅ **Optimizado para CPU**: Compatible con instancias t3.small

### 🔍 Infraestructura y Deployment (OE6)
- ✅ **Terraform**: Scripts para aprovisionamiento de EC2 en AWS
- ✅ **Docker Compose**: Configuración para producción optimizada
- ✅ **PostgreSQL**: Schema completo y scripts de carga de datos
- ✅ **Deployment automatizado**: Scripts bash/PowerShell para despliegue
- ✅ **Documentación completa**: Guías de deployment y arquitectura

### 🌐 Backend API (FastAPI + Python)
- 🔄 **En desarrollo**: Estructura base implementada
- 🔄 Endpoints para análisis de transacciones
- 🔄 Integración con modelos ML
- 🔄 Documentación automática (Swagger/ReDoc)

### 🗺️ Frontend (React + Vite)
- 🔄 **En desarrollo**: Componentes base creados
- 🔄 Dashboard, Mapa, Analizador
- 🔄 Integración con API backend

### 📚 Servicios Adicionales
- 🔄 **RAG Service**: Estructura base para chat inteligente
- 🔄 **Vector Store**: ChromaDB para búsqueda semántica

## 🏗️ Arquitectura

```
real-estate-risk-platform/
├── backend/              # FastAPI application
│   ├── api/             # API routes (transactions, map, chat)
│   ├── core/            # Config, logging, dependencies
│   ├── models/          # ML model inference
│   ├── utils/           # Validators, data readers
│   └── main.py          # App entrypoint
│
├── frontend/            # React + Vite application
│   ├── src/
│   │   ├── components/  # Reusable React components
│   │   ├── pages/       # Route pages (Home, Map, Analyzer, Chat)
│   │   ├── services/    # API client
│   │   └── main.jsx     # App entrypoint
│   └── public/
│
├── ml/                  # Machine Learning pipeline
│   ├── feature_engineering.py  # Feature creation & transforms
│   ├── model_training.py       # Training script
│   └── models/                 # Trained model artifacts
│
├── services/            # Microservices
│   └── rag/            # RAG service (embeddings, vector store)
│       ├── embedder.py
│       ├── vector_store.py
│       └── rag.py
│
├── data/               # Data ingestion & processing
│   ├── ingest.py      # ETL pipeline
│   ├── raw/           # Raw data files
│   └── processed/     # Cleaned data
│
├── infra/             # Infrastructure as code
│   ├── docker-compose.yml
│   └── .env.template
│
├── Makefile           # Development commands
└── README.md          # This file
```

### Flujo de Datos

```
┌─────────────┐
│   Usuario   │
└──────┬──────┘
       │
       v
┌─────────────────────────────────────┐
│         Frontend (React)            │
│  ┌──────────┐  ┌──────────────┐    │
│  │   Map    │  │   Analyzer   │    │
│  └──────────┘  └──────────────┘    │
│  ┌──────────────────────────────┐  │
│  │         Chat (RAG)           │  │
│  └──────────────────────────────┘  │
└────────────┬────────────────────────┘
             │ HTTP/REST
             v
┌─────────────────────────────────────┐
│      Backend (FastAPI)              │
│  ┌────────────┐  ┌──────────────┐  │
│  │ Validation │  │  Anomaly     │  │
│  │            │→ │  Detection   │  │
│  └────────────┘  └──────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │    RAG Pipeline              │  │
│  │  Embedder → VectorStore →   │  │
│  │  LLM Generation              │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
             │
             v
┌─────────────────────────────────────┐
│   ML Models + Vector Store          │
│  - Isolation Forest                 │
│  - Local Outlier Factor             │
│  - ChromaDB                         │
└─────────────────────────────────────┘
```

## 📦 Requisitos Previos

- **Docker** 20.10+ y **Docker Compose** 2.0+
- **Python** 3.11+ (para desarrollo local)
- **Node.js** 20+ (para desarrollo frontend)
- **Git**
- **Token de Mapbox** (para visualización de mapas)
- **OpenAI API Key** (opcional, para chat mejorado)

## 🛠️ Instalación

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd real-estate-risk-platform
```

### 2. Configurar Variables de Entorno

```bash
cp .env.template .env
```

Edita `.env` con tus configuraciones:

```env
# Mapbox (requerido para frontend)
VITE_MAPBOX_TOKEN=tu_token_aqui

# OpenAI (opcional, mejora chat)
OPENAI_API_KEY=tu_api_key_aqui

# Otras configuraciones tienen defaults razonables
```

### 3. Opción A: Desarrollo con Docker (Recomendado)

```bash
# Construir e iniciar todos los servicios
make dev

# O manualmente:
docker-compose up --build
```

Servicios disponibles:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ChromaDB**: http://localhost:8001

### 3. Opción B: Desarrollo Local

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📖 ETL y Feature Engineering

### 1. Procesar Datos SNR/IGAC

```bash
# Procesar dataset completo (30.9M registros)
python etl/clean_and_transform.py

# O con número específico de registros
python etl/clean_and_transform.py 5000000
```

**Salidas generadas** (en `data/clean/`):
- `completo.parquet` - Todos los registros procesados
- `limpio.parquet` - Solo registros con calidad OK
- `ml_training.parquet` - Registros listos para ML (5.7M)
- `mercado.parquet` - Solo transacciones de mercado
- `errores.parquet` - Registros con problemas de calidad
- `advertencias.parquet` - Registros con advertencias

**Estadísticas generadas**:
- Por departamento y municipio
- Por calidad de datos
- Flags de anomalías

### 2. Generar Features para ML

```bash
python ml/feature_engineering_propsafe.py \
  --input data/clean/ml_training.parquet \
  --output data/clean/ml_features.parquet
```

**Features generadas (39 total)**:
- 6 features temporales (año, mes, trimestre, día de semana)
- 7 features de valor (log, millones, categorías)
- 8 features de áreas (aunque no disponibles en datos actuales)
- 3 features de actividad (anotaciones por año)
- 3 features geográficas (urbano/rural)
- 3 features de tipo de predio
- 4 features de flags de anomalía
- 2 features de naturaleza jurídica
- 3 features de counts

### 3. Entrenar Modelo ML

```bash
# Con dataset completo (5.7M registros)
python ml/train_propsafe.py \
  --features data/clean/ml_features.parquet \
  --contamination 0.15

# Con muestra para pruebas
python ml/train_propsafe.py \
  --features data/clean/ml_features.parquet \
  --sample 100000 \
  --contamination 0.15
```

**Modelos generados** (en `ml/models/`):
- `propsafe_anomaly_model.joblib` - Modelo completo (Isolation Forest + LOF)
- `training_predictions.parquet` - Predicciones en datos de entrenamiento

**Estadísticas esperadas**:
- ~45% Normal (score < 0.4)
- ~50% Sospechoso (score 0.4-0.7)  
- ~5% Alto Riesgo (score > 0.7)

## 🚀 Despliegue en AWS

### Docker Production (Local o EC2)

```bash
# Build para producción
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Detener
docker-compose -f docker-compose.prod.yml down
```

### Variables de Producción

```env
# .env.production
API_WORKERS=2
LOG_LEVEL=INFO
CORS_ORIGINS=["https://propsafeai.ibacrea.com"]

# Security
SECRET_KEY=<generar-key-segura>

# Database
DATABASE_URL=postgresql://propsafe_user:password@postgres:5432/propsafe_db

# Model path
MODEL_PATH=./ml/models/propsafe_anomaly_model.joblib
```

### Opción 1: Deployment Automatizado (Recomendado)

```powershell
# Desde el directorio del proyecto
cd infra
.\deploy-quick.ps1
```

Este script automatizado:
1. Genera clave SSH si no existe
2. Inicializa Terraform
3. Provisiona EC2 t3.small (~$20/mes)
4. Espera que la instancia esté lista
5. Sube código y datos
6. Despliega la aplicación con Docker
7. Carga datos en PostgreSQL

### Opción 2: Deployment Manual

Ver guía completa en: [`infra/DEPLOYMENT.md`](infra/DEPLOYMENT.md)

**Pasos resumidos:**

1. **Generar clave SSH**:
```powershell
ssh-keygen -t ed25519 -f ~/.ssh/propsafe_key
```

2. **Provisionar infraestructura**:
```powershell
cd infra/terraform
terraform init
terraform apply
```

3. **Subir archivos**:
```powershell
scp -i ~/.ssh/propsafe_key -r backend frontend ml scripts docker-compose.prod.yml ubuntu@SERVER_IP:/opt/propsafe/
```

4. **Desplegar en servidor**:
```bash
ssh -i ~/.ssh/propsafe_key ubuntu@SERVER_IP
cd /opt/propsafe
./infra/scripts/deploy.sh
```

5. **Configurar DNS**:
Apuntar `propsafeai.ibacrea.com` a la IP pública del EC2

### Configuración de Producción

**Recursos de EC2 t3.small**:
- 2 vCPU
- 2 GB RAM
- 30 GB SSD
- Costo: ~$15-20/mes

**Servicios Docker**:
- PostgreSQL (256MB shared_buffers)
- Backend API (800MB limit, 2 workers)
- Frontend Nginx (200MB limit)

**Límites recomendados para no exceder recursos**:
- Max 50 conexiones simultáneas a DB
- Chunk size 10,000 registros para inferencia
- 2 workers Gunicorn en backend

## 📊 Estado del Proyecto

### ✅ Completado

- [x] ETL Pipeline (30.9M → 5.7M registros procesados)
- [x] Feature Engineering (39 features)
- [x] Model Training (Isolation Forest + LOF)
- [x] Scripts de deployment (Terraform + Docker)
- [x] PostgreSQL schema y data loading
- [x] Documentación completa
- [x] Código en GitHub: https://github.com/IBACREA/PropSafe-AI

### 🔄 En Desarrollo

- [ ] Backend API funcional con endpoints
- [ ] Frontend React con dashboard
- [ ] Integración ML model → API → Frontend
- [ ] RAG Service para chat inteligente
- [ ] Tests automatizados

### 📋 Pendiente

- [ ] Deployment en AWS EC2
- [ ] Configuración DNS propsafeai.ibacrea.com
- [ ] HTTPS con Let's Encrypt
- [ ] CI/CD con GitHub Actions
- [ ] Monitoreo con CloudWatch
- [ ] Backups automatizados

## 🔮 Roadmap

```bash
# Build para producción
docker-compose -f docker-compose.yml build

# Deploy
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

### Variables de Producción

```env
# .env.production
API_WORKERS=4
LOG_LEVEL=INFO
CORS_ORIGINS=["https://tu-dominio.com"]

# Security
SECRET_KEY=<generar-key-segura>

# Database (opcional)
DATABASE_URL=postgresql://user:pass@host:5432/db
```

### Health Monitoring

```bash
# Backend health
curl http://localhost:8000/health

# ChromaDB health
curl http://localhost:8001/api/v1/heartbeat
```

## 🔮 Roadmap

### Próximas Implementaciones

**Fase 1: Integración Backend → Frontend** (En desarrollo)
- [ ] Conectar modelo entrenado con API FastAPI
- [ ] Implementar endpoints funcionales
- [ ] Crear dashboard React con visualizaciones
- [ ] Integrar mapa Mapbox con datos reales

**Fase 2: RAG Service** (Planeado)
- [ ] Implementar ChromaDB con datos reales
- [ ] Configurar OpenAI/embeddings
- [ ] Chat inteligente funcional

**Fase 3: Integraciones Externas** (Futuro)
- [ ] API de IGAC para validación catastral
- [ ] Comparación con precios de mercado
- [ ] Historial de folios de matrícula

**Fase 4: Producción** (Q1 2025)
- [ ] Deploy en AWS EC2
- [ ] Configuración HTTPS
- [ ] CI/CD con GitHub Actions
- [ ] Monitoreo y alertas

**Fase 5: Expansión** (2025)
- [ ] Dashboard de administración
- [ ] Alertas automáticas por email/SMS
- [ ] Mobile app (React Native)
- [ ] Predicción de precios con time series

### Cómo Extender el Proyecto

1. **Agregar un nuevo modelo ML**:
   ```python
   # ml/models/nuevo_modelo.py
   class NuevoDetector:
       def fit(self, X, y):
           # Entrenamiento
           pass
       
       def predict(self, X):
           # Predicción
           pass
   ```

2. **Nuevo endpoint en API**:
   ```python
   # backend/api/nuevo_servicio.py
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/api/nuevo")
   
   @router.get("/endpoint")
   async def nuevo_servicio():
       return {"status": "ok"}
   ```

3. **Nueva página en frontend**:
   ```jsx
   // frontend/src/pages/NuevaPagina.jsx
   export default function NuevaPagina() {
       return <div>Contenido nuevo</div>
   }
   ```

## 🧪 Testing

_(Tests automatizados aún no implementados)_

```bash
# Backend tests (cuando se implementen)
cd backend
pytest tests/ -v --cov=.

# Frontend tests (cuando se implementen)
cd frontend
npm test
```

## 📊 Monitoreo y Logs

### Structured Logging (Planeado)

Los logs serán JSON estructurado para fácil análisis:

```json
{
  "event": "transaction_analyzed",
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "score": 0.85,
  "classification": "high-risk",
  "processing_time_ms": 45.2
}
```

## 🤝 Contribuir

1. Fork el repositorio en https://github.com/IBACREA/PropSafe-AI
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y propietario de IBACREA. Todos los derechos reservados.

---

**PropSafe AI** - Plataforma de Detección de Fraude en Transacciones Inmobiliarias de Colombia 🏠🔍
