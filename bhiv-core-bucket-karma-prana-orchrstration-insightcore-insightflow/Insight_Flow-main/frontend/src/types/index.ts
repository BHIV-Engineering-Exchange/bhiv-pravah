export interface AnalyticsOverview {
  time_range: string;
  total_routings: number;
  successful_routings: number;
  failed_routings: number;
  success_rate: number;
  average_confidence: number;
  average_latency_ms: number;
  active_agents: number;
  total_agents: number;
}

export interface AgentPerformance {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  status: string;
  performance_score: number;
  success_rate: number;
  average_latency: number;
  total_requests: number;
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp?: string;
}

export interface RouteRequest {
  input_data: Record<string, any>;
  input_type: string;
  context?: Record<string, any>;
  strategy?: string;
}

export interface RouteResponse {
  request_id: string;
  routing_log_id: string;
  agent_id: string;
  agent_name: string;
  agent_type: string;
  confidence_score: number;
  routing_reason: string;
  routing_strategy: string;
}