# Arquitectura del Sistema - Real Estate Risk Platform

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REAL ESTATE RISK PLATFORM                           │
│                     Detección de Fraude con Machine Learning                │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│  1. DATA INGESTION (ETL PIPELINE)                                             │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  CSV 8GB+                                                                      │
│     │                                                                          │
│     ├─► [Extract]  ──┐                                                        │
│     │   • Read chunks (10k rows)                                             │
│     │   • Parse dates                                                        │
│     │   • Type conversion                                                    │
│     │                 │                                                      │
│     ├─► [Transform] ◄┘                                                        │
│     │   • Clean text (uppercase, trim)                                       │
│     │   • Validate values (no negatives, realistic ranges)                  │
│     │   • Validate dates (no future, no ancient)                            │
│     │   • Remove invalid rows                                               │
│     │                 │                                                      │
│     └─► [Load] ◄──────┘                                                        │
│         • Bulk insert to PostgreSQL                                          │
│         • Transaction batches                                                │
│         • Progress logging                                                   │
│                 │                                                            │
│                 ▼                                                            │
│         ┌─────────────────┐                                                   │
│         │   PostgreSQL    │                                                   │
│         │  transactions   │                                                   │
│         │   8M+ records   │                                                   │
│         └─────────────────┘                                                   │
│                                                                                │
│  Throughput: ~6,000 rows/sec                                                   │
│  Time for 8GB: ~20-30 minutes                                                  │
└───────────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────────┐
│  2. MACHINE LEARNING TRAINING                                                 │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  PostgreSQL                                                                    │
│      │                                                                         │
│      ├─► [Data Extraction] ──────┐                                            │
│      │   • SQL query                │                                         │
│      │   • Sample or full dataset   │                                         │
│      │                              │                                         │
│      └─► [Feature Engineering] ◄───┘                                          │
│          • 34 engineered features                                             │
│          • Normalization                                                      │
│          • Ratios & aggregations                                              │
│          • Temporal features                                                  │
│                      │                                                        │
│                      ├──────────────────────┐                                 │
│                      │                      │                                 │
│              [Isolation Forest]    [Local Outlier Factor]                     │
│              • 150 trees           • 25 neighbors                             │
│              • 60% weight          • 40% weight                               │
│              • Contamination: 10%  • Novelty detection                        │
│                      │                      │                                 │
│                      └──────┬───────────────┘                                 │
│                             │                                                 │
│                      [Ensemble Scoring]                                       │
│                      • Weighted average                                       │
│                      • Normalize 0-1                                          │
│                      • 3 risk levels                                          │
│                             │                                                 │
│                             ▼                                                 │
│                     ┌──────────────┐                                          │
│                     │ Trained Models│                                         │
│                     │  .joblib files│                                         │
│                     └──────────────┘                                          │
│                                                                                │
│  Output:                                                                       │
│  • isolation_forest.joblib                                                    │
│  • local_outlier_factor.joblib                                                │
│  • feature_engineer.joblib                                                    │
│  • training_summary.json                                                      │
│                                                                                │
│  Training time: 5-10 min (100k), 30-60 min (full)                             │
└───────────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────────┐
│  3. MODEL APPLICATION                                                         │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  PostgreSQL ─────────┐                                                         │
│   transactions       │                                                         │
│   (no scores yet)    │                                                         │
│                      │                                                         │
│  Trained Models ─────┤                                                         │
│   .joblib files      │                                                         │
│                      │                                                         │
│                      ▼                                                         │
│              [Batch Processing]                                                │
│              • Load 5k rows                                                    │
│              • Apply feature engineering                                       │
│              • Score with IF + LOF                                             │
│              • Calculate ensemble score                                        │
│              • Classify risk level                                             │
│              • Update database                                                 │
│              • Repeat                                                          │
│                      │                                                         │
│                      ▼                                                         │
│              ┌──────────────┐                                                  │
│              │  PostgreSQL  │                                                  │
│              │ transactions │                                                  │
│              │ + scores     │                                                  │
│              │ + is_anomaly │                                                  │
│              │ + risk_class │                                                  │
│              └──────────────┘                                                  │
│                                                                                │
│  Throughput: ~4,500 rows/sec                                                   │
│  Time for 8M: ~30-40 minutes                                                   │
└───────────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────────┐
│  4. API BACKEND (FastAPI)                                                     │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│                  ┌─────────────────────────┐                                  │
│                  │   FastAPI Application   │                                  │
│                  │   (main_simple.py)      │                                  │
│                  └──────────┬──────────────┘                                  │
│                             │                                                 │
│              ┌──────────────┼──────────────┐                                  │
│              │              │              │                                  │
│    ┌─────────▼─────┐ ┌─────▼──────┐ ┌────▼────────┐                          │
│    │  Property API  │ │ Valuation │ │  Chat API   │                          │
│    │  (property_db) │ │    API    │ │             │                          │
│    └────────┬───────┘ └─────┬──────┘ └────┬────────┘                          │
│             │               │             │                                   │
│             │               │             │                                   │
│    ┌────────▼───────────────▼─────────────▼──────┐                            │
│    │          PostgreSQL Database               │                            │
│    │  • transactions (8M+ records)              │                            │
│    │  • model_metadata                          │                            │
│    │  • Indexed & optimized                     │                            │
│    └────────────────────────────────────────────┘                            │
│                                                                                │
│  Endpoints:                                                                    │
│  • POST /api/property/search       - Buscar por matrícula                     │
│  • GET  /api/property/health       - Health check                             │
│  • GET  /api/property/stats        - Estadísticas globales                    │
│  • POST /api/valuation/predict     - Validar precio                           │
│  • POST /api/chat/query            - RAG chat                                 │
│                                                                                │
│  Features:                                                                     │
│  • SQLAlchemy ORM                                                              │
│  • Connection pooling                                                          │
│  • Structured logging                                                          │
│  • CORS enabled                                                                │
└───────────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────────┐
│  5. FRONTEND (React + Vite)                                                   │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│              ┌───────────────────────────────┐                                │
│              │    React Application          │                                │
│              │    (Vite + Tailwind CSS)      │                                │
│              └───────────┬───────────────────┘                                │
│                          │                                                    │
│          ┌───────────────┼───────────────┐                                    │
│          │               │               │                                    │
│   ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐                              │
│   │ Property    │ │ Valuation  │ │   Chat     │                              │
│   │ Search Page │ │    Page    │ │   Page     │                              │
│   └──────┬──────┘ └─────┬──────┘ └─────┬──────┘                              │
│          │               │               │                                    │
│          └───────────────┼───────────────┘                                    │
│                          │                                                    │
│                  ┌───────▼────────┐                                           │
│                  │   API Client   │                                           │
│                  │  (axios)       │                                           │
│                  └───────┬────────┘                                           │
│                          │                                                    │
│                          │ HTTP/JSON                                          │
│                          │                                                    │
│                          ▼                                                    │
│                  ┌───────────────┐                                            │
│                  │ Backend API   │                                            │
│                  │ localhost:8080│                                            │
│                  └───────────────┘                                            │
│                                                                                │
│  Pages:                                                                        │
│  • /property-search  - Búsqueda por matrícula + historial                     │
│  • /analyzer         - Validación de precios                                  │
│  • /chat             - Chat con RAG                                           │
│  • /map              - Mapa de transacciones                                  │
└───────────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────────┐
│  DATA FLOW - User Query Example                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  1. User enters matrícula in frontend                                          │
│            │                                                                   │
│            ▼                                                                   │
│  2. React calls api.searchProperty(matricula)                                  │
│            │                                                                   │
│            ▼                                                                   │
│  3. POST /api/property/search with {"matricula": "..."}                        │
│            │                                                                   │
│            ▼                                                                   │
│  4. FastAPI property_db.search_property()                                      │
│            │                                                                   │
│            ├─► Query PostgreSQL:                                               │
│            │   SELECT * FROM transactions                                      │
│            │   WHERE matricula = '...'                                         │
│            │   ORDER BY fecha_radicacion DESC                                  │
│            │                                                                   │
│            ├─► Process results:                                                │
│            │   • Count anomalies                                               │
│            │   • Calculate avg price                                           │
│            │   • Get last price                                                │
│            │   • Calculate anomaly rate                                        │
│            │   • Generate alerts                                               │
│            │                                                                   │
│            ▼                                                                   │
│  5. Return PropertySearchResponse with:                                        │
│     • historial: [list of transactions]                                       │
│     • anomaly_score: 0.XX                                                      │
│     • risk_classification: "high-risk"|"suspicious"|"normal"                  │
│     • alertas: [list of warnings]                                             │
│     • ubicacion, precios, etc.                                                │
│            │                                                                   │
│            ▼                                                                   │
│  6. React displays results:                                                    │
│     • Metrics cards                                                            │
│     • Risk badge (colored)                                                     │
│     • Transaction history table                                                │
│     • Alerts banner                                                            │
│                                                                                │
│  Total time: ~100-500ms                                                        │
└───────────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────────┐
│  TECHNOLOGY STACK                                                              │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  Data Layer:                                                                   │
│  • PostgreSQL 14+          - Main database                                     │
│  • SQLAlchemy 2.0         - ORM                                                │
│  • psycopg2               - PostgreSQL driver                                  │
│                                                                                │
│  Machine Learning:                                                             │
│  • scikit-learn           - ML algorithms (IF, LOF)                            │
│  • pandas                 - Data manipulation                                  │
│  • numpy                  - Numerical computing                                │
│  • joblib                 - Model serialization                                │
│                                                                                │
│  Backend:                                                                      │
│  • FastAPI 0.104+         - Web framework                                      │
│  • Uvicorn               - ASGI server                                         │
│  • Pydantic              - Data validation                                     │
│  • structlog             - Structured logging                                  │
│                                                                                │
│  Frontend:                                                                     │
│  • React 18              - UI framework                                        │
│  • Vite 5                - Build tool                                          │
│  • Tailwind CSS          - Styling                                             │
│  • Axios                 - HTTP client                                         │
│  • Heroicons             - Icons                                               │
│                                                                                │
│  Dev Tools:                                                                    │
│  • Python 3.10+          - Programming language                                │
│  • Node.js 18+           - JavaScript runtime                                  │
│  • PowerShell            - Automation scripts                                  │
└───────────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────────┐
│  PERFORMANCE METRICS                                                           │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ETL Pipeline:                                                                 │
│  • Throughput: 5,000-10,000 rows/sec                                           │
│  • 8GB CSV: ~20-30 minutes                                                     │
│  • Memory: <2GB RAM (chunked processing)                                       │
│                                                                                │
│  ML Training:                                                                  │
│  • 100k samples: ~5-10 minutes                                                 │
│  • 1M+ samples: ~30-60 minutes                                                 │
│  • Memory: 4-8GB RAM                                                           │
│                                                                                │
│  Model Application:                                                            │
│  • Throughput: ~4,500 rows/sec                                                 │
│  • 8M records: ~30-40 minutes                                                  │
│  • Memory: <2GB RAM                                                            │
│                                                                                │
│  API Response Times:                                                           │
│  • /property/search: 100-500ms                                                 │
│  • /property/health: <50ms                                                     │
│  • /property/stats: 50-200ms                                                   │
│                                                                                │
│  Database:                                                                     │
│  • Index seek: <10ms                                                           │
│  • Full table scan: N/A (optimized with indexes)                               │
│  • Connection pool: 10-20 connections                                          │
└───────────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────────┐
│  SCALABILITY & PRODUCTION CONSIDERATIONS                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  Current Capacity:                                                             │
│  • Handles 10M+ transactions                                                   │
│  • Sub-second query response                                                   │
│  • Concurrent users: 100+                                                      │
│                                                                                │
│  To Scale to 100M+ transactions:                                               │
│  1. Table partitioning (by year/department)                                    │
│  2. Read replicas for queries                                                  │
│  3. Redis cache for hot queries                                                │
│  4. Horizontal scaling (multiple API servers)                                  │
│  5. CDN for frontend                                                           │
│                                                                                │
│  Production Deployment:                                                        │
│  • Docker containers                                                           │
│  • Kubernetes orchestration                                                    │
│  • Load balancer (nginx/traefik)                                               │
│  • Monitoring (Prometheus/Grafana)                                             │
│  • Logging aggregation (ELK stack)                                             │
│  • Automated backups                                                           │
│  • CI/CD pipeline                                                              │
└───────────────────────────────────────────────────────────────────────────────┘
