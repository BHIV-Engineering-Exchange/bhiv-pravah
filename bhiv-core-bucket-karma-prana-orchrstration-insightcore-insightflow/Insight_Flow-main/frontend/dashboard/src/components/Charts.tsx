// frontend/dashboard/src/components/Charts.tsx
import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface TelemetryPacket {
  request_id: string;
  decision: {
    selected_agent: string;
    alternatives: string[];
    confidence: number;
    latency_ms: number;
    strategy: string;
  };
  feedback: {
    reward_signal: number | null;
    last_outcome: string | null;
  };
  trace: {
    version: string;
    node: string;
    ts: string;
  };
}

interface ChartsProps {
  packets: TelemetryPacket[];
}

export const Charts: React.FC<ChartsProps> = ({ packets }) => {
  // Prepare confidence data (last 50 packets)
  const confidenceData = packets.slice(0, 50).reverse().map((p, idx) => ({
    index: idx,
    confidence: p.decision.confidence * 100,
    timestamp: new Date(p.trace.ts).toLocaleTimeString(),
  }));

  // Prepare latency data (last 50 packets)
  const latencyData = packets.slice(0, 50).reverse().map((p, idx) => ({
    index: idx,
    latency: p.decision.latency_ms,
    timestamp: new Date(p.trace.ts).toLocaleTimeString(),
  }));

  // Prepare reward histogram
  const rewardData = packets
    .filter((p) => p.feedback.reward_signal !== null)
    .reduce((acc, p) => {
      const bucket = Math.floor(p.feedback.reward_signal! * 10) / 10;
      const key = bucket.toFixed(1);
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

  const rewardHistogram = Object.entries(rewardData).map(([reward, count]) => ({
    reward: parseFloat(reward),
    count,
  }));

  // Prepare success ratio by agent
  const agentStats = packets.reduce((acc, p) => {
    const agent = p.decision.selected_agent;
    if (!acc[agent]) {
      acc[agent] = { total: 0, success: 0 };
    }
    acc[agent].total += 1;
    if (p.feedback.last_outcome === 'success') {
      acc[agent].success += 1;
    }
    return acc;
  }, {} as Record<string, { total: number; success: number }>);

  const successRatioData = Object.entries(agentStats).map(([agent, stats]) => ({
    agent,
    success_rate: (stats.success / stats.total) * 100,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Confidence Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Confidence Over Time
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={confidenceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="index" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="confidence"
              stroke="#0ea5e9"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Latency Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Latency Trend
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={latencyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="index" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="latency"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Reward Histogram */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Reward Signal Distribution
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={rewardHistogram}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="reward" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#f59e0b" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Success Ratio by Agent */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Success Rate by Agent
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={successRatioData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="agent" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Bar dataKey="success_rate" fill="#8b5cf6" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};