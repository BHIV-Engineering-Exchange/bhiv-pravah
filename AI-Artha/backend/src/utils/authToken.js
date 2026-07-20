import jwt from 'jsonwebtoken';

/**
 * Access token for API requests (Authorization: Bearer).
 * Payload shape matches what `protect` middleware decodes.
 */
export function signAccessToken(user) {
  const appId = process.env.APP_ID || process.env.BHIV_APP_ID;
  const payload = {
    user_id: user._id.toString(),
    email: user.email,
    name: user.name,
    roles: [user.role],
    allowedApps: appId ? [appId] : [],
  };
  return jwt.sign(payload, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  });
}
