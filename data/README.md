# Data directories

## Structure:
- raw/ - Original unprocessed data files
- processed/ - Cleaned and validated data ready for ML
- exports/ - Generated reports and exports

## Data Sources:
Colombian real estate transaction data from Superintendencia de Notariado y Registro (SNR)

## Expected Columns:
- valor_acto: Transaction value (COP)
- tipo_acto: Transaction type
- fecha_acto: Transaction date
- departamento: Colombian department
- municipio: Municipality
- tipo_predio: Property type (urban/rural/mixed)
- numero_intervinientes: Number of parties involved
- estado_folio: Registration folio status
- numero_catastral: Cadastral number (optional)
- matricula_inmobiliaria: Property registration number (optional)
- area_terreno: Land area in m2 (optional)
- area_construida: Built area in m2 (optional)

## Processing:
Run: make ingest OR python data/ingest.py --input <file> --output data/processed/
