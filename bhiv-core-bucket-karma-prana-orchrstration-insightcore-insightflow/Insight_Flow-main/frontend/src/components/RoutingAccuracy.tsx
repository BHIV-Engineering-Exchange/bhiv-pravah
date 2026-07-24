import React from 'react';

interface RoutingAccuracyProps {
  data: any[];
  loading: boolean;
}

const RoutingAccuracy: React.FC<RoutingAccuracyProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="loading-skeleton h-6 w-32 rounded mb-4"></div>
        <div className="loading-skeleton h-48 rounded-xl"></div>
      </div>
    );
  }

  const accuracyData = [
    { time: '00:00', accuracy: 94 },
    { time: '04:00', accuracy: 96 },
    { time: '08:00', accuracy: 92 },
    { time: '12:00', accuracy: 98 },
    { time: '16:00', accuracy: 95 },
    { time: '20:00', accuracy: 97 },
    { time: '24:00', accuracy: 94 }
  ];

  const strategies = [
    { name: 'Q-Learning', accuracy: 96.2, color: 'bg-orange-500', requests: 1247 },
    { name: 'Weighted', accuracy: 94.8, color: 'bg-blue-500', requests: 856 },
    { name: 'Round Robin', accuracy: 89.1, color: 'bg-purple-500', requests: 634 }
  ];

  return (
    <div className="chart-container fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Routing Accuracy</h3>
          <p className="text-sm text-gray-600">Strategy performance over time</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">95.4%</div>
          <div className="text-sm text-gray-600">Overall Accuracy</div>
        </div>
      </div>

      {/* Accuracy Chart Visualization */}
      <div className="bg-white/30 rounded-xl p-4 border border-white/20 mb-6">
        <div className="h-32 flex items-end justify-between space-x-2">
          {accuracyData.map((point, index) => (
            <div key={point.time} className="flex flex-col items-center flex-1">
              <div 
                className="w-full bg-gradient-to-t from-orange-400 to-orange-600 rounded-t transition-all duration-1000 hover:from-orange-500 hover:to-orange-700" 
                style={{ 
                  height: `${point.accuracy}%`,
                  animationDelay: `${index * 0.1}s`
                }}
                title={`${point.time}: ${point.accuracy}%`}
              ></div>
              <span className="text-xs text-gray-600 mt-2">{point.time}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Strategy Breakdown */}
      <div className="space-y-3">
        <h4 className="font-semibold text-gray-900">Strategy Performance</h4>
        {strategies.map((strategy, index) => (
          <div key={strategy.name} className="bg-white/50 rounded-xl p-4 border border-white/20 card-hover slide-in" style={{ animationDelay: `${index * 0.1}s` }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`w-4 h-4 ${strategy.color} rounded`}></div>
                <div>
                  <h5 className="font-medium text-gray-900">{strategy.name}</h5>
                  <p className="text-sm text-gray-600">{strategy.requests} requests</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">{strategy.accuracy}%</div>
              </div>
            </div>
            
            {/* Accuracy Bar */}
            <div className="mt-3">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`${strategy.color} h-2 rounded-full transition-all duration-1000`}
                  style={{ width: `${strategy.accuracy}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Accuracy Insights */}
      <div className="mt-6 bg-white/30 rounded-xl p-4 border border-white/20">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-lg font-bold text-gray-900">2,737</div>
            <div className="text-sm text-gray-600">Total Routings</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-900">+2.1%</div>
            <div className="text-sm text-gray-600">Improvement</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoutingAccuracy;