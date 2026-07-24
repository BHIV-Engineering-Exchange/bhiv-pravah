import axios from 'axios';
import { AnalyticsOverview, AgentPerformance } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000,
});

// Mock data for development/demo
const mockAnalyticsOverview: AnalyticsOverview = {
  time_range: '24h',
  total_routings: 2737,
  successful_routings: 2612,
  failed_routings: 125,
  success_rate: 95.4,
  average_confidence: 0.89,
  average_latency_ms: 187,
  active_agents: 3,
  total_agents: 3
};

const mockAgentPerformance: AgentPerformance[] = [
  {
    agent_id: '1',
    agent_name: 'NLP Processor',
    agent_type: 'nlp',
    status: 'active',
    performance_score: 0.94,
    success_rate: 0.96,
    average_latency: 145,
    total_requests: 1247
  },
  {
    agent_id: '2',
    agent_name: 'TTS Generator',
    agent_type: 'tts',
    status: 'active',
    performance_score: 0.89,
    success_rate: 0.91,
    average_latency: 230,
    total_requests: 856
  },
  {
    agent_id: '3',
    agent_name: 'Vision Analyzer',
    agent_type: 'computer_vision',
    status: 'active',
    performance_score: 0.87,
    success_rate: 0.88,
    average_latency: 320,
    total_requests: 634
  }
];

export const apiService = {
  async getAnalyticsOverview(timeRange: string): Promise<AnalyticsOverview> {
    try {
      const response = await api.get(`/api/v1/analytics/overview?time_range=${timeRange}`);
      return response.data;
    } catch (error) {
      console.warn('API not available, using mock data:', error);
      // Return mock data with slight variations based on time range
      const multiplier = timeRange === '1h' ? 0.1 : timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 1;
      return {
        ...mockAnalyticsOverview,
        total_routings: Math.floor(mockAnalyticsOverview.total_routings * multiplier),
        successful_routings: Math.floor(mockAnalyticsOverview.successful_routings * multiplier),
        failed_routings: Math.floor(mockAnalyticsOverview.failed_routings * multiplier)
      };
    }
  },

  async getAgentPerformance(timeRange: string): Promise<{ agents: AgentPerformance[] }> {
    try {
      const response = await api.get(`/api/v1/analytics/agent-performance?time_range=${timeRange}`);
      return response.data;
    } catch (error) {
      console.warn('API not available, using mock data:', error);
      // Return mock data with slight variations
      const multiplier = timeRange === '1h' ? 0.1 : timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 1;
      return {
        agents: mockAgentPerformance.map(agent => ({
          ...agent,
          total_requests: Math.floor(agent.total_requests * multiplier)
        }))
      };
    }
  },

  async healthCheck(): Promise<boolean> {
    try {
      await api.get('/health');
      return true;
    } catch (error) {
      return false;
    }
  }
};