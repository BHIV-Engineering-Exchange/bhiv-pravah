import React from 'react';
import { WebSocketMessage } from '../types';

interface RecentRoutingsProps {
  routings: WebSocketMessage[];
  loading: boolean;
}

const RecentRoutings: React.FC<RecentRoutingsProps> = ({ routings, loading }) => {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="loading-skeleton h-6 w-32 rounded mb-4"></div>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <div className="loading-skeleton w-10 h-10 rounded-full"></div>
              <div className="flex-1">
                <div className="loading-skeleton h-4 w-48 rounded mb-2"></div>
                <div className="loading-skeleton h-3 w-32 rounded"></div>
              </div>
              <div className="loading-skeleton h-6 w-16 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Mock data for demonstration
  const mockRoutings = routings.length > 0 ? routings : [
    {
      id: '1',
      type: 'nlp_request',
      agent: 'NLP Processor',
      status: 'success',
      latency: 145,
      confidence: 0.94,
      timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
      input: 'Analyze sentiment of customer feedback'
    },
    {
      id: '2',
      type: 'tts_request',
      agent: 'TTS Generator',
      status: 'success',
      latency: 230,
      confidence: 0.89,
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      input: 'Convert text to speech for notification'
    },
    {
      id: '3',
      type: 'vision_request',
      agent: 'Vision Analyzer',
      status: 'success',
      latency: 320,
      confidence: 0.87,
      timestamp: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
      input: 'Detect objects in uploaded image'
    },
    {
      id: '4',
      type: 'nlp_request',
      agent: 'NLP Processor',
      status: 'warning',
      latency: 580,
      confidence: 0.72,
      timestamp: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
      input: 'Process complex multi-language text'
    },
    {
      id: '5',
      type: 'tts_request',
      agent: 'TTS Generator',
      status: 'error',
      latency: 0,
      confidence: 0,
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      input: 'Generate speech for long document'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'nlp_request':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        );
      case 'tts_request':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M9 12a3 3 0 106 0v5a3 3 0 11-6 0v-5z" />
          </svg>
        );
      case 'vision_request':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000 / 60);
    
    if (diff < 1) return 'Just now';
    if (diff < 60) return `${diff}m ago`;
    if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="chart-container fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Recent Activity</h3>
          <p className="text-sm text-gray-600">Live routing events and agent responses</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded-full pulse-animation"></div>
          <span className="text-sm text-gray-600">Live</span>
        </div>
      </div>

      <div className="space-y-4 max-h-96 overflow-y-auto scrollbar-hide">
        {mockRoutings.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-gray-500">No recent routing activity</p>
            <p className="text-sm text-gray-400 mt-1">Activity will appear here as requests are processed</p>
          </div>
        ) : (
          mockRoutings.map((routing: any, index) => (
            <div key={routing.id || index} className="bg-white/50 rounded-xl p-4 border border-white/20 card-hover slide-in" style={{ animationDelay: `${index * 0.05}s` }}>
              <div className="flex items-start space-x-4">
                {/* Agent Icon */}
                <div className="w-10 h-10 warm-gradient rounded-xl flex items-center justify-center text-white flex-shrink-0">
                  {getAgentIcon(routing.type)}
                </div>
                
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900 truncate">{routing.agent}</h4>
                    <div className="flex items-center space-x-2">
                      <div className={`w-6 h-6 ${getStatusColor(routing.status)} rounded-full flex items-center justify-center text-white`}>
                        {getStatusIcon(routing.status)}
                      </div>
                      <span className="text-sm text-gray-500">{formatTime(routing.timestamp)}</span>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-3 truncate">{routing.input}</p>
                  
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-4">
                      {routing.status !== 'error' && (
                        <>
                          <span className="text-gray-500">
                            <span className="font-medium">Latency:</span> {routing.latency}ms
                          </span>
                          <span className="text-gray-500">
                            <span className="font-medium">Confidence:</span> {(routing.confidence * 100).toFixed(1)}%
                          </span>
                        </>
                      )}
                      {routing.status === 'error' && (
                        <span className="text-red-600 font-medium">Request failed</span>
                      )}
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      routing.status === 'success' ? 'bg-green-100 text-green-800' :
                      routing.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                      routing.status === 'error' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {routing.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Activity Summary */}
      <div className="mt-6 bg-white/30 rounded-xl p-4 border border-white/20">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-lg font-bold text-gray-900">{mockRoutings.filter((r: any) => r.status === 'success').length}</div>
            <div className="text-sm text-gray-600">Successful</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-900">{mockRoutings.filter((r: any) => r.status === 'warning').length}</div>
            <div className="text-sm text-gray-600">Warnings</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-900">{mockRoutings.filter((r: any) => r.status === 'error').length}</div>
            <div className="text-sm text-gray-600">Errors</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecentRoutings;