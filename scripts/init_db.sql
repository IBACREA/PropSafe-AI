-- PropSafe AI Database Schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Geographic info
    divipola VARCHAR(10),
    departamento VARCHAR(100),
    municipio VARCHAR(100),
    codigo_orip VARCHAR(10),
    
    -- Property info
    numero_matricula VARCHAR(50),
    numero_predial VARCHAR(50),
    tipo_predio VARCHAR(20),
    area_terreno NUMERIC(15,2),
    area_construida NUMERIC(15,2),
    
    -- Transaction info
    numero_anotacion VARCHAR(50),
    codigo_naturaleza_juridica VARCHAR(10),
    descripcion_naturaleza_juridica TEXT,
    dinamica_mercado INTEGER,
    tipo_acto VARCHAR(100),
    fecha_acto DATE,
    year_radica INTEGER,
    valor_acto NUMERIC(18,2),
    
    -- Parties
    numero_intervinientes INTEGER,
    
    -- Geography
    tipo_zona VARCHAR(50),
    latitud NUMERIC(10,6),
    longitud NUMERIC(10,6),
    
    -- Quality flags
    calidad_datos VARCHAR(20),
    tiene_valor_nulo BOOLEAN,
    tiene_area_cero BOOLEAN,
    
    -- Anomaly flags
    flag_actividad_excesiva BOOLEAN,
    anotaciones_por_anio INTEGER,
    flag_discrepancia_geografica BOOLEAN,
    
    -- ML results (to be populated after inference)
    anomaly_score NUMERIC(5,4),
    risk_classification VARCHAR(20),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_transactions_divipola ON transactions(divipola);
CREATE INDEX idx_transactions_municipio ON transactions(municipio);
CREATE INDEX idx_transactions_matricula ON transactions(numero_matricula);
CREATE INDEX idx_transactions_fecha ON transactions(fecha_acto);
CREATE INDEX idx_transactions_year ON transactions(year_radica);
CREATE INDEX idx_transactions_tipo_acto ON transactions(tipo_acto);
CREATE INDEX idx_transactions_calidad ON transactions(calidad_datos);
CREATE INDEX idx_transactions_anomaly_score ON transactions(anomaly_score);
CREATE INDEX idx_transactions_risk ON transactions(risk_classification);
CREATE INDEX idx_transactions_composite ON transactions(divipola, numero_matricula, year_radica);

-- Full text search index
CREATE INDEX idx_transactions_search ON transactions USING gin(to_tsvector('spanish', 
    COALESCE(municipio, '') || ' ' || 
    COALESCE(tipo_acto, '') || ' ' ||
    COALESCE(descripcion_naturaleza_juridica, '')
));

-- Statistics table for dashboard
CREATE TABLE IF NOT EXISTS statistics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(18,2),
    metric_date DATE DEFAULT CURRENT_DATE,
    departamento VARCHAR(100),
    municipio VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_statistics_metric ON statistics(metric_name, metric_date);
CREATE INDEX idx_statistics_location ON statistics(departamento, municipio);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(255) REFERENCES transactions(transaction_id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_created ON alerts(created_at);

-- Users table (for future authentication)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'analyst',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);

-- Views for common queries
CREATE OR REPLACE VIEW vw_high_risk_transactions AS
SELECT 
    t.*,
    s.metric_value as municipal_avg_value
FROM transactions t
LEFT JOIN statistics s ON s.municipio = t.municipio 
    AND s.metric_name = 'avg_transaction_value'
    AND s.metric_date = CURRENT_DATE
WHERE t.anomaly_score > 0.7
    OR t.flag_actividad_excesiva = true
    OR t.flag_discrepancia_geografica = true
ORDER BY t.anomaly_score DESC NULLS LAST;

CREATE OR REPLACE VIEW vw_dashboard_stats AS
SELECT 
    COUNT(*) as total_transactions,
    COUNT(CASE WHEN calidad_datos = 'OK' THEN 1 END) as clean_transactions,
    COUNT(CASE WHEN anomaly_score > 0.7 THEN 1 END) as high_risk_count,
    COUNT(CASE WHEN anomaly_score BETWEEN 0.4 AND 0.7 THEN 1 END) as suspicious_count,
    AVG(valor_acto) as avg_transaction_value,
    COUNT(DISTINCT municipio) as municipalities_covered,
    MAX(created_at) as last_updated
FROM transactions;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO propsafe_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO propsafe_user;

-- Vacuum and analyze
VACUUM ANALYZE;

COMMENT ON TABLE transactions IS 'Main table storing all real estate transactions from SNR/IGAC';
COMMENT ON TABLE statistics IS 'Aggregated metrics for dashboard and analysis';
COMMENT ON TABLE alerts IS 'Active and historical alerts for anomalous transactions';
