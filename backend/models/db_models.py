"""
Database models for real estate transactions
"""
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime, Text, Index
from sqlalchemy.sql import func
from backend.core.database import Base


class Transaction(Base):
    """Real estate transaction record"""
    __tablename__ = "transactions"

    # Primary key
    pk = Column(Integer, primary_key=True, index=True, comment="Primary key")
    
    # Property identifiers
    matricula = Column(String(50), nullable=False, index=True, comment="Matrícula inmobiliaria")
    numero_catastral = Column(String(100), nullable=True, comment="Número catastral")
    matricula_inmobiliaria = Column(String(50), nullable=True, comment="Matrícula inmobiliaria alternativa")
    
    # Transaction details
    fecha_radicacion = Column(Date, nullable=True, index=True, comment="Fecha de radicación")
    fecha_apertura = Column(Date, nullable=True, comment="Fecha de apertura")
    year_radica = Column(Integer, nullable=True, index=True, comment="Año de radicación")
    
    # Location
    orip = Column(String(10), nullable=True, comment="Código ORIP")
    divipola = Column(String(10), nullable=True, comment="Código DIVIPOLA")
    departamento = Column(String(100), nullable=True, index=True, comment="Departamento")
    municipio = Column(String(100), nullable=True, index=True, comment="Municipio")
    
    # Property details
    tipo_predio = Column(String(50), nullable=True, comment="Tipo de predio (urbano/rural)")
    area_terreno = Column(Float, nullable=True, comment="Área del terreno en m²")
    area_construida = Column(Float, nullable=True, comment="Área construida en m²")
    
    # Transaction type and value
    nombre_natujur = Column(String(100), nullable=True, index=True, comment="Tipo de acto jurídico")
    valor_acto = Column(Float, nullable=True, comment="Valor del acto en COP")
    tiene_valor = Column(Boolean, default=False, comment="Si tiene valor reportado")
    
    # Parties involved
    count_a = Column(Integer, default=0, comment="Número de compradores/beneficiarios")
    count_de = Column(Integer, default=0, comment="Número de vendedores/otorgantes")
    
    # Folio status
    estado_folio = Column(String(50), nullable=True, comment="Estado del folio (activo/cancelado)")
    
    # ML Predictions (populated after training)
    anomaly_score = Column(Float, nullable=True, index=True, comment="Score de anomalía (0-1)")
    is_anomaly = Column(Boolean, default=False, index=True, comment="Si es detectado como anomalía")
    risk_classification = Column(String(20), nullable=True, comment="normal/suspicious/high-risk")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Timestamp de creación")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Timestamp de actualización")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_matricula_fecha', 'matricula', 'fecha_radicacion'),
        Index('idx_location', 'departamento', 'municipio'),
        Index('idx_anomaly', 'is_anomaly', 'anomaly_score'),
        Index('idx_valor_tipo', 'valor_acto', 'nombre_natujur'),
    )


class ModelMetadata(Base):
    """Metadata about trained ML models"""
    __tablename__ = "model_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, comment="Nombre del modelo")
    model_version = Column(String(50), nullable=False, comment="Versión del modelo")
    model_type = Column(String(50), nullable=False, comment="Tipo (isolation_forest/lof/statistical)")
    
    # Training metadata
    trained_at = Column(DateTime(timezone=True), server_default=func.now())
    training_samples = Column(Integer, comment="Número de samples de entrenamiento")
    features_used = Column(Text, comment="Features usados (JSON)")
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Model path
    model_path = Column(String(500), comment="Path al archivo del modelo")
    is_active = Column(Boolean, default=True, comment="Si es el modelo activo")
    
    __table_args__ = (
        Index('idx_model_active', 'model_name', 'is_active'),
    )
