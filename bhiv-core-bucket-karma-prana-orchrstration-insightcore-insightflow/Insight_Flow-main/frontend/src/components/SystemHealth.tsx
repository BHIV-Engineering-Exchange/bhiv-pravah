import React from 'react';

interface SystemHealthProps {
  loading: boolean;
}

const SystemHealth: React.FC<SystemHealthProps> = ({ loading }) => {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="loading-skeleton h-6 w-32 rounded mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="loading-skeleton h-20 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  const healthMetrics = [
    {
      name: 'API Health',
      status: 'healthy',
      value: '99.9%',
      description: 'All endpoints operational',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    {
      name: 'Database',
      status: 'healthy',
      value: '2.3ms',
      description: 'Query response time',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
      )
    },
    {
      name: 'Memory Usage',
      status: 'warning',
      value: '78%',
      description: 'System memory utilization',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
        </svg>
      )
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-50 border-green-200';
      case 'warning': return 'bg-yellow-50 border-yellow-200';
      case 'error': return 'bg-red-50 border-red-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="chart-container fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900">System Health</h3>
          <p className="text-xs text-gray-600">System monitoring</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded-full pulse-animation"></div>
          <span className="text-sm text-gray-600">All Systems Operational</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {healthMetrics.map((metric, index) => (
          <div key={metric.name} className={`p-4 rounded-lg border ${getStatusBg(metric.status)} card-hover slide-in`} style={{ animationDelay: `${index * 0.1}s` }}>
            <div className="flex items-center justify-between mb-3">
              <div className={`w-8 h-8 rounded-lg ${metric.status === 'healthy' ? 'bg-green-500' : metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'} flex items-center justify-center text-white`}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {metric.name === 'API Health' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />}
                  {metric.name === 'Database' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />}
                  {metric.name === 'Memory Usage' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />}
                </svg>
              </div>
              <div className={`w-3 h-3 ${getStatusColor(metric.status)} rounded-full`}></div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-1 text-sm">{metric.name}</h4>
              <div className="text-lg font-bold text-gray-900 mb-1">{metric.value}</div>
              <p className="text-xs text-gray-600">{metric.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* System Overview */}
      <div className="mt-6 bg-white/30 rounded-xl p-6 border border-white/20">
        <h4 className="font-semibold text-gray-900 mb-4">System Overview</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">24/7</div>
            <div className="text-sm text-gray-600">Uptime</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">3.2GB</div>
            <div className="text-sm text-gray-600">Memory Used</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">45%</div>
            <div className="text-sm text-gray-600">CPU Usage</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">1.2TB</div>
            <div className="text-sm text-gray-600">Storage</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealth;