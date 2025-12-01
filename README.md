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
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Guía de Uso](#guía-de-uso)
- [API Endpoints](#api-endpoints)
- [Entrenamiento del Modelo](#entrenamiento-del-modelo)
- [Despliegue](#despliegue)
- [Expansión Futura](#expansión-futura)
- [Contribuir](#contribuir)

## 🚀 Características

### 📊 Dashboard de Monitoreo (OE4)
- ✅ **Indicadores clave de riesgo (KPIs)** en tiempo real
  - Total de transacciones procesadas (34M+)
  - Tasa de anomalías detectadas
  - Alertas de fraude activas
  - Score de calidad de datos
- ✅ **Alertas críticas recientes** con severidad y geolocalización
- ✅ **Distribución de anomalías** por tipo (valores atípicos, duplicidades, errores)
- ✅ **Top municipios de riesgo** con tendencias
- ✅ **Filtros temporales** (24h, 7d, 30d, 90d, 1y)

### 🤖 Machine Learning (OE2)
- ✅ **Ensemble de modelos**: Isolation Forest + Local Outlier Factor
- ✅ **Feature engineering avanzado**: 34+ features derivadas de datos transaccionales
- ✅ **Detección multi-nivel**: Normal (<0.4), Sospechoso (0.4-0.7), Alto Riesgo (>0.7)
- ✅ **Explicabilidad**: Features contribuyentes y recomendaciones de acción
- ✅ **Pipeline reproducible**: Entrenamiento automatizado con scikit-learn
- ✅ **Escalabilidad**: Procesamiento en chunks para 34M+ registros

### 🔍 Detección de Patrones de Fraude (OE3)
- ✅ **Valores atípicos**: Detección de precios anormalmente altos/bajos
- ✅ **Duplicidades sospechosas**: Identificación de matrículas inmobiliarias duplicadas
- ✅ **Errores de anotación**: Validación de campos obligatorios y formatos
- ✅ **Inconsistencias temporales**: Análisis de secuencias de transacciones
- ✅ **Análisis geoespacial**: Comparación con promedios municipales/departamentales

### 🌐 Backend (FastAPI + Python) (OE1)
- ✅ **Integración y estandarización** de registros inmobiliarios
- ✅ API REST con documentación automática (Swagger/ReDoc)
- ✅ Análisis individual y por lotes (CSV/Parquet)
- ✅ Endpoints geoespaciales para visualización
- ✅ Sistema de chat con RAG (Retrieval Augmented Generation)
- ✅ Logging estructurado con correlación de requests
- ✅ Validación robusta con Pydantic

### 🗺️ Frontend (React + Leaflet)
- ✅ **Mapa interactivo** con visualización de 10 ciudades principales
- ✅ **Dashboard completo** con KPIs y alertas
- ✅ **Analizador individual** con formulario de transacciones
- ✅ **Análisis por lotes** (carga de archivos CSV/Parquet)
- ✅ **Chat inteligente** con asistente IA
- ✅ **Diseño responsive** con TailwindCSS

### 📚 Servicios RAG
- ✅ Embeddings multilenguaje (español) con Sentence Transformers
- ✅ Vector store con ChromaDB para búsqueda semántica
- ✅ Pipeline RAG con OpenAI GPT para respuestas contextuales
- ✅ Fallback inteligente sin API key

### 🏗️ Infraestructura
- ✅ Docker Compose para desarrollo y producción
- ✅ Dockerfiles optimizados multi-stage
- ✅ Health checks y logging centralizado
- ✅ Variables de entorno con `.env.template`

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

## 📖 Guía de Uso

### 1. Entrenar el Modelo (Primera Vez)

```bash
# Generar datos sintéticos y entrenar
make train

# O con tus propios datos
python ml/model_training.py --data data/raw/transactions.csv --output ml/models
```

El entrenamiento genera:
- `ml/models/isolation_forest.joblib`
- `ml/models/lof.joblib`
- `ml/models/feature_engineer.joblib`
- `ml/models/training_metadata.json`

### 2. Ingestar Datos

```bash
# Procesar archivo de datos
make ingest

# O manualmente
python data/ingest.py --input data/raw/transactions.csv --output data/processed/
```

Formatos soportados:
- CSV (UTF-8)
- Parquet (Apache Arrow)

Columnas requeridas:
- `valor_acto`, `tipo_acto`, `fecha_acto`
- `departamento`, `municipio`, `tipo_predio`
- `numero_intervinientes`, `estado_folio`

### 3. Usar la Aplicación Web

#### a) Mapa Interactivo (`/map`)

- Visualiza transacciones por municipio
- Colores indican nivel de riesgo
- Click en puntos para ver detalles
- Heatmap de actividad transaccional

#### b) Analizador de Transacciones (`/analyzer`)

**Análisis Individual:**
1. Completa el formulario con datos de la transacción
2. Click en "Analizar Transacción"
3. Revisa el score de anomalía y recomendaciones

**Análisis por Lote:**
1. Carga archivo CSV o Parquet
2. El sistema procesa en chunks
3. Obtén estadísticas agregadas y lista de alto riesgo

#### c) Chat Inteligente (`/chat`)

- Haz preguntas en lenguaje natural
- "¿Cuál es el valor promedio en Bogotá?"
- "Muestra transacciones de alto riesgo"
- "¿Qué municipios tienen más anomalías?"

## 🔌 API Endpoints

### Transacciones

```http
POST /api/transactions/analyze-transaction
Content-Type: application/json

{
  "valor_acto": 250000000,
  "tipo_acto": "compraventa",
  "fecha_acto": "2024-01-15T10:30:00",
  "departamento": "CUNDINAMARCA",
  "municipio": "BOGOTA",
  "tipo_predio": "urbano",
  "numero_intervinientes": 2,
  "estado_folio": "activo"
}
```

**Respuesta:**
```json
{
  "result": {
    "anomaly_score": 0.15,
    "classification": "normal",
    "contributing_features": [...],
    "confidence": 0.92,
    "explanation": "Transacción normal...",
    "recommendations": [...]
  },
  "processing_time_ms": 45.2
}
```

### Análisis por Lote

```http
POST /api/transactions/batch-analyze
Content-Type: multipart/form-data

file: transactions.csv
analyze_all: true
```

### Mapa

```http
GET /api/map/transactions?departamento=CUNDINAMARCA&limit=1000
```

Retorna GeoJSON con:
- Coordenadas de municipios
- Estadísticas agregadas
- Métricas de riesgo

### Chat

```http
POST /api/chat/query
Content-Type: application/json

{
  "question": "¿Cuál es el valor promedio de transacciones en Bogotá?",
  "top_k": 5
}
```

### Health Check

```http
GET /health
```

## 🧠 Entrenamiento del Modelo

### Pipeline de Entrenamiento

1. **Feature Engineering**: Crea 34+ features desde datos raw
   - Temporales (año, mes, día de la semana)
   - Derivadas (valor/m², ratios, etc.)
   - Categóricas encodificadas
   - Indicadores de datos faltantes

2. **Model Training**: Ensemble de algoritmos
   - Isolation Forest (contamination=0.1)
   - Local Outlier Factor (n_neighbors=20)
   - Voting ensemble para clasificación final

3. **Evaluation**: Métricas en test set
   - Anomaly count por modelo
   - Feature importance
   - Confusion matrix

### Comandos de Entrenamiento

```bash
# Training con datos sintéticos (testing)
python ml/model_training.py

# Training con datos reales
python ml/model_training.py \
  --data data/processed/transactions.parquet \
  --output ml/models

# Ver metadata del entrenamiento
cat ml/models/training_metadata.json
```

### Hiperparámetros

Edita `ml/model_training.py`:

```python
isolation_forest = IsolationForest(
    contamination=0.1,      # % esperado de anomalías
    n_estimators=100,       # Número de árboles
    max_samples='auto',     # Samples por árbol
    random_state=42
)

lof = LocalOutlierFactor(
    n_neighbors=20,         # Vecinos para LOF
    contamination=0.1,
    novelty=True
)
```

### Interpretación de Scores

- **Score < 0.4**: Normal ✅
- **Score 0.4-0.7**: Sospechoso ⚠️
- **Score > 0.7**: Alto Riesgo 🚨

## 🚢 Despliegue

### Docker Production

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

## 🔮 Expansión Futura

### Hooks Implementados (Stubs)

El proyecto incluye placeholders para integraciones futuras:

#### 1. Lookup Catastral (`/api/cadastral/lookup`)

```python
# Integración futura con IGAC
# - Validar números catastrales
# - Obtener datos oficiales de predios
# - Verificar avalúos
```

#### 2. Valuación de Mercado (`/api/market/valuation`)

```python
# Comparación con mercado
# - Precios de referencia por zona
# - Análisis comparativo de valor
# - Índices de valorización
```

#### 3. Historial de Folio (`/api/folio/history`)

```python
# Trazabilidad completa
# - Chain of title
# - Transacciones previas
# - Cambios de propietario
```

### Roadmap

- [ ] **Q1 2025**: Integración con API de IGAC
- [ ] **Q2 2025**: Dashboard de administración
- [ ] **Q3 2025**: Alertas automáticas por email/SMS
- [ ] **Q4 2025**: Mobile app (React Native)
- [ ] **2026**: Predicción de precios con time series

### Cómo Extender

1. **Agregar un nuevo modelo ML**:
   ```python
   # ml/models/nuevo_modelo.py
   class NuevoDetector:
       def predict(self, features):
           # Tu lógica aquí
           pass
   ```

2. **Nuevo endpoint en API**:
   ```python
   # backend/api/nuevo_servicio.py
   @router.get("/nuevo-endpoint")
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

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=.

# Frontend tests (cuando se implementen)
cd frontend
npm test

# Integration tests
make test
```

## 📊 Monitoreo y Logs

### Structured Logging

Todos los logs son JSON estructurado:

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

### Ver Logs

```bash
# Docker logs
docker-compose logs -f backend

# Logs locales
tail -f logs/app.log
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y propietario. Todos los derechos reservados.

## 📞 Soporte

Para preguntas o soporte:
- 📧 Email: support@realestate-risk.com
- 📖 Docs: http://localhost:8000/docs
- 🐛 Issues: GitHub Issues

## 🙏 Agradecimientos

- Datos de prueba basados en estructura de SNR Colombia
- Stack tecnológico: FastAPI, React, Scikit-learn, ChromaDB, Mapbox
- Inspirado en mejores prácticas de MLOps y DevOps

---

**¡Gracias por usar Real Estate Risk Platform!** 🏠🔍
