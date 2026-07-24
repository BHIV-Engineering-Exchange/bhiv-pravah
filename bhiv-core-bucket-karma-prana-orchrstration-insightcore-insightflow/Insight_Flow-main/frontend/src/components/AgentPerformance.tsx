import React from 'react';
import { AgentPerformance } from '../types';

interface AgentPerformanceChartProps {
  agents: AgentPerformance[];
  loading: boolean;
}

const AgentPerformanceChart: React.FC<AgentPerformanceChartProps> = ({ agents, loading }) => {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="loading-skeleton h-6 w-40 rounded mb-6"></div>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <div className="loading-skeleton w-12 h-12 rounded-xl"></div>
              <div className="flex-1">
                <div className="loading-skeleton h-4 w-32 rounded mb-2"></div>
                <div className="loading-skeleton h-3 w-24 rounded"></div>
              </div>
              <div className="loading-skeleton h-8 w-16 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Mock data if no agents provided
  const mockAgents: AgentPerformance[] = agents.length > 0 ? agents : [
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

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'nlp':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        );
      case 'tts':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M9 12a3 3 0 106 0v5a3 3 0 11-6 0v-5z" />
          </svg>
        );
      case 'computer_vision':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        );
      default:
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getPerformanceColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.8) return 'text-yellow-600';
    if (score >= 0.7) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="chart-container fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900">Agent Performance</h3>
          <p className="text-xs text-gray-600">Real-time metrics</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-sm text-gray-600">{mockAgents.filter(a => a.status === 'active').length} Active</span>
        </div>
      </div>

      <div className="space-y-4">
        {mockAgents.map((agent, index) => (
          <div key={agent.agent_id} className="bg-white/50 rounded-lg p-3 border border-white/20 card-hover" style={{ animationDelay: `${index * 0.1}s` }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="w-8 h-8 warm-gradient rounded-lg flex items-center justify-center text-white">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {agent.agent_type === 'nlp' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />}
                      {agent.agent_type === 'tts' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M9 12a3 3 0 106 0v5a3 3 0 11-6 0v-5z" />}
                      {agent.agent_type === 'computer_vision' && <><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></>}
                    </svg>
                  </div>
                  <div className={`absolute -top-1 -right-1 w-3 h-3 ${getStatusColor(agent.status)} rounded-full border border-white`}></div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 text-sm">{agent.agent_name}</h4>
                  <p className="text-xs text-gray-600 capitalize">{agent.agent_type.replace('_', ' ')}</p>
                </div>
              </div>
              
              <div className="text-right">
                <div className={`text-lg font-bold ${getPerformanceColor(agent.performance_score)}`}>
                  {(agent.performance_score * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500">
                  {agent.total_requests.toLocaleString()} req
                </div>
              </div>
            </div>
            
            {/* Performance Metrics */}
            <div className="mt-3 grid grid-cols-3 gap-2">
              <div className="text-center">
                <div className="text-sm font-semibold text-gray-900">
                  {(agent.success_rate * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500">Success</div>
              </div>
              <div className="text-center">
                <div className="text-sm font-semibold text-gray-900">
                  {agent.average_latency}ms
                </div>
                <div className="text-xs text-gray-500">Latency</div>
              </div>
              <div className="text-center">
                <div className="text-sm font-semibold text-gray-900">
                  {Math.floor(agent.total_requests / 24)}/h
                </div>
                <div className="text-xs text-gray-500">Rate</div>
              </div>
            </div>
            
            {/* Performance Bar */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                <span>Performance</span>
                <span>{(agent.performance_score * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="progress-bar h-2 rounded-full transition-all duration-1000" 
                  style={{ width: `${agent.performance_score * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Summary Stats */}
      <div className="mt-6 bg-white/30 rounded-xl p-4 border border-white/20">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {(mockAgents.reduce((acc, agent) => acc + agent.performance_score, 0) / mockAgents.length * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">Avg Performance</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {mockAgents.reduce((acc, agent) => acc + agent.total_requests, 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Total Requests</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(mockAgents.reduce((acc, agent) => acc + agent.average_latency, 0) / mockAgents.length)}ms
            </div>
            <div className="text-sm text-gray-600">Avg Latency</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentPerformanceChart;