import React from 'react';

interface KarmaMetricsProps {
  loading: boolean;
}

const KarmaMetrics: React.FC<KarmaMetricsProps> = ({ loading }) => {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="loading-skeleton h-6 w-32 rounded mb-4"></div>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="loading-skeleton h-16 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  const karmaData = [
    {
      agent: 'NLP Processor',
      score: 94,
      trend: 'up',
      change: '+5.2',
      requests: 1247,
      color: 'bg-gradient-to-r from-green-400 to-green-600'
    },
    {
      agent: 'TTS Generator',
      score: 89,
      trend: 'up',
      change: '+2.1',
      requests: 856,
      color: 'bg-gradient-to-r from-blue-400 to-blue-600'
    },
    {
      agent: 'Vision Analyzer',
      score: 87,
      trend: 'down',
      change: '-1.3',
      requests: 634,
      color: 'bg-gradient-to-r from-purple-400 to-purple-600'
    }
  ];

  return (
    <div className="chart-container fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Karma Metrics</h3>
          <p className="text-sm text-gray-600">Behavioral scoring and agent reputation</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 warm-gradient rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <span className="text-sm text-gray-600">Enabled</span>
        </div>
      </div>

      <div className="space-y-4">
        {karmaData.map((item, index) => (
          <div key={item.agent} className="bg-white/50 rounded-xl p-4 border border-white/20 card-hover slide-in" style={{ animationDelay: `${index * 0.1}s` }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`w-12 h-12 ${item.color} rounded-xl flex items-center justify-center text-white font-bold`}>
                  {item.score}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">{item.agent}</h4>
                  <p className="text-sm text-gray-600">{item.requests.toLocaleString()} requests processed</p>
                </div>
              </div>
              
              <div className="text-right">
                <div className={`flex items-center space-x-1 ${item.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                  <svg className={`w-4 h-4 ${item.trend === 'down' ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
                  </svg>
                  <span className="text-sm font-medium">{item.change}</span>
                </div>
              </div>
            </div>
            
            {/* Karma Score Bar */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                <span>Karma Score</span>
                <span>{item.score}/100</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="progress-bar h-2 rounded-full transition-all duration-1000" 
                  style={{ width: `${item.score}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Karma Summary */}
      <div className="mt-6 bg-white/30 rounded-xl p-4 border border-white/20">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-gray-900">90.0</div>
            <div className="text-sm text-gray-600">Avg Karma</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">+2.0</div>
            <div className="text-sm text-gray-600">Weekly Change</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">2,737</div>
            <div className="text-sm text-gray-600">Total Requests</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KarmaMetrics;