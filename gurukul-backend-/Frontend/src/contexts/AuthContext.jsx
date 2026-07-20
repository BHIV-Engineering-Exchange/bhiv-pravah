import { createContext, useContext, useEffect, useState } from 'react';
import API_BASE_URL from '../config';

const AuthContext = createContext();

// Multi-tenant: add X-Tenant-ID from localStorage so backend uses correct DB
function authHeaders(extra = {}) {
    const h = { ...extra };
    try {
        const tenantId = localStorage.getItem('gurukul_tenant_id');
        if (tenantId) h['X-Tenant-ID'] = tenantId;
    } catch (e) { /* ignore */ }
    return h;
}

// Helper function to retry fetch requests with exponential backoff
// This handles Render free tier cold starts which can take 30-60 seconds
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
    const isNetworkError = (error) => {
        return (
            error instanceof TypeError ||
            error.name === 'NetworkError' ||
            error.message.includes('fetch') ||
            error.message.includes('NetworkError') ||
            error.message.includes('Failed to fetch')
        );
    };

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        let timeoutId = null;
        try {
            console.log(`[Auth] Fetch attempt ${attempt + 1}/${maxRetries + 1} to:`, url);

            // Increase timeout for later attempts (backend may be waking up)
            const timeout = 30000 + (attempt * 10000); // 30s, 40s, 50s, 60s
            const controller = new AbortController();
            timeoutId = setTimeout(() => controller.abort(), timeout);

            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });

            if (timeoutId) clearTimeout(timeoutId);
            return response;
        } catch (error) {
            if (timeoutId) clearTimeout(timeoutId);

            // If it's the last attempt, throw the error
            if (attempt === maxRetries) {
                console.error(`[Auth] All ${maxRetries + 1} fetch attempts failed`);
                throw error;
            }

            // Only retry on network errors (backend sleeping)
            if (isNetworkError(error) || error.name === 'AbortError') {
                const delay = Math.min(1000 * Math.pow(2, attempt), 10000); // Exponential backoff: 1s, 2s, 4s, max 10s
                console.warn(`[Auth] Network error on attempt ${attempt + 1}, retrying in ${delay}ms... (backend may be waking up)`);
                await new Promise(resolve => setTimeout(resolve, delay));
                continue;
            }

            // For other errors (CORS, auth, etc.), don't retry
            throw error;
        }
    }
}

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [token, setToken] = useState(() => {
        // Get token from localStorage
        return localStorage.getItem('auth_token') || null;
    });

    // Log runtime API configuration to help debug connectivity issues in production
    if (typeof window !== 'undefined') {
        // This will run on initial render in the browser only
        // eslint-disable-next-line no-console
        console.log('[Auth] Runtime API_BASE_URL:', API_BASE_URL, 'hostname:', window.location.hostname);

        // Test backend connectivity on page load
        // Use longer timeout for Render cold starts (free tier services can take 30+ seconds to wake up)
        (async () => {
            try {
                console.log('[Auth] Testing backend connectivity to:', `${API_BASE_URL}/health`);
                const healthResponse = await fetch(`${API_BASE_URL}/health`, {
                    method: 'GET',
                    signal: AbortSignal.timeout(30000) // 30 second timeout for Render cold starts
                });
                console.log('[Auth] Backend health check status:', healthResponse.status);
                if (healthResponse.ok) {
                    const healthData = await healthResponse.json();
                    console.log('[Auth] Backend is reachable! Health data:', healthData);
                } else {
                    console.warn('[Auth] Backend health check returned non-OK status:', healthResponse.status);
                }
            } catch (error) {
                console.error('[Auth] Backend connectivity test FAILED:', error);
                console.error('[Auth] Error type:', error.constructor.name);
                console.error('[Auth] Error message:', error.message);
                if (error.name === 'TimeoutError' || error.message.includes('timeout')) {
                    console.warn('[Auth] Backend may be waking up from sleep (Render free tier). This is normal and requests will work once it\'s ready.');
                } else {
                    console.error('[Auth] This suggests the backend URL may be wrong or CORS is blocking requests');
                }
            }
        })();
    }

    // Check if user is authenticated on mount
    useEffect(() => {
        const checkAuth = async () => {
            const storedToken = localStorage.getItem('auth_token');
            if (storedToken) {
                try {
                    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
                        headers: authHeaders({
                            'Authorization': `Bearer ${storedToken}`
                        }),
                        // Add timeout to prevent hanging - longer for Render cold starts
                        signal: AbortSignal.timeout(30000) // 30 second timeout for Render cold starts
                    });

                    if (response.ok) {
                        const userData = await response.json();
                        setUser({
                            id: userData.id,
                            email: userData.email,
                            full_name: userData.full_name,
                            role: userData.role,
                            assessment_completed: userData.assessment_completed
                        });
                    } else if (response.status === 401) {
                        // Only logout on actual 401 Unauthorized (token is invalid/expired)
                        console.warn('[Auth] Token invalid (401), logging out');
                        localStorage.removeItem('auth_token');
                        localStorage.removeItem('ems_token');
                        // Clear chat-related data to prevent cross-user chat history access
                        localStorage.removeItem('chatbot_conversationId');
                        localStorage.removeItem('chatbot_chatHistory');
                        localStorage.removeItem('gurukul_saved_chats');
                        setToken(null);
                        setUser(null);
                    } else {
                        // For other errors (500, 503, network issues, etc.), keep user logged in
                        // They might have a valid token but server is temporarily unavailable
                        console.warn('[Auth] Auth check failed with status:', response.status, '- keeping session active');
                        // Don't clear token or logout - just don't set user state
                        // User can still use the app, and we'll retry on next page load
                    }
                } catch (error) {
                    // Network errors, timeouts, CORS issues - don't logout
                    // User might have valid token but connection is temporarily unavailable
                    if (error.name === 'AbortError' || error.message.includes('timeout')) {
                        console.warn('[Auth] Auth check timed out - keeping session active');
                    } else if (error instanceof TypeError && error.message.includes('fetch')) {
                        console.warn('[Auth] Network error during auth check - keeping session active');
                    } else {
                        console.warn('[Auth] Auth check error:', error.message, '- keeping session active');
                    }
                    // Don't clear token or logout on network errors
                    // User stays logged in and can continue using the app
                }
            }
            setLoading(false);
        };

        checkAuth();
    }, []);

    const login = async (email, password) => {
        const loginUrl = `${API_BASE_URL}/api/v1/auth/login`;
        console.log('[Auth] ===== LOGIN DEBUG =====');
        console.log('[Auth] Runtime API_BASE_URL:', API_BASE_URL);
        console.log('[Auth] Full login URL:', loginUrl);
        console.log('[Auth] Hostname:', typeof window !== 'undefined' ? window.location.hostname : 'N/A');
        console.log('[Auth] Attempting login...');

        try {
            const response = await fetchWithRetry(loginUrl, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ email, password }),
            }, 3); // Retry up to 3 times (4 total attempts)

            console.log('[Auth] Login response status:', response.status);
            console.log('[Auth] Response OK:', response.ok);

            if (!response.ok) {
                let errorMessage = 'Login failed';
                try {
                    const error = await response.json();
                    errorMessage = error.detail || error.message || 'Login failed';
                    console.error('[Auth] Login error response:', error);
                } catch (e) {
                    // If response is not JSON, use status text
                    errorMessage = response.statusText || 'Login failed';
                    console.error('[Auth] Failed to parse error response:', e);
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            console.log('[Auth] Login successful!');

            // Store token
            localStorage.setItem('auth_token', data.access_token);
            setToken(data.access_token);

            // Extract session_id from token (backend includes it in JWT payload)
            const contextManager = (await import('../utils/contextManager')).default;
            const sessionId = contextManager.extractSessionIdFromToken(data.access_token);
            if (sessionId) {
                localStorage.setItem('session_id', sessionId);
                console.log('[Auth] Session ID extracted from token:', sessionId);
            } else {
                console.warn('[Auth] No session_id found in token');
            }

            // Set user
            setUser(data.user);

            return { session: { access_token: data.access_token }, user: data.user };
        } catch (error) {
            console.error('[Auth] ===== LOGIN ERROR DETAILS =====');
            console.error('[Auth] Error type:', error.constructor.name);
            console.error('[Auth] Error message:', error.message);
            console.error('[Auth] Error stack:', error.stack);
            console.error('[Auth] Full error object:', error);

            // Handle network errors with more detail
            if (error.name === 'TimeoutError' || error.name === 'AbortError' || error.message.includes('timeout')) {
                console.error('[Auth] Request timed out after all retries - backend may be taking too long to wake up');
                throw new Error('Server is taking longer than expected to respond. This may happen if the server is waking up from sleep. Please wait a moment and try again.');
            } else if (error instanceof TypeError || error.message.includes('NetworkError') || error.message.includes('fetch')) {
                console.error('[Auth] Network error after all retries - backend may be unreachable');
                console.error('[Auth] Error message contains "fetch":', error.message.includes('fetch'));
                console.error('[Auth] Error message contains "NetworkError":', error.message.includes('NetworkError'));
                // Still throw the generic message for user, but log everything
                throw new Error('Unable to connect to server. The server may be starting up. Please wait a moment and try again.');
            }
            throw error;
        }
    };

    const signup = async (email, password, role, full_name) => {
        const signupUrl = `${API_BASE_URL}/api/v1/auth/register`;
        console.log('[Auth] ===== SIGNUP DEBUG =====');
        console.log('[Auth] Runtime API_BASE_URL:', API_BASE_URL);
        console.log('[Auth] Full signup URL:', signupUrl);
        console.log('[Auth] Hostname:', typeof window !== 'undefined' ? window.location.hostname : 'N/A');
        console.log('[Auth] Attempting registration...');

        try {
            const response = await fetchWithRetry(signupUrl, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({
                    email,
                    password,
                    role: role || 'STUDENT',
                    full_name: full_name || null
                }),
            }, 3); // Retry up to 3 times (4 total attempts)

            console.log('[Auth] Registration response status:', response.status);
            console.log('[Auth] Response OK:', response.ok);
            console.log('[Auth] Response headers:', Object.fromEntries(response.headers.entries()));

            if (!response.ok) {
                let errorMessage = 'Registration failed';
                try {
                    const error = await response.json();
                    errorMessage = error.detail || error.message || 'Registration failed';
                    console.error('[Auth] Registration error response:', error);
                } catch (e) {
                    // If response is not JSON, use status text
                    errorMessage = response.statusText || 'Registration failed';
                    console.error('[Auth] Failed to parse error response:', e);
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            console.log('[Auth] Registration successful!');

            // Store token
            localStorage.setItem('auth_token', data.access_token);
            setToken(data.access_token);

            // Set user
            setUser(data.user);

            return { user: data.user, session: { access_token: data.access_token } };
        } catch (error) {
            console.error('[Auth] ===== SIGNUP ERROR DETAILS =====');
            console.error('[Auth] Error type:', error.constructor.name);
            console.error('[Auth] Error message:', error.message);
            console.error('[Auth] Error stack:', error.stack);
            console.error('[Auth] Full error object:', error);

            // Handle network errors with more detail
            if (error.name === 'TimeoutError' || error.name === 'AbortError' || error.message.includes('timeout')) {
                console.error('[Auth] Request timed out after all retries - backend may be taking too long to wake up');
                throw new Error('Server is taking longer than expected to respond. This may happen if the server is waking up from sleep. Please wait a moment and try again.');
            } else if (error instanceof TypeError || error.message.includes('NetworkError') || error.message.includes('fetch')) {
                console.error('[Auth] Network error after all retries - backend may be unreachable');
                console.error('[Auth] Error message contains "fetch":', error.message.includes('fetch'));
                console.error('[Auth] Error message contains "NetworkError":', error.message.includes('NetworkError'));
                // Still throw the generic message for user, but log everything
                throw new Error('Unable to connect to server. The server may be starting up. Please wait a moment and try again.');
            }
            throw error;
        }
    };

    const logout = async () => {
        // Clear token and user
        localStorage.removeItem('auth_token');
        // Clear EMS authentication to prevent cross-account contamination
        localStorage.removeItem('ems_token');
        // Clear chat-related data to prevent cross-user chat history access
        localStorage.removeItem('chatbot_conversationId');
        localStorage.removeItem('chatbot_chatHistory');
        localStorage.removeItem('gurukul_saved_chats');
        setToken(null);
        setUser(null);
    };

    const updateUser = (updates) => {
        setUser(prevUser => prevUser ? { ...prevUser, ...updates } : null);
    };

    return (
        <AuthContext.Provider value={{ user, login, signup, logout, loading, token, updateUser }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    return useContext(AuthContext);
};
