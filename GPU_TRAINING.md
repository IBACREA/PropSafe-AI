# GPU Training Setup

## 🎮 Para NVIDIA GPU

### Opción 1: XGBoost con GPU (Recomendado - más fácil)
```powershell
# Instalar XGBoost con soporte GPU
pip install xgboost

# Verificar que funciona
python -c "import xgboost as xgb; print('GPU Available:', 'gpu_hist' in xgb.XGBClassifier().get_params())"
```

### Opción 2: RAPIDS cuML (Más rápido pero más complejo)
```powershell
# Requiere conda y CUDA 11+
conda install -c rapidsai -c conda-forge -c nvidia cuml

# O con pip (CUDA 11.8)
pip install cuml-cu11
```

---

## ⚡ Entrenar con GPU

```powershell
# Con GPU (2-5 minutos para 100k registros)
python ml/train_gpu.py --input data/processed/snr_synthetic.parquet --output ml/models

# O con tu CSV de 8GB (5-10 minutos)
python ml/train_gpu.py --input "C:/ruta/tu-csv-8gb.csv" --output ml/models
```

---

## 📊 Comparación de Tiempos

| Dataset | CPU (scikit-learn) | GPU (XGBoost) | GPU (cuML) |
|---------|-------------------|---------------|------------|
| 100k registros | 3-5 min | 1-2 min | 30-60 seg |
| 1M registros | 15-25 min | 3-5 min | 2-3 min |
| 10M registros | 2-3 horas | 20-30 min | 10-15 min |

**Speedup:** 3-10x más rápido con GPU

---

## 🔧 Verificar GPU

```powershell
# Ver tu GPU
nvidia-smi

# Verificar CUDA
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Verificar XGBoost GPU
python -c "import xgboost as xgb; print('XGBoost GPU:', xgb.get_config())"
```

---

## 🚀 Pipeline Completo con GPU

```powershell
# 1. ETL (CPU - no hay GPU para pandas nativo)
python data/etl_pipeline.py --input "tu-csv-8gb.csv" --batch-size 10000
# Tiempo: 20-35 min

# 2. Train con GPU
python ml/train_gpu.py --input data/processed/snr_synthetic.parquet
# Tiempo: 2-5 min (vs 15-30 min en CPU)

# 3. Apply modelos (necesitas actualizar apply_models.py para GPU)
python ml/apply_models.py --batch-size 5000
# Tiempo: Similar (I/O bound)
```

---

## 💡 Tips

1. **XGBoost** es más fácil de instalar que cuML
2. **cuML** es más rápido pero requiere CUDA 11+
3. Si tienes **RTX 3060 o superior**, cuML vale la pena
4. Para **GTX 1660 o inferior**, XGBoost es suficiente
5. GPU acelera **entrenamiento**, no ETL (pandas es CPU)

---

## 🐛 Troubleshooting

### "No GPU detected"
```powershell
# Instalar drivers NVIDIA
# Descargar de: https://www.nvidia.com/download/index.aspx

# Instalar CUDA Toolkit 11.8
# Descargar de: https://developer.nvidia.com/cuda-downloads
```

### "cuML not found"
```powershell
# Usar solo XGBoost (más simple)
pip install xgboost

# O instalar cuML con conda
conda create -n rapids -c rapidsai -c conda-forge -c nvidia cuml python=3.10
```

### "Out of GPU memory"
```powershell
# Reducir tamaño de batch o sample
python ml/train_gpu.py --input data.csv --sample-size 500000
```

---

## ✅ Recomendación

Para tu caso (múltiples entrenamientos):

1. **Instala XGBoost GPU** (fácil, compatible)
   ```powershell
   pip install xgboost
   ```

2. **Entrena con GPU**
   ```powershell
   python ml/train_gpu.py --input tu-data.csv
   ```

3. **Itera rápido** (2-5 min por entrenamiento vs 15-30 min CPU)
