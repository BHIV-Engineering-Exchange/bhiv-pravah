// Automatically detect if running on localhost
const isLocalhost =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1' ||
    window.location.hostname === '');

// Detect the current Render frontend hostname so we can hard-bind the correct backend.
// This makes the signup/login flow robust even if an old build or misconfigured VITE_API_URL is present.
const isRenderGurukulFrontend =
  typeof window !== 'undefined' &&
  window.location.hostname === 'gurukul-frontend-738j.onrender.com';

// In development mode (Vite), always use localhost (override env variable).
// In production on Render, force the known backend URL so network calls never point to a dead/old service.
// Otherwise, fall back to VITE_API_URL if provided, or the official backend URL.
let API_BASE_URL;

const DEMO_TENANT_ID = import.meta.env.VITE_DEMO_TENANT_ID || '55380df9-9af7-43cc-b065-5a98a3dc6d00';

if (import.meta.env.DEV || isLocalhost) {
  API_BASE_URL = 'http://localhost:3000';
} else if (isRenderGurukulFrontend) {
  // Hard-bind to the live Gurukul backend on Render
  API_BASE_URL = 'https://gurukul-up9j.onrender.com';
} else {
  API_BASE_URL =
    import.meta.env.VITE_API_URL || 'https://gurukul-up9j.onrender.com';
}

export { API_BASE_URL, DEMO_TENANT_ID };

// Debug log in development AND production (for troubleshooting)
console.log('[Config] API Configuration:', {
  VITE_API_URL: import.meta.env.VITE_API_URL,
  isDev: import.meta.env.DEV,
  hostname: typeof window !== 'undefined' ? window.location.hostname : 'N/A',
  isLocalhost,
  isRenderGurukulFrontend,
  API_BASE_URL,
});

// Build version for cache busting
export const BUILD_VERSION = '2026-01-06-v2';

// Updated: 2026-01-06 - Auto-detects localhost vs production (with Render safeguard)
export default API_BASE_URL;
