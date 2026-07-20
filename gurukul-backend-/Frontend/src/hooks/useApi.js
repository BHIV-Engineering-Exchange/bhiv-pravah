import useSWR from 'swr';
import API_BASE_URL from '../config';

/**
 * Custom hook for API data fetching with caching
 * Uses SWR for automatic caching, revalidation, and error handling
 */
const fetcher = async (url) => {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = new Error('An error occurred while fetching the data.');
    error.info = await response.json().catch(() => ({}));
    error.status = response.status;
    throw error;
  }

  return response.json();
};

/**
 * useApi hook - Fetches data with caching
 * @param {string} endpoint - API endpoint (e.g., '/api/v1/user/me')
 * @param {object} options - SWR options (revalidateOnFocus, revalidateOnReconnect, etc.)
 * @returns {object} { data, error, isLoading, mutate }
 */
export const useApi = (endpoint, options = {}) => {
  const { data, error, isLoading, mutate } = useSWR(
    endpoint ? endpoint : null, // Only fetch if endpoint is provided
    fetcher,
    {
      revalidateOnFocus: false, // Don't refetch on window focus
      revalidateOnReconnect: true, // Refetch when network reconnects
      dedupingInterval: 5000, // Dedupe requests within 5 seconds
      ...options,
    }
  );

  return {
    data,
    error,
    isLoading,
    mutate, // Function to manually revalidate
  };
};

export default useApi;

