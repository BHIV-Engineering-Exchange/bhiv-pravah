// frontend/dashboard/src/components/LiveStream.tsx
import React, { useState } from 'react';
import { Search, Filter } from 'lucide-react';

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

interface LiveStreamProps {
  packets: TelemetryPacket[];
}

export const LiveStream: React.FC<LiveStreamProps> = ({ packets }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAgent, setFilterAgent] = useState('');

  const filteredPackets = packets.filter((packet) => {
    const matchesSearch = 
      packet.request_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      packet.decision.selected_agent.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = 
      !filterAgent || packet.decision.selected_agent === filterAgent;
    
    return matchesSearch && matchesFilter;
  });

  const uniqueAgents = Array.from(
    new Set(packets.map((p) => p.decision.selected_agent))
  );

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Live Stream</h2>
        <span className="text-sm text-gray-500">
          {filteredPackets.length} decisions
        </span>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-4 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search by request ID or agent..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div className="relative">
          <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <select
            value={filterAgent}
            onChange={(e) => setFilterAgent(e.target.value)}
            className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none bg-white"
          >
            <option value="">All Agents</option>
            {uniqueAgents.map((agent) => (
              <option key={agent} value={agent}>
                {agent}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Packets Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Request ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agent
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Confidence
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Latency
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Strategy
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Timestamp
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredPackets.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No decisions yet. Waiting for routing traffic...
                </td>
              </tr>
            ) : (
              filteredPackets.map((packet) => (
                <tr key={packet.request_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-mono text-gray-900">
                    {packet.request_id.substring(0, 12)}...
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {packet.decision.selected_agent}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        packet.decision.confidence >= 0.8
                          ? 'bg-green-100 text-green-800'
                          : packet.decision.confidence >= 0.5
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {(packet.decision.confidence * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {packet.decision.latency_ms.toFixed(1)}ms
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {packet.decision.strategy}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(packet.trace.ts).toLocaleTimeString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};