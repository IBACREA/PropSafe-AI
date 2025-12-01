#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick start script for Real Estate Risk Platform

.DESCRIPTION
    Guía interactiva para configurar y ejecutar la plataforma completa

.EXAMPLE
    .\quickstart.ps1
#>

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "  REAL ESTATE RISK PLATFORM - QUICK START" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/6] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python no encontrado. Por favor instala Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check PostgreSQL
Write-Host "`n[2/6] Verificando PostgreSQL..." -ForegroundColor Yellow
try {
    $pgVersion = & psql --version 2>&1
    Write-Host "  ✓ $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ PostgreSQL no encontrado." -ForegroundColor Red
    Write-Host "    Instalar desde: https://www.postgresql.org/download/" -ForegroundColor Yellow
    $continue = Read-Host "    ¿Continuar sin PostgreSQL? (y/N)"
    if ($continue -ne "y") { exit 1 }
}

# Check .env
Write-Host "`n[3/6] Verificando configuración..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ✓ Archivo .env existe" -ForegroundColor Green
} else {
    Write-Host "  ! Archivo .env no encontrado" -ForegroundColor Yellow
    $create = Read-Host "    ¿Crear .env desde .env.example? (Y/n)"
    if ($create -ne "n") {
        Copy-Item ".env.example" ".env"
        Write-Host "  ✓ .env creado. Por favor edita DATABASE_URL antes de continuar." -ForegroundColor Green
        Write-Host "    Abre .env y configura tu contraseña de PostgreSQL" -ForegroundColor Yellow
        Read-Host "    Presiona ENTER cuando esté listo"
    }
}

# Install dependencies
Write-Host "`n[4/6] Instalando dependencias Python..." -ForegroundColor Yellow
Write-Host "  (Esto puede tomar varios minutos...)" -ForegroundColor Gray
& python -m pip install --quiet --upgrade pip
& python -m pip install --quiet -r requirements.txt
Write-Host "  ✓ Dependencias instaladas" -ForegroundColor Green

# Menu principal
Write-Host "`n" -NoNewline
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "  ¿QUÉ DESEAS HACER?" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""
Write-Host "  [1] Setup inicial - Crear base de datos y tablas" -ForegroundColor White
Write-Host "  [2] ETL - Procesar CSV y cargar a PostgreSQL" -ForegroundColor White
Write-Host "  [3] ML - Entrenar modelos de IA" -ForegroundColor White
Write-Host "  [4] ML - Aplicar modelos a toda la base de datos" -ForegroundColor White
Write-Host "  [5] Backend - Iniciar servidor API" -ForegroundColor White
Write-Host "  [6] Frontend - Iniciar interfaz web" -ForegroundColor White
Write-Host "  [7] All - Ejecutar todo (setup + backend + frontend)" -ForegroundColor White
Write-Host "  [0] Salir" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Selecciona una opción"

switch ($choice) {
    "1" {
        Write-Host "`n🔧 Ejecutando setup de base de datos..." -ForegroundColor Yellow
        & python scripts/setup_database.py
    }
    
    "2" {
        Write-Host "`n📊 Pipeline ETL" -ForegroundColor Yellow
        $csvPath = Read-Host "Ruta al archivo CSV (ej: C:/datos/transactions.csv)"
        $batchSize = Read-Host "Batch size [10000]"
        if ([string]::IsNullOrWhiteSpace($batchSize)) { $batchSize = "10000" }
        
        Write-Host "  Procesando $csvPath..." -ForegroundColor Gray
        & python data/etl_pipeline.py --input $csvPath --batch-size $batchSize
    }
    
    "3" {
        Write-Host "`n🧠 Entrenamiento de modelos ML" -ForegroundColor Yellow
        $sampleSize = Read-Host "Sample size (deja vacío para todos los datos)"
        
        if ([string]::IsNullOrWhiteSpace($sampleSize)) {
            & python ml/train_from_db.py --output ml/models
        } else {
            & python ml/train_from_db.py --sample-size $sampleSize --output ml/models
        }
    }
    
    "4" {
        Write-Host "`n🎯 Aplicando modelos a base de datos..." -ForegroundColor Yellow
        $batchSize = Read-Host "Batch size [5000]"
        if ([string]::IsNullOrWhiteSpace($batchSize)) { $batchSize = "5000" }
        
        & python ml/apply_models.py --batch-size $batchSize
    }
    
    "5" {
        Write-Host "`n🚀 Iniciando backend..." -ForegroundColor Yellow
        Write-Host "  URL: http://localhost:8080" -ForegroundColor Cyan
        Write-Host "  Docs: http://localhost:8080/docs" -ForegroundColor Cyan
        Write-Host "  Presiona Ctrl+C para detener" -ForegroundColor Gray
        Write-Host ""
        
        Set-Location backend
        & python -m uvicorn main_simple:app --reload --port 8080
    }
    
    "6" {
        Write-Host "`n🎨 Iniciando frontend..." -ForegroundColor Yellow
        Write-Host "  URL: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "  Presiona Ctrl+C para detener" -ForegroundColor Gray
        Write-Host ""
        
        Set-Location frontend
        npm run dev
    }
    
    "7" {
        Write-Host "`n🚀 Iniciando stack completo..." -ForegroundColor Yellow
        
        # Setup database si no existe
        Write-Host "  [1/3] Setup database..." -ForegroundColor Gray
        & python scripts/setup_database.py
        
        # Start backend
        Write-Host "`n  [2/3] Iniciando backend en segundo plano..." -ForegroundColor Gray
        Set-Location backend
        Start-Process python -ArgumentList "-m", "uvicorn", "main_simple:app", "--port", "8080" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        
        # Start frontend
        Write-Host "  [3/3] Iniciando frontend..." -ForegroundColor Gray
        Set-Location ../frontend
        
        Write-Host "`n✓ Stack iniciado!" -ForegroundColor Green
        Write-Host "  Backend: http://localhost:8080" -ForegroundColor Cyan
        Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "`n  Presiona Ctrl+C para detener frontend" -ForegroundColor Gray
        Write-Host "  (Backend seguirá corriendo en segundo plano)" -ForegroundColor Gray
        Write-Host ""
        
        npm run dev
    }
    
    "0" {
        Write-Host "`nSaliendo..." -ForegroundColor Gray
        exit 0
    }
    
    default {
        Write-Host "`n✗ Opción inválida" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "  ¡Completado!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan
