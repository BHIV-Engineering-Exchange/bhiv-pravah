import logger from './logger.js';

/**
 * Normalize origin: trim, strip trailing slash.
 */
function norm(s) {
  if (!s || typeof s !== 'string') return '';
  return s.trim().replace(/\/$/, '');
}

/**
 * Split comma-separated env values into unique origins.
 */
function splitOrigins(value) {
  if (!value || typeof value !== 'string') return [];
  return value
    .split(',')
    .map(norm)
    .filter(Boolean);
}

/**
 * Build allowed browser origins for CORS (credentials: true → must echo exact Origin).
 */
export function buildAllowedOrigins({
  frontendUrl,
  appUrl,
  corsOrigin,
  corsAllowedOrigins,
  authServerUrl,
  allowLocalhostCors,
}) {
  const set = new Set();

  for (const o of [
    norm(frontendUrl),
    norm(appUrl),
    norm(authServerUrl),
    ...splitOrigins(corsOrigin),
    ...splitOrigins(corsAllowedOrigins),
  ]) {
    if (o) set.add(o);
  }

  if (allowLocalhostCors !== false && allowLocalhostCors !== 'false') {
    [
      'http://localhost:5173',
      'http://127.0.0.1:5173',
      'http://localhost:4173',
      'http://127.0.0.1:4173',
      'http://localhost:3000',
      'http://127.0.0.1:3000',
    ].forEach((h) => set.add(h));
  }

  const list = [...set];
  logger.info(`CORS: ${list.length} allowed origin(s) configured`);
  return list;
}
