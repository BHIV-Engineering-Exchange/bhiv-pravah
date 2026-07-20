/**
 * Split deploy: SPA vs API (cookie set on API host; magic-link redirect = API /auth/callback).
 *
 * - Legacy: FRONTEND_URL = SPA, APP_URL = API base.
 * - New: APP_URL = SPA only → set API_PUBLIC_URL to the API base (required in production).
 */
export function resolvePublicUrls() {
  const norm = (s) => (typeof s === 'string' ? s.trim().replace(/\/$/, '') : '');
  const port = process.env.PORT || 5000;

  const apiEx = norm(process.env.API_PUBLIC_URL);
  const fe = norm(process.env.FRONTEND_URL);
  const app = norm(process.env.APP_URL);

  let SPA_URL;
  let API_PUBLIC_URL;

  if (apiEx) {
    API_PUBLIC_URL = apiEx;
    SPA_URL = norm(process.env.APP_URL || process.env.FRONTEND_URL) || `http://localhost:5173`;
  } else if (fe && app) {
    API_PUBLIC_URL = app;
    SPA_URL = fe;
  } else if (fe && !app) {
    SPA_URL = fe;
    API_PUBLIC_URL = `http://localhost:${port}`;
  } else if (app && !fe) {
    SPA_URL = app;
    API_PUBLIC_URL = `http://localhost:${port}`;
  } else {
    SPA_URL = `http://localhost:5173`;
    API_PUBLIC_URL = `http://localhost:${port}`;
  }

  return { SPA_URL, API_PUBLIC_URL };
}

/** Call after `dotenv.config()` (e.g. from server / middleware on each use is fine). */
export function getResolvedUrls() {
  return resolvePublicUrls();
}
