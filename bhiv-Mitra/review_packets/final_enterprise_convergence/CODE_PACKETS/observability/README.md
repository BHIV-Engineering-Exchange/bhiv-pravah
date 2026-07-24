# Observability Code Packet

## Contents

### OpenTelemetry
- `backend/app/core/monitoring.py` - OTEL initialization, tracer, meter, Prometheus integration

### Prometheus
- `backend/deploy/prometheus/prometheus.yml` - Scrape configuration

### OpenTelemetry Collector
- `backend/deploy/otel-collector/config.yml` - Collector pipeline config

### Grafana
- `backend/deploy/grafana/provisioning/datasources.yml` - Prometheus datasource
- `backend/deploy/grafana/dashboards/dashboard.yml` - Dashboard provisioning
- `backend/deploy/grafana/dashboards/mitra-overview.json` - Enterprise dashboard

## What Changed
- Added OpenTelemetry tracing and metrics with OTLP export
- Prometheus metrics auto-instrumented via FastAPIInstrumentor
- Grafana dashboard with request rate, latency, enforcement, integrations panels
- Collector pipeline with batching, memory limiting, resource attributes

## Why
- Production systems need observability for debugging and optimization
- Prometheus metrics enable alerting and capacity planning
- OpenTelemetry provides distributed tracing across services
- Grafana dashboards give operational visibility
