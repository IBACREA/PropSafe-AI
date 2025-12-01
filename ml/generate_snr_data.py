"""
Generador de datos sintéticos con estructura SNR
Genera transacciones usando las columnas oficiales de la SNR Colombia
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

# Municipios principales con DIVIPOLA
MUNICIPIOS = [
    ('BOGOTA', 'CUNDINAMARCA', '11001', 35),
    ('MEDELLIN', 'ANTIOQUIA', '05001', 20),
    ('CALI', 'VALLE DEL CAUCA', '76001', 15),
    ('BARRANQUILLA', 'ATLANTICO', '08001', 10),
    ('CARTAGENA', 'BOLIVAR', '13001', 8),
    ('CUCUTA', 'NORTE DE SANTANDER', '54001', 4),
    ('BUCARAMANGA', 'SANTANDER', '68001', 3),
    ('PEREIRA', 'RISARALDA', '66001', 2),
    ('MANIZALES', 'CALDAS', '17001', 2),
    ('IBAGUE', 'TOLIMA', '73001', 1),
]

# Actos jurídicos más comunes (Resolución 07448 de 2021)
ACTOS_JURIDICOS = [
    ('COMPRAVENTA', 80),
    ('HIPOTECA', 10),
    ('DONACION', 3),
    ('PERMUTA', 2),
    ('ADJUDICACION', 2),
    ('SUCESION', 1),
    ('REMATE', 1),
    ('CANCELACION DE HIPOTECA', 1),
]

TIPO_PREDIO = [
    ('URBANO', 70),
    ('RURAL', 25),
    ('SIN INFORMACION', 5),
]

ESTADO_FOLIO = [
    ('ACTIVO', 90),
    ('CERRADO', 7),
    ('CUSTODIA', 2),
    ('CANCELADO', 1),
]

CATEGORIAS_RURALIDAD = [
    'CIUDADES Y AGLOMERACIONES',
    'INTERMEDIO',
    'RURAL',
    'RURAL DISPERSO',
]

def generate_snr_transaction(idx, municipio, departamento, divipola, precio_base):
    """Genera una transacción con estructura SNR"""
    
    # PK único
    pk = f"TXN{idx:08d}"
    
    # Matrícula inmobiliaria (3 dígitos ORIP + número)
    orip = divipola[:3]
    matricula = f"{orip}{random.randint(100000, 999999)}"
    
    # Fechas
    fecha_rad = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
    fecha_apertura = fecha_rad - timedelta(days=random.randint(0, 365))
    
    # Tipo de predio
    tipo_predio = random.choices(
        [t[0] for t in TIPO_PREDIO],
        weights=[t[1] for t in TIPO_PREDIO]
    )[0]
    
    # Categoría ruralidad
    if tipo_predio == 'RURAL':
        categoria = random.choice(['RURAL', 'RURAL DISPERSO'])
    elif tipo_predio == 'URBANO':
        categoria = random.choice(['CIUDADES Y AGLOMERACIONES', 'INTERMEDIO'])
    else:
        categoria = 'CIUDADES Y AGLOMERACIONES'
    
    # Acto jurídico
    acto = random.choices(
        [a[0] for a in ACTOS_JURIDICOS],
        weights=[a[1] for a in ACTOS_JURIDICOS]
    )[0]
    
    # Estado folio
    estado = random.choices(
        [e[0] for e in ESTADO_FOLIO],
        weights=[e[1] for e in ESTADO_FOLIO]
    )[0]
    
    # Número de intervinientes
    count_a = random.randint(1, 3)  # Receptores
    count_de = random.randint(1, 4)  # Otorgantes
    
    # Predio nuevo (10%)
    predios_nuevos = 1 if random.random() < 0.1 else 0
    
    # Dinámica inmobiliaria (actos relevantes para mercado)
    dinamica = 1 if acto in ['COMPRAVENTA', 'HIPOTECA', 'PERMUTA', 'DONACION', 'REMATE'] else 0
    
    # Valor de la transacción
    tiene_valor = 1 if acto in ['COMPRAVENTA', 'PERMUTA', 'DONACION', 'REMATE', 'HIPOTECA'] else 0
    tiene_mas_de_un_valor = 1 if acto == 'PERMUTA' and random.random() < 0.5 else 0
    
    if tiene_valor:
        # Precio base con variación
        factor = random.uniform(0.5, 2.5)
        
        # Ajustes por tipo de predio
        if tipo_predio == 'RURAL':
            factor *= 0.6
        elif tipo_predio == 'URBANO':
            factor *= 1.2
        
        # Ajustes por tipo de acto
        if acto == 'DONACION':
            factor *= 0.7  # Suelen ser subvaloradas
        elif acto == 'REMATE':
            factor *= 0.6  # Precios más bajos
        elif acto == 'HIPOTECA':
            factor *= 1.1  # Tienden a ser avalúos conservadores
        
        valor = precio_base * factor
        
        # Redondear a miles
        valor = round(valor / 1000) * 1000
    else:
        valor = None
    
    return {
        'pk': pk,
        'matricula': matricula,
        'fecha_radicacion': fecha_rad.strftime('%Y-%m-%d'),
        'fecha_apertura': fecha_apertura.strftime('%Y-%m-%d'),
        'year_radica': fecha_rad.year,
        'orip': orip,
        'divipola': divipola,
        'departamento': departamento,
        'municipio': municipio,
        'tipo_predio': tipo_predio,
        'categoria_ruralidad': categoria,
        'num_anotacion': random.randint(1, 50),
        'estado_folio': estado,
        'folios_derivados': '[]',
        'dinamica_inmobiliaria': dinamica,
        'cod_natujur': random.randint(100, 999),
        'nombre_natujur': acto,
        'numero_catastral': f"{divipola}{random.randint(1000000000000000000, 9999999999999999999)}",
        'numero_catastral_antiguo': '',
        'documento_justificativo': f"ESC{random.randint(1000, 9999)}",
        'count_a': count_a,
        'count_de': count_de,
        'predios_nuevos': predios_nuevos,
        'tiene_valor': tiene_valor,
        'tiene_mas_de_un_valor': tiene_mas_de_un_valor,
        'valor_acto': valor,
    }

def generate_snr_dataset(n_samples=100000, output_file='data/processed/snr_synthetic.parquet'):
    """Genera dataset sintético con estructura SNR"""
    
    print(f"Generando {n_samples:,} transacciones sintéticas SNR...")
    
    transactions = []
    
    # Distribuir por municipios según pesos
    total_weight = sum(m[3] for m in MUNICIPIOS)
    
    for municipio, departamento, divipola, weight in MUNICIPIOS:
        n_mun = int((weight / total_weight) * n_samples)
        
        # Precio base según municipio
        if municipio == 'BOGOTA':
            precio_base = 200000000
        elif municipio == 'MEDELLIN':
            precio_base = 170000000
        elif municipio == 'CALI':
            precio_base = 150000000
        elif municipio == 'BARRANQUILLA':
            precio_base = 140000000
        elif municipio == 'CARTAGENA':
            precio_base = 180000000
        else:
            precio_base = 120000000
        
        for i in range(n_mun):
            idx = len(transactions)
            tx = generate_snr_transaction(idx, municipio, departamento, divipola, precio_base)
            transactions.append(tx)
    
    # Completar hasta n_samples
    while len(transactions) < n_samples:
        mun = random.choice(MUNICIPIOS)
        idx = len(transactions)
        precio_base = 150000000
        tx = generate_snr_transaction(idx, mun[0], mun[1], mun[2], precio_base)
        transactions.append(tx)
    
    df = pd.DataFrame(transactions)
    
    # Agregar anomalías intencionales (5%)
    n_anomalias = int(n_samples * 0.05)
    anomaly_idx = random.sample(range(len(df)), n_anomalias)
    
    for idx in anomaly_idx:
        if df.loc[idx, 'tiene_valor'] == 1:
            tipo_anomalia = random.choice(['precio_muy_bajo', 'precio_muy_alto', 'intervinientes_inusual'])
            
            if tipo_anomalia == 'precio_muy_bajo':
                df.loc[idx, 'valor_acto'] *= 0.2  # 80% menos
            elif tipo_anomalia == 'precio_muy_alto':
                df.loc[idx, 'valor_acto'] *= 3.5  # 250% más
            elif tipo_anomalia == 'intervinientes_inusual':
                df.loc[idx, 'count_a'] = random.randint(5, 10)
                df.loc[idx, 'count_de'] = random.randint(6, 12)
    
    # Guardar
    from pathlib import Path
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    
    print(f"\n✅ Dataset generado: {output_file}")
    print(f"   Tamaño: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   Registros: {len(df):,}")
    print(f"\n📊 Distribución por municipio:")
    for mun, count in df['municipio'].value_counts().head(10).items():
        print(f"   {mun}: {count:,} ({count/len(df)*100:.1f}%)")
    
    print(f"\n💰 Estadísticas de valor (registros con valor):")
    df_con_valor = df[df['tiene_valor'] == 1]
    print(f"   Registros con valor: {len(df_con_valor):,} ({len(df_con_valor)/len(df)*100:.1f}%)")
    print(f"   Precio promedio: ${df_con_valor['valor_acto'].mean():,.0f}")
    print(f"   Precio mediano: ${df_con_valor['valor_acto'].median():,.0f}")
    print(f"   Precio mín: ${df_con_valor['valor_acto'].min():,.0f}")
    print(f"   Precio máx: ${df_con_valor['valor_acto'].max():,.0f}")
    
    print(f"\n📝 Top 5 actos jurídicos:")
    for acto, count in df['nombre_natujur'].value_counts().head(5).items():
        print(f"   {acto}: {count:,} ({count/len(df)*100:.1f}%)")
    
    print(f"\n🏢 Distribución tipo predio:")
    for tipo, count in df['tipo_predio'].value_counts().items():
        print(f"   {tipo}: {count:,} ({count/len(df)*100:.1f}%)")
    
    return df

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=100000)
    parser.add_argument('--output', type=str, default='data/processed/snr_synthetic.parquet')
    args = parser.parse_args()
    
    generate_snr_dataset(args.samples, args.output)
