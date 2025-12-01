# ETL Actualizado - Reglas de Negocio Transaccionales

## Resumen de Cambios Implementados

### 1. **Composite Transaction Key** ✅
- **Implementado**: `transaction_id` = DIVIPOLA + MATRICULA + NUM_ANOTACION + COD_NATUJUR + AÑO
- **Propósito**: Identificador único a nivel transacción (no predio)
- **Ubicación**: Método `crear_composite_key()`

### 2. **Clasificación Contextual de Calidad** ✅
- **Antes**: Descartaba todos los registros con VALOR=0 o NULL
- **Ahora**: Análisis contextual según `codigo_naturaleza_juridica`
  
  **Reglas implementadas**:
  - ❌ **ERROR**: Actos de mercado (Dinámica=1) SIN valor → Anomalía de Calidad
  - ✅ **OK**: Actos administrativos (Dinámica=0) con valor=0 → CORRECTO
  - ⚠️ **ADVERTENCIA**: Compraventas con valores irrisorios (<1M COP)
  - ❌ **ERROR**: Valores extremos (>10B COP) → Error de digitación

### 3. **Preservación de Categorías Válidas** ✅
- **TIPO_PREDIO_ZONA**: Ahora incluye `'SIN INFORMACION'` (antes "Indeterminado")
- **Razón**: Es una categoría VÁLIDA (fallo de georreferenciación), no un error
- **Tratamiento**: Se mantiene en dataset para análisis

### 4. **Detección de Anomalías de Negocio** ✅

#### 4.1 Actividad Excesiva
- **Métrica**: Contar anotaciones por matrícula por año
- **Umbral**: >150 anotaciones/año = Flag de fraude potencial
- **Output**: Columna `flag_actividad_excesiva`

#### 4.2 Discrepancia Geográfica
- **Lógica**: 
  1. Crear mapeo ORIP → Departamento esperado (el más frecuente)
  2. Comparar con DEPARTAMENTO real del DIVIPOLA
  3. Flag si NO coinciden (jurisdicción cruzada posible pero sospechosa)
- **Output**: Columna `flag_geo_discrepancia`

### 5. **Flujo ETL Actualizado** ✅

```
1. Cargar datos (batches 500k registros)
2. Crear composite key ← NUEVO
3. Validar y tipar (26 columnas)
4. Clasificar calidad (contextual) ← ACTUALIZADO
5. Detectar anomalías negocio ← NUEVO
6. Crear 6 datasets especializados
7. Generar estadísticas agregadas
8. Guardar resultados
```

## Resultados con 100k Muestra

| Métrica | Valor | % |
|---------|-------|---|
| Registros entrada | 100,000 | 100% |
| Registros OK | 56,098 | 56.1% |
| Registros ADVERTENCIA | 204 | 0.2% |
| Registros ERROR | 43,698 | 43.7% |
| **ML Training** | **11,355** | **11.4%** |
| Actividad excesiva | 0 | 0.0% |
| Discrepancia geo | 0 | 0.0% |

## Datasets Generados

1. **completo.parquet**: Todos los registros con tipos correctos + composite key
2. **limpio.parquet**: Solo calidad=OK (56k)
3. **mercado.parquet**: Dinámica=1, sin errores (11.6k)
4. **ml_training.parquet**: Listo para ML (11.4k) ← Dataset final
5. **errores.parquet**: Para revisión manual (43.7k)
6. **advertencias.parquet**: Valores irrisorios para review (204)

## Columnas Adicionales Creadas

- `transaction_id`: Composite key único
- `calidad_datos`: OK | ADVERTENCIA | ERROR
- `tipo_error`: Categoría del problema
- `es_mercado_valido`: Boolean (Dinámica=1)
- `valor_valido`: Boolean (1M-10B COP)
- `flag_actividad_excesiva`: Boolean (>150 anotaciones/año)
- `flag_geo_discrepancia`: Boolean (ORIP vs DIVIPOLA mismatch)
- `anotaciones_por_anio`: Contador
- `depto_esperado_orip`: Departamento esperado según ORIP
- `total_flags_anomalia`: Suma de flags

## Próximos Pasos

### Inmediato (En Progreso)
- ✅ ETL completo corriendo (30.9M registros, ~40 min estimado)

### Siguientes
1. **Actualizar export_to_database.py**:
   - Agregar columna `transaction_id` a schema
   - Agregar columnas de flags de anomalías
   - Crear vistas SQL con reglas de negocio

2. **Reescribir Feature Engineering** (ml/train_hybrid_gpu.py):
   - Features nivel transacción (no predio)
   - Incluir `codigo_naturaleza_juridica` (codificado)
   - Segmentar outliers por divipola + tipo_zona
   - Usar composite key para joins
   - 25-30 features bien diseñadas

3. **Implementar Reglas Estadísticas SQL**:
   - Compraventas sin valor
   - Actividad excesiva por matrícula
   - Outliers segmentados por región
   - Discrepancias geográficas severas

## Diferencias Clave vs Versión Anterior

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Unidad análisis | Predio (implícito) | **Transacción** |
| Identificador | PK solo | **Composite key** |
| Valores nulos | Descarta todos | **Contextual** (según acto) |
| Ceros en valor | Advertencia | **OK si admin, ERROR si mercado** |
| Tipo "Indeterminado" | Descartaba | **Preserva** (válido) |
| Anomalías | Solo valores | **+ Actividad + Geo** |
| Filtrado | Universal | **Según naturaleza jurídica** |

## Validación Exitosa ✅

- ✅ Composite keys creadas: 100,000 únicas
- ✅ Clasificación contextual funciona
- ✅ Detección geo corregida (0% en muestra Antioquia = correcto)
- ✅ Detección actividad lista (0 en muestra = correcto)
- ✅ Preserva "SIN INFORMACION" como categoría
- ✅ ETL completo (30.9M) en ejecución

## Impacto en Downstream

### ML Feature Engineering
- Ahora debe usar `transaction_id` como índice
- Debe incluir features de `codigo_naturaleza_juridica`
- Outliers deben segmentarse por `DEPARTAMENTO + TIPO_PREDIO_ZONA`
- No usar `numero_catastral` como key (alta tasa nulls)

### SQL Database
- Schema debe incluir composite key
- Views deben usar reglas contextuales
- Dashboard debe mostrar flags de anomalías
- Manual review queue debe priorizar por flags

### Análisis
- Interpretar zeros/nulls según tipo de acto
- Discrepancia geo es posible (jurisdicción), no siempre error
- Actividad excesiva es señal fuerte de fraude
- Tipo "Indeterminado" es categoría válida para análisis

---

**Timestamp**: 2025-11-28 16:25
**Status**: ETL completo ejecutándose (batch 43/~62)
**ETA**: ~20-25 minutos restantes
