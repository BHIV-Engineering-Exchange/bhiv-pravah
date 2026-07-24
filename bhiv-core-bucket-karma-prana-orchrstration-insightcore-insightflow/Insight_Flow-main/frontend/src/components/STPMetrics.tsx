import React from 'react';

interface STPMetricsProps {
  loading: boolean;
}

const STPMetrics: React.FC<STPMetricsProps> = ({ loading }) => {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="loading-skeleton h-6 w-32 rounded mb-4"></div>
        <div className="grid grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="loading-skeleton h-20 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  const stpMetrics = [
    {
      title: 'Packets Sent',
      value: '15,247',
      change: '+12%',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      ),
      color: 'bg-gradient-to-r from-indigo-400 to-indigo-600'
    },
    {
      title: 'Success Rate',
      value: '99.8%',
      change: '+0.2%',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'bg-gradient-to-r from-green-400 to-green-600'
    },
    {
      title: 'Avg Latency',
      value: '23ms',
      change: '-5ms',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'bg-gradient-to-r from-blue-400 to-blue-600'
    },
    {
      title: 'Security Score',
      value: '100%',
      change: '0%',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      color: 'bg-gradient-to-r from-purple-400 to-purple-600'
    }
  ];

  return (
    <div className="chart-container fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900">STP Metrics</h3>
          <p className="text-sm text-gray-600">Secure Token Protocol performance</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-r from-purple-400 to-purple-600 rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <span className="text-sm text-gray-600">Secured</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {stpMetrics.map((metric, index) => (
          <div key={metric.title} className="bg-white/50 rounded-xl p-4 border border-white/20 card-hover slide-in" style={{ animationDelay: `${index * 0.1}s` }}>
            <div className="flex items-center justify-between mb-3">
              <div className={`w-10 h-10 ${metric.color} rounded-lg flex items-center justify-center text-white`}>
                {metric.icon}
              </div>
              <div className={`text-xs font-medium px-2 py-1 rounded-full ${
                metric.change.startsWith('+') || metric.change.startsWith('-') && metric.title === 'Avg Latency'
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {metric.change}
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-1">{metric.title}</h4>
              <p className="text-xl font-bold text-gray-900">{metric.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* STP Protocol Status */}
      <div className="mt-6 bg-white/30 rounded-xl p-4 border border-white/20">
        <h4 className="font-semibold text-gray-900 mb-4">Protocol Status</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Encryption</span>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm font-medium text-gray-900">AES-256</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Token Validation</span>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm font-medium text-gray-900">Active</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Checksum Verification</span>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm font-medium text-gray-900">Enabled</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default STPMetrics;