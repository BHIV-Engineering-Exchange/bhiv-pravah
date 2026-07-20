import { useEffect, useState } from 'react';
import { useSocket } from '../context/socket-context';

/**
 * Custom hook for handling real-time updates
 * @param {string} eventType - The type of event to listen for ('attendance', 'aim', 'progress', 'task')
 * @param {function} onUpdate - Callback function to execute when update occurs
 * @param {array} dependencies - Dependencies array for the effect
 */
export const useRealTimeUpdates = (eventType, onUpdate, dependencies = []) => {
  const { connected } = useSocket();
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    if (!connected || !onUpdate) return;

    const handleUpdate = (event) => {
      console.log(`🔄 Real-time update received for ${eventType}:`, event.detail);
      setLastUpdate({ type: eventType, data: event.detail, timestamp: Date.now() });
      onUpdate(event.detail);
    };

    // Map event types to their corresponding custom events
    const eventMap = {
      'attendance': 'attendance-updated',
      'aim': 'aim-updated',
      'progress': 'progress-updated',
      'task': 'task-updated'
    };

    const eventName = eventMap[eventType];
    if (eventName) {
      window.addEventListener(eventName, handleUpdate);
      
      return () => {
        window.removeEventListener(eventName, handleUpdate);
      };
    }
  }, [connected, eventType, onUpdate, ...dependencies]);

  return { lastUpdate, connected };
};

/**
 * Hook for multiple event types
 * @param {object} eventHandlers - Object with event types as keys and handlers as values
 * @param {array} dependencies - Dependencies array for the effect
 */
export const useMultipleRealTimeUpdates = (eventHandlers, dependencies = []) => {
  const { connected } = useSocket();
  const [lastUpdates, setLastUpdates] = useState({});

  useEffect(() => {
    if (!connected || !eventHandlers) return;

    const eventMap = {
      'attendance': 'attendance-updated',
      'aim': 'aim-updated',
      'progress': 'progress-updated',
      'task': 'task-updated'
    };

    const listeners = [];

    Object.entries(eventHandlers).forEach(([eventType, handler]) => {
      const eventName = eventMap[eventType];
      if (eventName && handler) {
        const handleUpdate = (event) => {
          console.log(`🔄 Real-time update received for ${eventType}:`, event.detail);
          setLastUpdates(prev => ({
            ...prev,
            [eventType]: { data: event.detail, timestamp: Date.now() }
          }));
          handler(event.detail);
        };

        window.addEventListener(eventName, handleUpdate);
        listeners.push({ eventName, handler: handleUpdate });
      }
    });

    return () => {
      listeners.forEach(({ eventName, handler }) => {
        window.removeEventListener(eventName, handler);
      });
    };
  }, [connected, eventHandlers, ...dependencies]);

  return { lastUpdates, connected };
};

/**
 * Hook for refreshing data when real-time updates occur
 * @param {function} refreshFunction - Function to call when updates occur
 * @param {array} eventTypes - Array of event types to listen for
 * @param {array} dependencies - Dependencies array for the effect
 */
export const useAutoRefresh = (refreshFunction, eventTypes = ['attendance', 'aim', 'progress', 'task'], dependencies = []) => {
  const { connected } = useSocket();
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!connected || !refreshFunction) return;

    const eventMap = {
      'attendance': 'attendance-updated',
      'aim': 'aim-updated',
      'progress': 'progress-updated',
      'task': 'task-updated'
    };

    const handleUpdate = async (event) => {
      console.log(`🔄 Auto-refreshing data due to ${event.type} update:`, event.detail);
      setIsRefreshing(true);
      try {
        await refreshFunction();
      } catch (error) {
        console.error('Error during auto-refresh:', error);
      } finally {
        setIsRefreshing(false);
      }
    };

    const listeners = [];

    eventTypes.forEach(eventType => {
      const eventName = eventMap[eventType];
      if (eventName) {
        window.addEventListener(eventName, handleUpdate);
        listeners.push(eventName);
      }
    });

    return () => {
      listeners.forEach(eventName => {
        window.removeEventListener(eventName, handleUpdate);
      });
    };
  }, [connected, refreshFunction, eventTypes, ...dependencies]);

  return { isRefreshing, connected };
};