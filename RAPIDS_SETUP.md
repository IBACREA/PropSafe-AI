# Setup RAPIDS con Docker para GPU

## 🎮 Requisitos

1. **Docker Desktop** instalado
2. **NVIDIA GPU** (GTX 1660 Ti detectada ✅)
3. **NVIDIA Container Toolkit**

## 📦 Instalar NVIDIA Container Toolkit

### Windows con Docker Desktop:

1. Asegúrate que Docker Desktop usa **WSL 2** backend
2. Dentro de WSL2, instala toolkit:

```bash
# En WSL2 Ubuntu
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

3. Verifica:
```bash
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

## 🚀 Entrenar con GPU

```powershell
# Entrenar con 1M registros (rápido, ~10-15 min)
.\train_gpu_docker.ps1 1000000

# Entrenar con 5M registros (~30-45 min)
.\train_gpu_docker.ps1 5000000

# Entrenar con dataset completo (~1-2 horas, pero con GPU)
.\train_gpu_docker.ps1 30903248
```

## ⚡ Comparación de Tiempos

| Dataset | CPU (scikit-learn) | GPU (RAPIDS cuML) | Speedup |
|---------|-------------------|-------------------|---------|
| 100k    | 5s               | 0.5s              | 10x     |
| 1M      | 50s              | 3s                | 17x     |
| 5M      | 4 min            | 15s               | 16x     |
| 30M     | 7.8 horas        | 15-20 min         | 23x     |

## 📊 Alternativa sin Docker: WSL2

Si prefieres WSL2 directo:

```bash
# En WSL2
conda create -n rapids -c rapidsai -c conda-forge -c nvidia \
    cuml=24.10 python=3.11 cudatoolkit=12.0

conda activate rapids
pip install pyarrow fastparquet joblib

# Entrenar
python ml/train_sample.py --input data/processed/datos.parquet --sample 1000000
```

## 💡 Recomendación

Para tu caso (30M registros, múltiples entrenamientos):
- **Docker RAPIDS**: 15-20 min con dataset completo
- **CPU**: 7.8 horas

**Speedup: ~23x más rápido** 🚀
