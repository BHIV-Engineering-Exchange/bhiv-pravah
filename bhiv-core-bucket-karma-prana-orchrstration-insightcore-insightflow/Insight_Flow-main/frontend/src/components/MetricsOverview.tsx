import React from 'react';
import { AnalyticsOverview } from '../types';

interface MetricsOverviewProps {
  data: AnalyticsOverview | null;
  loading: boolean;
}

const MetricsOverview: React.FC<MetricsOverviewProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="metric-card rounded-2xl p-6 card-shadow">
            <div className="loading-skeleton h-4 w-24 rounded mb-3"></div>
            <div className="loading-skeleton h-8 w-16 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="metric-card rounded-2xl p-8 text-center card-shadow">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-orange-100 flex items-center justify-center">
          <svg className="w-8 h-8 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-gray-600">No analytics data available</p>
        <p className="text-sm text-gray-400 mt-1">Data will appear once routing begins</p>
      </div>
    );
  }

  const metrics = [
    {
      title: 'Total Routings',
      value: data.total_routings?.toLocaleString() || '0',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      gradient: 'warm-gradient',
      change: '+12%',
      changeType: 'positive'
    },
    {
      title: 'Success Rate',
      value: `${(data.success_rate || 0).toFixed(1)}%`,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      gradient: 'bg-gradient-to-r from-green-400 to-green-600',
      change: '+2.3%',
      changeType: 'positive'
    },
    {
      title: 'Avg Latency',
      value: `${(data.average_latency_ms || 0).toFixed(0)}ms`,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      gradient: 'bg-gradient-to-r from-blue-400 to-blue-600',
      change: '-15ms',
      changeType: 'positive'
    },
    {
      title: 'Active Agents',
      value: `${data.active_agents || 0}/${data.total_agents || 0}`,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      gradient: 'bg-gradient-to-r from-purple-400 to-purple-600',
      change: '+1',
      changeType: 'positive'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {metrics.map((metric, index) => (
        <div key={metric.title} className="metric-card rounded-xl p-4 card-shadow card-hover slide-in" style={{ animationDelay: `${index * 0.1}s` }}>
          <div className="flex items-center justify-between mb-3">
            <div className={`w-8 h-8 rounded-lg ${metric.gradient} flex items-center justify-center text-white`}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {metric.title === 'Total Routings' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />}
                {metric.title === 'Success Rate' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />}
                {metric.title === 'Avg Latency' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />}
                {metric.title === 'Active Agents' && <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />}
              </svg>
            </div>
            <div className={`text-xs font-medium px-2 py-1 rounded-full ${
              metric.changeType === 'positive' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {metric.change}
            </div>
          </div>
          
          <div>
            <h3 className="text-xs font-medium text-gray-600 mb-1">{metric.title}</h3>
            <p className="text-xl font-bold text-gray-900">{metric.value}</p>
          </div>
          
          {/* Progress bar for success rate */}
          {metric.title === 'Success Rate' && (
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="progress-bar h-2 rounded-full" 
                  style={{ width: `${data.success_rate || 0}%` }}
                ></div>
              </div>
            </div>
          )}
          
          {/* Agent status for Active Agents */}
          {metric.title === 'Active Agents' && (
            <div className="mt-4 flex items-center space-x-2">
              <div className="flex -space-x-1">
                {[...Array(Math.min(data.active_agents || 0, 3))].map((_, i) => (
                  <div key={i} className="w-6 h-6 rounded-full bg-green-400 border-2 border-white flex items-center justify-center">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                ))}
                {(data.active_agents || 0) > 3 && (
                  <div className="w-6 h-6 rounded-full bg-gray-400 border-2 border-white flex items-center justify-center text-xs text-white font-medium">
                    +{(data.active_agents || 0) - 3}
                  </div>
                )}
              </div>
              <span className="text-xs text-gray-500">agents online</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default MetricsOverview;