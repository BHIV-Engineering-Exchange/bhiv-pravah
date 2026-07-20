-- =========================================================================
-- Gurukul Historical Analytics Schema
-- Section 4: Data Collection Foundation
-- Creates dedicated historical intelligence relational schema.
-- =========================================================================

CREATE SCHEMA IF NOT EXISTS gurukul_analytics;

-- 1. Historical System Resource Metrics (CPU, RAM, Autoscale Signals)
CREATE TABLE IF NOT EXISTS gurukul_analytics.historical_system_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    node_name VARCHAR(100) NOT NULL,
    active_replicas INT NOT NULL,
    cpu_utilization_ratio NUMERIC(5, 4) NOT NULL,
    memory_utilization_ratio NUMERIC(5, 4) NOT NULL,
    network_rx_bytes_sec BIGINT NOT NULL,
    network_tx_bytes_sec BIGINT NOT NULL,
    hpa_target_utilization_percent INT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_system_metrics_time ON gurukul_analytics.historical_system_metrics (timestamp DESC);

-- 2. Historical API Traffic & Performance Metrics
CREATE TABLE IF NOT EXISTS gurukul_analytics.historical_traffic_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    total_requests INT NOT NULL,
    error_requests_5xx INT NOT NULL,
    avg_latency_ms NUMERIC(8, 2) NOT NULL,
    p95_latency_ms NUMERIC(8, 2) NOT NULL,
    unique_visitor_count INT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_traffic_logs_time ON gurukul_analytics.historical_traffic_logs (timestamp DESC, endpoint);

-- 3. Historical Visitor Demographics & Client Breakdowns
CREATE TABLE IF NOT EXISTS gurukul_analytics.historical_visitor_demographics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    browser VARCHAR(50) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    traffic_volume INT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_visitor_demographics_time ON gurukul_analytics.historical_visitor_demographics (timestamp DESC);

-- 4. Critical Operational Event Log (Crashes, Restarts, Autoscale Triggering)
CREATE TABLE IF NOT EXISTS gurukul_analytics.operational_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL, -- e.g., 'POD_CRASH', 'HPA_SCALE_UP', 'DB_FAILOVER'
    severity VARCHAR(15) NOT NULL,   -- e.g., 'INFO', 'WARNING', 'CRITICAL'
    source_service VARCHAR(50) NOT NULL, -- e.g., 'gurukul-backend', 'tts-service'
    event_details TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ops_events_severity ON gurukul_analytics.operational_events (timestamp DESC, severity);
