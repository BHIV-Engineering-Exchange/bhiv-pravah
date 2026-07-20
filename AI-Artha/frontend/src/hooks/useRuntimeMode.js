/**
 * useRuntimeMode.js
 *
 * Single source of truth for backend connection state.
 * Determines: BACKEND_CONNECTED | BACKEND_DEGRADED | BACKEND_UNAVAILABLE | MOCK_MODE
 *
 * Rules:
 * - MOCK_MODE only when VITE_MOCK_MODE=true explicitly set
 * - BACKEND_CONNECTED: /health returned 200
 * - BACKEND_DEGRADED: /health returned but signals/snapshot failed
 * - BACKEND_UNAVAILABLE: /health itself failed (network error / 5xx)
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import api from '../services/api';
import { AUTH_TOKEN_KEY } from '../services/api';

export const RUNTIME_MODES = {
  CHECKING:            'CHECKING',
  BACKEND_CONNECTED:   'BACKEND_CONNECTED',
  BACKEND_DEGRADED:    'BACKEND_DEGRADED',
  BACKEND_UNAVAILABLE: 'BACKEND_UNAVAILABLE',
  MOCK_MODE:           'MOCK_MODE',
};

export const MODE_META = {
  CHECKING:            { label: 'CHECKING CONNECTION',    color: 'text-muted-foreground', bg: 'bg-muted/40',          border: 'border-border/40' },
  BACKEND_CONNECTED:   { label: 'LIVE BACKEND SIGNALS',   color: 'text-success',          bg: 'bg-success/10',        border: 'border-success/30' },
  BACKEND_DEGRADED:    { label: 'SNAPSHOT FALLBACK ACTIVE', color: 'text-warning',         bg: 'bg-warning/10',        border: 'border-warning/30' },
  BACKEND_UNAVAILABLE: { label: 'BACKEND UNAVAILABLE',    color: 'text-destructive',       bg: 'bg-destructive/10',    border: 'border-destructive/30' },
  MOCK_MODE:           { label: 'MOCK DEVELOPMENT MODE',  color: 'text-secondary',         bg: 'bg-secondary/10',      border: 'border-secondary/30' },
};

export function useRuntimeMode() {
  const [mode, setMode]           = useState(RUNTIME_MODES.CHECKING);
  const [lastChecked, setLastChecked] = useState(null);
  const [healthDetail, setHealthDetail] = useState(null);

  const check = useCallback(async () => {
    // Explicit mock override
    if (import.meta.env.VITE_MOCK_MODE === 'true') {
      setMode(RUNTIME_MODES.MOCK_MODE);
      return;
    }

    setMode(RUNTIME_MODES.CHECKING);

    // Health endpoint is at root /health — NOT under /api/v1
    // Derive the origin from the api baseURL (strip /api/v1)
    const origin = api.defaults.baseURL?.replace(/\/api\/v1$/, '') || 'http://localhost:5000';

    try {
      const res = await axios.get(`${origin}/health`, { timeout: 5000 });
      setHealthDetail(res.data);

      // Health OK — now check signals endpoint (requires auth token)
      const token = typeof window !== 'undefined' ? localStorage.getItem(AUTH_TOKEN_KEY) : null;

      if (!token) {
        // No token yet (user not logged in) — backend is reachable, signals need auth
        setMode(RUNTIME_MODES.BACKEND_CONNECTED);
      } else {
        try {
          await api.get('/signals/snapshot', { timeout: 5000 });
          setMode(RUNTIME_MODES.BACKEND_CONNECTED);
        } catch (sigErr) {
          // 401 means token expired — still connected, just auth issue
          if (sigErr.response?.status === 401) {
            setMode(RUNTIME_MODES.BACKEND_CONNECTED);
          } else {
            setMode(RUNTIME_MODES.BACKEND_DEGRADED);
          }
        }
      }
    } catch {
      setMode(RUNTIME_MODES.BACKEND_UNAVAILABLE);
    }

    setLastChecked(new Date());
  }, []);

  useEffect(() => { check(); }, [check]);

  return { mode, lastChecked, healthDetail, recheck: check };
}
