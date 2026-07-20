/**
 * Centralized API Client
 * Handles all API calls with graceful error handling, retries, and fallbacks
 * Ensures frontend never breaks when backend fails
 */

import API_BASE_URL from '../config';

class ApiError extends Error {
    constructor(message, status, data = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }
}

/**
 * Makes an API request with automatic retry and graceful error handling
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {object} options - Fetch options
 * @param {number} retries - Number of retry attempts (default: 1)
 * @returns {Promise<object>} Response data
 */
export const apiRequest = async (endpoint, options = {}, retries = 1) => {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Debug logging
    if (endpoint.includes('analytics')) {
        console.log('API Request Debug:', {
            endpoint,
            API_BASE_URL,
            fullUrl: url,
            hasToken: !!localStorage.getItem('auth_token')
        });
    }

    // Default options
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const fetchOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };

    // Inject auth token from localStorage if available
    try {
        const token = localStorage.getItem('auth_token');
        if (token) {
            fetchOptions.headers['Authorization'] = `Bearer ${token}`;
        }
        // Multi-tenant: send X-Tenant-ID so backend uses correct DB (set via tenant picker or localStorage)
        const tenantId = localStorage.getItem('gurukul_tenant_id');
        if (tenantId) {
            fetchOptions.headers['X-Tenant-ID'] = tenantId;
        }
    } catch (e) {
        console.warn('Failed to get auth token for API request', e);
    }

    let lastError;

    // Retry logic
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const response = await fetch(url, fetchOptions);
            
            // Debug logging for analytics endpoint
            if (endpoint.includes('analytics')) {
                console.log('API Response Debug:', {
                    status: response.status,
                    statusText: response.statusText,
                    url: response.url,
                    headers: Object.fromEntries(response.headers.entries())
                });
            }

            // Handle non-JSON responses
            const contentType = response.headers.get('content-type');
            let data;

            if (contentType && contentType.includes('application/json')) {
                try {
                    data = await response.json();
                } catch (e) {
                    // Response is not valid JSON
                    throw new ApiError(
                        'Invalid response format from server',
                        response.status
                    );
                }
            } else {
                // Handle text or other response types
                const text = await response.text();
                data = { message: text, success: response.ok };
            }

            // Check if response is successful
            if (!response.ok) {
                // Don't retry on client errors (4xx)
                if (response.status >= 400 && response.status < 500) {
                    throw new ApiError(
                        data.detail || data.message || `Request failed with status ${response.status}`,
                        response.status,
                        data
                    );
                }
                // Retry on server errors (5xx) or network issues
                throw new ApiError(
                    data.detail || data.message || `Server error: ${response.status}`,
                    response.status,
                    data
                );
            }

            return data;

        } catch (error) {
            lastError = error;

            // Don't retry on client errors or if it's the last attempt
            if (
                (error instanceof ApiError && error.status >= 400 && error.status < 500) ||
                attempt === retries
            ) {
                break;
            }

            // Wait before retrying (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        }
    }

    // Handle network errors
    if (lastError instanceof TypeError && lastError.message.includes('fetch')) {
        throw new ApiError(
            'Unable to connect to server. Please check your connection.',
            0,
            { networkError: true }
        );
    }

    // Re-throw the last error
    throw lastError;
};

/**
 * GET request helper
 */
export const apiGet = (endpoint, options = {}, retries = 1) => {
    return apiRequest(endpoint, { ...options, method: 'GET' }, retries);
};

/**
 * POST request helper
 */
export const apiPost = (endpoint, data = {}, options = {}, retries = 1) => {
    return apiRequest(
        endpoint,
        {
            ...options,
            method: 'POST',
            body: JSON.stringify(data),
        },
        retries
    );
};

/**
 * PUT request helper
 */
export const apiPut = (endpoint, data = {}, options = {}, retries = 1) => {
    return apiRequest(
        endpoint,
        {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data),
        },
        retries
    );
};

/**
 * DELETE request helper
 */
export const apiDelete = (endpoint, options = {}, retries = 1) => {
    return apiRequest(endpoint, { ...options, method: 'DELETE' }, retries);
};

/**
 * Handles API errors gracefully and returns user-friendly messages
 * @param {Error} error - The error object
 * @param {object} context - Context about what operation failed
 * @returns {object} User-friendly error message and details
 */
export const handleApiError = (error, context = {}) => {
    console.error('API Error:', error, context);

    if (error instanceof ApiError) {
        // Network errors
        if (error.status === 0 || error.data?.networkError) {
            return {
                message: 'We\'re having trouble connecting right now. Please check your internet connection and try again when you\'re ready.',
                title: 'Connection Issue',
                canRetry: true,
                isNetworkError: true,
            };
        }

        // Client errors (4xx)
        if (error.status >= 400 && error.status < 500) {
            if (error.status === 401) {
                return {
                    message: 'Your session has ended. Please sign in again to continue your learning journey.',
                    title: 'Sign In Required',
                    canRetry: false,
                    requiresAuth: true,
                };
            }

            if (error.status === 403) {
                return {
                    message: 'This action isn\'t available right now. If you believe this is an error, please contact support.',
                    title: 'Access Limited',
                    canRetry: false,
                };
            }

            if (error.status === 404) {
                return {
                    message: 'We couldn\'t find what you\'re looking for. It may have been moved or removed.',
                    title: 'Not Found',
                    canRetry: false,
                };
            }

            if (error.status === 422) {
                return {
                    message: error.message || 'Please review your input and try again. We\'re here to help if you need guidance.',
                    title: 'Input Needed',
                    canRetry: false,
                };
            }

            return {
                message: error.message || 'Something didn\'t work as expected. Please try again, or take a moment and come back.',
                title: 'Request Issue',
                canRetry: false,
            };
        }

        // Server errors (5xx)
        if (error.status >= 500) {
            return {
                message: 'Our servers are taking a brief rest. Please try again in a moment. Your progress is safe.',
                title: 'Temporary Issue',
                canRetry: true,
                isServerError: true,
            };
        }
    }

    // Generic error
    return {
        message: error.message || 'Something unexpected happened. Please try again when you\'re ready. Your learning journey continues.',
        title: 'Unexpected Issue',
        canRetry: true,
    };
};

/**
 * Checks if backend is available
 * @returns {Promise<boolean>} True if backend is reachable
 */
export const checkBackendHealth = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(5000), // 5 second timeout
        });
        return response.ok;
    } catch (error) {
        return false;
    }
};

export { ApiError };

