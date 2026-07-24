// frontend/dashboard/src/hooks/useWebSocket.ts
import { useState, useEffect, useCallback, useRef } from 'react';

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
  stp?: {
    karmic_weight: number | null;
    context_tags: string[];
    version: string;
  };
}

interface UseWebSocketReturn {
  packets: TelemetryPacket[];
  isConnected: boolean;
  error: string | null;
  reconnect: () => void;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [packets, setPackets] = useState<TelemetryPacket[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    try {
      // Clear existing connection
      if (ws.current) {
        ws.current.close();
      }

      // Create new WebSocket connection
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        try {
          const packet: TelemetryPacket = JSON.parse(event.data);
          
          setPackets((prev) => {
            // Keep last 100 packets
            const updated = [packet, ...prev];
            return updated.slice(0, 100);
          });
        } catch (err) {
          console.error('Failed to parse packet:', err);
        }
      };

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error');
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt reconnection with exponential backoff
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current += 1;
        
        reconnectTimeout.current = setTimeout(() => {
          console.log(`Reconnecting (attempt ${reconnectAttempts.current})...`);
          connect();
        }, delay);
      };

    } catch (err) {
      console.error('Failed to connect:', err);
      setError('Failed to connect');
    }
  }, [url]);

  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const reconnect = useCallback(() => {
    reconnectAttempts.current = 0;
    connect();
  }, [connect]);

  return { packets, isConnected, error, reconnect };
};