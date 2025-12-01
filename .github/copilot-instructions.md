# Real Estate Risk Platform - AI Coding Agent Instructions

## Project Overview

Production-ready platform for detecting fraud and anomalies in Colombian real estate transactions. Processes 34M+ records using ML ensemble (Isolation Forest + LOF) with FastAPI backend, React frontend, and RAG-powered chat.

## Architecture & Key Components

### Backend (`/backend`)

- **FastAPI** app with structured logging (structlog) and Pydantic validation
- **3 main routers**: `api/transactions.py`, `api/map.py`, `api/chat.py`
- **ML inference**: `models/anomaly_model.py` - loads joblib models, returns risk scores
- **Core utilities**: `core/config.py` (settings), `core/logger.py` (structured logs)
- **Data readers**: `utils/parquet_reader.py` - memory-efficient chunking for large files

**Key patterns**:

- All API routes return Pydantic schemas defined in `api/schemas.py`
- Use `get_logger(__name__)` for logging with context
- Settings via `get_settings()` cached singleton
- Transaction validation in `utils/validators.py` before ML processing

### Machine Learning (`/ml`)

- **Training pipeline**: `model_training.py` - trains ensemble, saves to `ml/models/`
- **Feature engineering**: `feature_engineering.py` - creates 34+ features from raw data
- **Ensemble scoring**: Weighted average of IF (0.4) + LOF (0.3) + Statistical (0.3)
- **Risk classification**: Normal (<0.4), Suspicious (0.4-0.7), High-risk (>0.7)

**When modifying ML**:

- Update `AnomalyDetector.prepare_features()` for new input fields
- Retrain models: `python ml/model_training.py --data <path>`
- Models are loaded lazily on first request (global singleton pattern)

### RAG Service (`/services/rag`)

- **embedder.py**: Sentence Transformers (multilingual Spanish support)
- **vector_store.py**: ChromaDB for semantic search
- **rag.py**: RAG pipeline - retrieval → context → LLM generation
- **Fallback**: Returns simple keyword-based response if no OpenAI key

**Integration**: RAG is called from `api/chat.py`, add documents via `index_document()`

### Frontend (`/frontend/src`)

- **React 18 + Vite** with Tailwind CSS
- **Pages**: `HomePage`, `MapPage` (Mapbox GL), `AnalyzerPage`, `ChatPage`
- **API client**: `services/api.js` - axios with interceptors
- **Reusable components**: `RiskBadge`, `LoadingSpinner`

**Mapbox integration**:

- Token required in `VITE_MAPBOX_TOKEN`
- GeoJSON from `/api/map/transactions` rendered as circles
- Circle size = transaction count, color = anomaly rate

### Data Pipeline (`/data`)

- **ingest.py**: ETL script with validation and chunking
- Processes CSV/Parquet → validates → cleans → outputs to `data/processed/`
- Run: `python data/ingest.py --input <file> --output data/processed/`

## Development Workflows

### Running the Stack

```bash
make dev              # Docker Compose (all services)
make dev-backend      # Backend only (local Python)
make dev-frontend     # Frontend only (local Node)
```

### Training & Data

```bash
make train            # Train ML models
make ingest           # Run data ingestion
```

### Testing & Quality

```bash
make test             # Run pytest suite
make lint             # Flake8 + pylint
make format           # Black + isort
```

## Code Conventions

### Backend Python

- **Type hints**: Required for public functions
- **Error handling**: Raise `HTTPException` with descriptive `detail`
- **Logging**: Use structured logger with context fields
  ```python
  logger.info("transaction_analyzed", score=0.85, municipio="BOGOTA")
  ```
- **Validation**: Pydantic models with custom validators
- **Async**: Use `async def` for I/O-bound operations

### Frontend React

- **Components**: Functional components with hooks
- **State**: `useState` for local, consider Context for global
- **API calls**: Always handle loading and error states
- **Styling**: Tailwind utility classes, avoid inline styles
- **Icons**: Use Heroicons (`@heroicons/react/24/outline`)

### ML Code

- **Reproducibility**: Set `random_state=42` for sklearn models
- **Memory**: Use generators/chunks for large datasets
- **Serialization**: joblib for models, JSON for metadata
- **Features**: Document new features in `feature_engineering.py`

## Critical Files to Understand

1. **`backend/main.py`**: App initialization, middleware, route registration
2. **`backend/models/anomaly_model.py`**: Core ML inference logic
3. **`ml/feature_engineering.py`**: Feature transformation pipeline
4. **`frontend/src/services/api.js`**: All API endpoint definitions
5. **`docker-compose.yml`**: Service orchestration

## Data Schemas

### Transaction Input (Colombian Real Estate)

Required fields matching SNR (Superintendencia de Notariado) structure:

- `valor_acto` (float): Transaction value in COP
- `tipo_acto` (enum): compraventa, hipoteca, donacion, permuta, etc.
- `fecha_acto` (datetime): Transaction date
- `departamento` (str): Colombian department (UPPERCASE)
- `municipio` (str): Municipality (UPPERCASE)
- `tipo_predio` (enum): urbano, rural, mixto
- `numero_intervinientes` (int): Number of parties involved
- `estado_folio` (enum): activo, cancelado, cerrado, suspendido

Optional: `area_terreno`, `area_construida`, `numero_catastral`, `matricula_inmobiliaria`

### Risk Analysis Output

```python
{
  "anomaly_score": 0.85,  # 0-1 scale
  "classification": "high-risk",  # normal|suspicious|high-risk
  "contributing_features": [  # Top 5 factors
    {
      "feature_name": "valor_acto",
      "value": 50000000,
      "contribution_score": 0.45,
      "explanation": "Valor significativamente inferior..."
    }
  ],
  "confidence": 0.92,
  "explanation": "...",  # Natural language summary
  "recommendations": ["Verificar avalúo catastral", ...]
}
```

## Integration Points

### Adding New Endpoints

1. Create router in `backend/api/`
2. Define Pydantic schemas in `api/schemas.py`
3. Register router in `main.py`: `app.include_router(new_router)`
4. Add API method in `frontend/src/services/api.js`

### Adding New Features

1. Add feature calculation in `ml/feature_engineering.py`
2. Retrain models: `make train`
3. Update `anomaly_model.py` if needed
4. Test with sample transaction

### Extending RAG

1. Index documents: `rag_pipeline.index_batch(docs, metadatas)`
2. Query via `/api/chat/query` endpoint
3. Customize prompt in `services/rag/rag.py`

## Environment Variables

Critical configs in `.env`:

- `VITE_MAPBOX_TOKEN`: Required for map visualization
- `OPENAI_API_KEY`: Optional, improves chat quality
- `MODEL_PATH`: Location of trained models (default: `./ml/models`)
- `VECTOR_STORE_PATH`: ChromaDB persistence (default: `./vector_store`)

## Common Tasks

### Debug ML Predictions

```python
# In backend/models/anomaly_model.py
logger.info("features", features=features.tolist())
logger.info("if_score", score=if_score)
```

### Update Transaction Schema

1. Modify `api/schemas.py` Pydantic model
2. Update `prepare_features()` in `anomaly_model.py`
3. Update frontend form in `pages/AnalyzerPage.jsx`

### Add Colombia Geography Data

Extend `api/map.py` functions:

- `get_colombia_municipalities()`: Add more municipalities
- `generate_mock_map_data()`: Real data from DB/API

## Performance Considerations

- **Batch processing**: Use chunk_size=50000 for files >1M rows
- **Model loading**: Lazy-loaded on first request (warmup ~2s)
- **Vector search**: ChromaDB indexed, queries <100ms
- **Frontend**: React.memo for expensive components

## Future Hooks (Placeholders)

Stubs in `main.py` for future integrations:

- `/api/cadastral/lookup`: IGAC cadastral data
- `/api/market/valuation`: Market price comparison
- `/api/folio/history`: Property transaction history

Enable via feature flags in `.env`:

```env
ENABLE_CADASTRAL_LOOKUP=true
ENABLE_MARKET_VALUATION=true
```

## Testing Strategy

- **Unit tests**: `backend/tests/` with pytest
- **API tests**: FastAPI TestClient
- **ML tests**: Validate model outputs with known samples
- **Frontend**: Vitest + React Testing Library (TODO)

## Deployment

Production-ready with:

- Health checks: `/health` endpoint
- Graceful shutdown: SIGTERM handling
- Log aggregation: JSON structured logs
- Container orchestration: Docker Compose
- Reverse proxy: Nginx (frontend container)

## When Things Go Wrong

- **Model not found**: Run `make train` first
- **ChromaDB errors**: Check `VECTOR_STORE_PATH` permissions
- **Frontend CORS**: Verify `CORS_ORIGINS` in `core/config.py`
- **Map not loading**: Validate `VITE_MAPBOX_TOKEN`
- **Memory issues**: Reduce `CHUNK_SIZE` in `.env`

## Key Dependencies

- **Backend**: fastapi, uvicorn, scikit-learn, pandas, chromadb
- **Frontend**: react, mapbox-gl, axios, tailwindcss
- **ML**: numpy, scipy, joblib, sentence-transformers
- **Infra**: docker, docker-compose, nginx

---

**Quick Start for AI Agents**: Read `README.md` for full setup, review `backend/main.py` for API structure, check `ml/model_training.py` for ML pipeline, explore `frontend/src/App.jsx` for UI routing.
