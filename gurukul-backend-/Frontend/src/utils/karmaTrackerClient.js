// Karma Tracker is now integrated into backend - use same URL as the main API.
// In dev we use localhost, in production we default to the Gurukul backend on Render.
const KARMA_TRACKER_URL =
  import.meta.env.VITE_KARMA_TRACKER_URL ||
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? 'http://localhost:3000' : 'https://gurukul-up9j.onrender.com');

/**
 * Send a life_event to Karma Tracker.
 * This is backend-only karma; it does not touch any local frontend state.
 *
 * @param {Object} params
 * @param {string} params.userId - Stable user id
 * @param {string} params.action - Karma action (e.g. completing_lessons, solving_doubts, cheat)
 * @param {string} [params.role] - Optional role label (default: learner)
 * @param {string} [params.note] - Optional human-readable note
 * @param {string} [params.context] - Optional context string
 */
export async function sendLifeEvent({ userId, action, role = 'learner', note, context }) {
  if (!userId || !action) {
    return;
  }

  // Send flat payload format expected by /api/v1/karma/ (log_action endpoint)
  const payload = {
    user_id: userId,
    action,
    role,
    ...(context ? { context } : {}),
    ...(note ? { note } : {})
  };

  try {
    const response = await fetch(`${KARMA_TRACKER_URL}/api/v1/karma/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(5000) // Increased timeout to 5 seconds
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.warn('[KARMA] life_event failed:', response.status, response.statusText, errorText);
      throw new Error(`Karma Tracker returned ${response.status}: ${errorText}`);
    }
    
    const result = await response.json();
    console.log('[KARMA] life_event sent successfully:', result);
    return result;
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.warn('[KARMA] life_event send error (non-blocking):', error.message);
    }
    throw error; // Re-throw so caller can handle it
  }
}


