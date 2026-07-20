import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import {
  disconnectRecruiterConnection,
  subscribeRecruiterConnectionEvents,
  getRecruiterCurrentConnection,
  checkConnectionHealth,
  RECRUITER_LAST_CONNECTION_KEY,
} from '../services/api'

const CONNECTION_ID_LENGTH = 24

export type RecruiterConnectionStatus = 'none' | 'connected' | 'invalid'

interface RecruiterConnectionState {
  connectionId: string | null
  companyName: string | null
  status: RecruiterConnectionStatus
}

interface RecruiterConnectionContextValue extends RecruiterConnectionState {
  setConnection: (connectionId: string, companyName: string) => void
  clearConnection: () => void
}

const initialState: RecruiterConnectionState = {
  connectionId: null,
  companyName: null,
  status: 'none',
}

const RecruiterConnectionContext = createContext<RecruiterConnectionContextValue | null>(null)

function loadFromStorage(): { connectionId: string; companyName: string } | null {
  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(RECRUITER_LAST_CONNECTION_KEY) : null
    if (!raw) return null
    const parsed = JSON.parse(raw) as { connectionId?: string; companyName?: string }
    if (parsed?.connectionId && parsed.connectionId.length === CONNECTION_ID_LENGTH) {
      return { connectionId: parsed.connectionId, companyName: parsed.companyName ?? '' }
    }
    return null
  } catch {
    return null
  }
}

function saveToStorage(connectionId: string, companyName: string) {
  try {
    localStorage.setItem(RECRUITER_LAST_CONNECTION_KEY, JSON.stringify({ connectionId, companyName }))
  } catch {
    // ignore
  }
}

function clearStorage() {
  try {
    localStorage.removeItem(RECRUITER_LAST_CONNECTION_KEY)
  } catch {
    // ignore
  }
}

export function RecruiterConnectionProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<RecruiterConnectionState>(() => {
    const stored = loadFromStorage()
    if (stored) {
      return {
        connectionId: stored.connectionId,
        companyName: stored.companyName,
        status: 'connected',
      }
    }
    return initialState
  })

  // Fetch current connection from database on mount - ensures connection persists across browsers/devices
  useEffect(() => {
    let mounted = true
    getRecruiterCurrentConnection()
      .then((data) => {
        if (!mounted) return
        if (data.connection_id && data.company_name) {
          // Database has connection - update state and localStorage
          setState({
            connectionId: data.connection_id,
            companyName: data.company_name,
            status: 'connected',
          })
          saveToStorage(data.connection_id, data.company_name)
        } else {
          // No connection in database - clear localStorage if any
          const stored = loadFromStorage()
          if (stored) {
            clearStorage()
            setState(initialState)
          }
        }
      })
      .catch((err) => {
        console.error('Failed to fetch recruiter connection from database:', err)
        // Keep localStorage state on error - fallback behavior
      })
    return () => {
      mounted = false
    }
  }, [])

  // Synchronized updates via SSE - no per-user polling; both parties get same events
  useEffect(() => {
    const abort = new AbortController()
    const unsubscribe = subscribeRecruiterConnectionEvents(
      (ev) => {
        if (ev.event === 'connected' && ev.company_name != null) {
          setState(prev => ({
            ...prev,
            companyName: ev.company_name ?? null,
            status: 'connected',
          }))
        } else if (ev.event === 'disconnected') {
          clearStorage()
          setState(initialState)
        }
      },
      abort.signal
    )
    return () => {
      unsubscribe()
      abort.abort()
    }
  }, [])

  // Bidirectional health check - runs every 30 seconds when connected
  useEffect(() => {
    if (state.status !== 'connected' || !state.connectionId) {
      return
    }

    let intervalId: number | undefined
    let mounted = true

    const performHealthCheck = async () => {
      if (!mounted) return
      try {
        console.log('[Recruiter Health Check] Starting check for connection:', state.connectionId)
        const result = await checkConnectionHealth()
        if (!mounted) return
        
        console.log('[Recruiter Health Check] Result:', result)
        
        // If health check indicates disconnection, clear connection state
        if (!result.healthy || result.disconnected) {
          console.warn('[Recruiter Health Check] Connection unhealthy - disconnecting:', result.reason || 'unknown')
          clearStorage()
          setState(initialState)
        } else if (result.connected === false) {
          // Connection was removed from database
          console.warn('[Recruiter Health Check] Connection no longer exists - disconnecting')
          clearStorage()
          setState(initialState)
        } else {
          console.log('[Recruiter Health Check] Connection healthy')
        }
      } catch (err) {
        console.error('[Recruiter Health Check] Error:', err)
        // Don't disconnect on network errors - SSE will handle actual disconnects
      }
    }

    // Initial health check after 5 seconds (give time for initial setup)
    const timeoutId = window.setTimeout(() => {
      performHealthCheck()
    }, 5000)

    // Periodic health check every 30 seconds
    intervalId = window.setInterval(() => {
      performHealthCheck()
    }, 30000)

    return () => {
      mounted = false
      window.clearTimeout(timeoutId)
      if (intervalId) {
        window.clearInterval(intervalId)
      }
    }
  }, [state.status, state.connectionId])

  const setConnection = useCallback((connectionId: string, companyName: string) => {
    clearStorage()
    saveToStorage(connectionId, companyName)
    setState({
      connectionId,
      companyName,
      status: 'connected',
    })
  }, [])

  const clearConnection = useCallback(() => {
    disconnectRecruiterConnection().catch(() => {})
    clearStorage()
    setState(initialState)
  }, [])

  const value: RecruiterConnectionContextValue = {
    ...state,
    setConnection,
    clearConnection,
  }

  return (
    <RecruiterConnectionContext.Provider value={value}>
      {children}
    </RecruiterConnectionContext.Provider>
  )
}

export function useRecruiterConnection() {
  const ctx = useContext(RecruiterConnectionContext)
  if (!ctx) {
    throw new Error('useRecruiterConnection must be used within RecruiterConnectionProvider')
  }
  return ctx
}

export function useRecruiterConnectionOptional() {
  return useContext(RecruiterConnectionContext)
}
