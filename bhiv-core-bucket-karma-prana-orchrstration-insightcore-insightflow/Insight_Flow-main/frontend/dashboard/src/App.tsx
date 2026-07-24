// frontend/dashboard/src/App.tsx
import React from 'react';
import { Activity, Wifi, WifiOff } from 'lucide-react';
import { useWebSocket } from './hooks/useWebSocket';
import { LiveStream } from './components/LiveStream';
import { Charts } from './components/Charts';

const WEBSOCKET_URL = 'ws://localhost:8000/telemetry/decisions';

function App() {
  const { packets, isConnected, error, reconnect } = useWebSocket(WEBSOCKET_URL);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Activity className="w-8 h-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">
                InsightFlow V3 Dashboard
              </h1>
            </div>

            {/* Connection Status */}
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <>
                  <Wifi className="w-5 h-5 text-green-500" />
                  <span className="text-sm text-green-600 font-medium">
                    Connected
                  </span>
                </>
              ) : (
                <>
                  <WifiOff className="w-5 h-5 text-red-500" />
                  <span className="text-sm text-red-600 font-medium">
                    Disconnected
                  </span>
                  <button
                    onClick={reconnect}
                    className="ml-2 px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-700"
                  >
                    Reconnect
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Live Stream */}
          <LiveStream packets={packets} />

          {/* Charts */}
          <Charts packets={packets} />

          {/* Empty State */}
          {packets.length === 0 && (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <Activity className="mx-auto w-12 h-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Signal
              </h3>
              <p className="text-gray-500">
                Waiting for routing decisions from InsightFlow...
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Make a routing request to see live telemetry
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
