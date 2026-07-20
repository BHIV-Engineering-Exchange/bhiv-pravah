import { useEffect, useRef } from 'react';

/**
 * Custom hook for performance monitoring
 * Tracks page load times, API response times, and other metrics
 */
export const usePerformanceMonitor = (pageName) => {
  const startTimeRef = useRef(performance.now());
  const metricsRef = useRef({
    pageLoadTime: 0,
    apiCalls: [],
    renderTime: 0,
  });

  useEffect(() => {
    // Track page load time
    const loadTime = performance.now() - startTimeRef.current;
    metricsRef.current.pageLoadTime = loadTime;

    // Log to console in development
    if (import.meta.env.DEV) {
      console.log(`[Performance] ${pageName} loaded in ${loadTime.toFixed(2)}ms`);
    }

    // Track render time
    const renderStart = performance.now();
    requestAnimationFrame(() => {
      const renderTime = performance.now() - renderStart;
      metricsRef.current.renderTime = renderTime;
      
      if (import.meta.env.DEV) {
        console.log(`[Performance] ${pageName} rendered in ${renderTime.toFixed(2)}ms`);
      }
    });

    // Log metrics on unmount (optional - can send to analytics)
    return () => {
      if (import.meta.env.DEV) {
        console.log(`[Performance] ${pageName} metrics:`, metricsRef.current);
      }
    };
  }, [pageName]);

  return metricsRef.current;
};

/**
 * Hook to measure API call performance
 * @param {string} endpoint - API endpoint name
 * @returns {function} - Function to wrap API calls
 */
export const useApiPerformance = () => {
  const trackApiCall = (endpoint, startTime) => {
    const duration = performance.now() - startTime;
    
    if (import.meta.env.DEV) {
      console.log(`[Performance] API call to ${endpoint} took ${duration.toFixed(2)}ms`);
    }

    // In production, you could send this to analytics
    // analytics.track('api_call', { endpoint, duration });

    return duration;
  };

  return { trackApiCall };
};

/**
 * Hook to measure component render performance
 * @param {string} componentName - Name of the component
 */
export const useRenderPerformance = (componentName) => {
  const renderCountRef = useRef(0);
  const renderTimesRef = useRef([]);

  useEffect(() => {
    const renderStart = performance.now();
    renderCountRef.current += 1;

    return () => {
      const renderTime = performance.now() - renderStart;
      renderTimesRef.current.push(renderTime);

      if (import.meta.env.DEV && renderCountRef.current % 10 === 0) {
        const avgRenderTime = renderTimesRef.current.reduce((a, b) => a + b, 0) / renderTimesRef.current.length;
        console.log(`[Performance] ${componentName} average render time: ${avgRenderTime.toFixed(2)}ms (${renderCountRef.current} renders)`);
      }
    };
  });
};

export default usePerformanceMonitor;

