# Script para entrenar con GPU en Docker RAPIDS

Write-Host "🚀 Entrenamiento con RAPIDS cuML (GPU)" -ForegroundColor Green
Write-Host "=" * 80

# Verificar Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker no está instalado" -ForegroundColor Red
    exit 1
}

# Verificar GPU NVIDIA
$gpu = docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ GPU NVIDIA no disponible en Docker" -ForegroundColor Red
    Write-Host "Instala NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    exit 1
}

Write-Host "✅ GPU detectada" -ForegroundColor Green

# Build imagen (skip si ya existe)
Write-Host "`n📦 Verificando imagen Docker..." -ForegroundColor Cyan
$imageExists = docker images rapids-train -q
if (!$imageExists) {
    Write-Host "Construyendo imagen (primera vez, ~10 min)..." -ForegroundColor Yellow
    docker build -t rapids-train -f Dockerfile.rapids .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error construyendo imagen" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Imagen ya existe" -ForegroundColor Green
}

# Ejecutar entrenamiento
Write-Host "`n🎮 Ejecutando entrenamiento con GPU..." -ForegroundColor Cyan
Write-Host "=" * 80

$sample = $args[0]
if (!$sample) { $sample = 100000 }

Write-Host "Muestra: $sample registros" -ForegroundColor Yellow

docker run --rm --gpus all `
    -v "${PWD}/data/processed:/data" `
    -v "${PWD}/ml:/workspace" `
    -v "${PWD}/ml/models:/models" `
    rapids-train `
    /workspace/train_cuml.py --input /data/datos.parquet --sample $sample --output /models

Write-Host "`n✅ Entrenamiento completado" -ForegroundColor Green
Write-Host "Modelos guardados en: ml/models/"
