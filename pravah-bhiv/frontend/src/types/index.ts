export interface ObservedService {
  url: string;
  status: 'healthy' | 'degraded' | 'unreachable' | 'timeout' | 'error';
  latency_ms: number;
  detail: string;
  last_checked: string;
}

export interface TelemetryEvent {
  ts: string;
  service: string;
  status: string;
  detail: string;
  latency_ms: number;
}

export interface EvidenceBundle {
  bundle_id: string;
  trace_id: string;
  execution_id: string;
  decision_id: string;
  decision_type: string;
  authority_chain: string[];
  evidence: Record<string, any> | Record<string, any>[];
  replay_reference?: string;
  constitutional_hash?: string;
  produced_at: string;
  correlation_id?: string;
  source?: string;
  action?: string;
}

export interface Decision {
  decision_id?: string;
  decision_type?: string;
  environment?: string;
  selected_action?: string;
  action?: string;
  reason: string;
  confidence?: number;
  timestamp?: string;
  version?: string;
  app_name?: string;
  executed_action?: string;
  execution_success?: boolean;
  event?: {
    trace_id: string;
    correlation_id: string;
  };
}

export interface RuntimeMetrics {
  cpu: number;
  memory: number;
  error_rate: number;
  uptime: number;
  workers?: number;
}

export interface RuntimeState {
  service_id: string;
  timestamp: string;
  status: string;
  metrics: RuntimeMetrics;
  issue_detected: boolean;
  issue_type: string;
  recommended_action: string;
}

export interface LiveProductionMonitoredService {
  name: string;
  domain: string;
  url: string;
  status: 'CONNECTED' | 'DEGRADED' | 'DISCONNECTED' | 'CRITICAL';
  health_score: number;
  response_time_ms: number;
  cpu_percent: number;
  memory_percent: number;
  uptime_percent: number;
  last_action: string;
  errors_24h: number;
}

export interface FileStatusRow {
  filename: string;
  status: 'ACTIVE' | 'MISSING';
  size: string;
}

export interface ProjectFileSection {
  title: string;
  icon: string;
  active: number;
  total: number;
  files: FileStatusRow[];
}

export interface LiveDashboardResponse {
  generated_at: string;
  header: {
    title: string;
    subtitle: string;
  };
  live_production_monitoring: LiveProductionMonitoredService[];
  summary_metrics: { label: string; value: string }[];
  ai_learning_status: { label: string; value: string; tone: string }[];
  system_health: { label: string; value: string; tone: string }[];
  performance_metrics: { label: string; value: string }[];
  project_files_status: ProjectFileSection[];
  enhanced_telemetry: {
    status: string;
    avg_latency: string;
    cost: string;
    success: string;
    requests: string;
  };
  policy_evolution: {
    title: string;
    metrics: { label: string; value: string }[];
  };
  error_analytics: {
    recent_errors: { code: string; severity: string }[];
    statistics: {
      total_errors: number;
      avg_impact_score: number;
      critical_issues: number;
      test_coverage_avg: number;
    };
  };
  auto_failover_status: {
    active_domain: string;
    failure_threshold: number;
    domains: { name: string; status: string }[];
  };
  live_events: { title: string; time_ago: string; tone: string }[];
}

export interface AutonomousStatus {
  last_runtime: Record<string, any> | null;
  last_action: string | null;
  recent_autonomous_decisions: Record<string, any>[];
  loop_running: boolean;
}

export interface ActionScope {
  [environment: string]: string[];
}
