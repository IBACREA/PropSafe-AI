from datetime import datetime
from typing import Any
import re

from api.schemas import TransactionInput, TipoActo, TipoPredio, EstadoFolio
from core.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_transaction_data(transaction: TransactionInput) -> None:
    """
    Validate transaction data for business rules and data quality.
    
    Raises ValidationError if validation fails.
    """
    errors = []
    
    # Valor validation
    if transaction.valor_acto <= 0:
        errors.append("valor_acto must be positive")
    
    if transaction.valor_acto > 100_000_000_000:  # > 100B COP
        errors.append("valor_acto exceeds reasonable maximum")
    
    # Date validation
    if transaction.fecha_acto > datetime.now():
        errors.append("fecha_acto cannot be in the future")
    
    # Year range validation
    if transaction.fecha_acto.year < 1990:
        errors.append("fecha_acto too far in the past")
    
    # Intervinientes validation
    if transaction.numero_intervinientes < 1:
        errors.append("numero_intervinientes must be at least 1")
    
    if transaction.numero_intervinientes > 50:
        errors.append("numero_intervinientes exceeds reasonable maximum")
    
    # Area validation
    if transaction.area_terreno is not None:
        if transaction.area_terreno < 0:
            errors.append("area_terreno cannot be negative")
        if transaction.area_terreno > 1_000_000:  # > 1M m2
            errors.append("area_terreno exceeds reasonable maximum")
    
    if transaction.area_construida is not None:
        if transaction.area_construida < 0:
            errors.append("area_construida cannot be negative")
        if transaction.area_construida > transaction.area_terreno if transaction.area_terreno else False:
            errors.append("area_construida cannot exceed area_terreno")
    
    # Catastral number format (if provided)
    if transaction.numero_catastral:
        if not is_valid_catastral_number(transaction.numero_catastral):
            errors.append("numero_catastral format is invalid")
    
    # Matricula format (if provided)
    if transaction.matricula_inmobiliaria:
        if not is_valid_matricula(transaction.matricula_inmobiliaria):
            errors.append("matricula_inmobiliaria format is invalid")
    
    if errors:
        error_msg = "; ".join(errors)
        logger.warning("validation_failed", errors=error_msg)
        raise ValidationError(error_msg)
    
    logger.debug("validation_passed", municipio=transaction.municipio)


def is_valid_catastral_number(numero: str) -> bool:
    """
    Validate Colombian catastral number format.
    
    Format: 30 alphanumeric characters (may vary by municipality)
    """
    if not numero:
        return False
    
    # Basic validation: alphanumeric, length between 20-35
    pattern = r'^[A-Z0-9]{20,35}$'
    return bool(re.match(pattern, numero.upper()))


def is_valid_matricula(matricula: str) -> bool:
    """
    Validate Colombian matricula inmobiliaria format.
    
    Format: <codigo_oficina>-<numero>
    Example: 50C-1234567
    """
    if not matricula:
        return False
    
    # Pattern: alphanumeric code - numeric value
    pattern = r'^[A-Z0-9]+-\d+$'
    return bool(re.match(pattern, matricula.upper()))


def validate_departamento(departamento: str) -> bool:
    """Validate if departamento exists in Colombia."""
    # List of Colombian departments
    valid_departamentos = {
        "AMAZONAS", "ANTIOQUIA", "ARAUCA", "ATLANTICO", "BOLIVAR",
        "BOYACA", "CALDAS", "CAQUETA", "CASANARE", "CAUCA",
        "CESAR", "CHOCO", "CORDOBA", "CUNDINAMARCA", "GUAINIA",
        "GUAVIARE", "HUILA", "LA GUAJIRA", "MAGDALENA", "META",
        "NARIÑO", "NORTE DE SANTANDER", "PUTUMAYO", "QUINDIO", "RISARALDA",
        "SAN ANDRES", "SANTANDER", "SUCRE", "TOLIMA", "VALLE DEL CAUCA",
        "VAUPES", "VICHADA"
    }
    
    return departamento.upper() in valid_departamentos


def sanitize_text(text: str) -> str:
    """Sanitize text input by removing special characters and normalizing."""
    if not text:
        return ""
    
    # Remove special characters, keep alphanumeric and spaces
    sanitized = re.sub(r'[^A-Za-z0-9\s]', '', text)
    
    # Normalize whitespace
    sanitized = ' '.join(sanitized.split())
    
    return sanitized.upper()


def validate_file_format(filename: str, allowed_formats: list) -> bool:
    """Validate if file has an allowed format."""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1]
    return extension in [fmt.lower() for fmt in allowed_formats]
