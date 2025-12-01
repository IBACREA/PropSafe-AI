# Test rápido GPU con batch pequeño
Write-Host "🎮 Test GPU con RAPIDS cuML" -ForegroundColor Cyan

# Test 1: cuML disponible
Write-Host "`n[1/3] Verificando cuML..." -ForegroundColor Yellow
docker run --rm --gpus all rapids-train -c "import cuml; print('✅ cuML funciona')"

# Test 2: Leer datos
Write-Host "`n[2/3] Leyendo datos..." -ForegroundColor Yellow
docker run --rm --gpus all `
    -v "${PWD}/data/processed:/data:ro" `
    rapids-train -c "import pandas as pd; df = pd.read_parquet('/data/datos.parquet'); print(f'✅ {len(df):,} registros')"

# Test 3: Entrenar con 10k registros
Write-Host "`n[3/3] Entrenamiento GPU (10k registros)..." -ForegroundColor Yellow
docker run --rm --gpus all `
    -v "${PWD}/data/processed:/data:ro" `
    -v "${PWD}/ml/models:/models" `
    -v "${PWD}/ml/train_cuml.py:/app/train.py:ro" `
    rapids-train /app/train.py --input /data/datos.parquet --sample 10000 --output /models

Write-Host "`n✅ Test completado" -ForegroundColor Green
