const jwt = require("jsonwebtoken");
const fs = require("fs");
const path = require("path");

const ROTATION_LOG = path.join(__dirname, "../logs/jwt_rotation.log");

class JWTRotationManager {
  constructor() {
    this.currentSecret = process.env.JWT_SECRET;
    this.previousSecret = null;
    this.rotationDate = null;
    this.gracePeriod = 24 * 60 * 60 * 1000; // 24 hours
  }

  // Rotate to new secret with grace period
  rotateSecret(newSecret) {
    this.previousSecret = this.currentSecret;
    this.currentSecret = newSecret;
    this.rotationDate = Date.now();

    this.log({
      event: "SECRET_ROTATED",
      timestamp: new Date().toISOString(),
      gracePeriodHours: 24
    });

    console.log("[JWT] Secret rotated. Grace period: 24h");
  }

  // Verify token with fallback to previous secret
  verifyToken(token) {
    try {
      return jwt.verify(token, this.currentSecret);
    } catch (err) {
      if (this.previousSecret && this.isInGracePeriod()) {
        try {
          const decoded = jwt.verify(token, this.previousSecret);
          this.log({
            event: "TOKEN_VERIFIED_WITH_OLD_SECRET",
            timestamp: new Date().toISOString(),
            userId: decoded.userId
          });
          return decoded;
        } catch (fallbackErr) {
          throw err;
        }
      }
      throw err;
    }
  }

  // Check if still in grace period
  isInGracePeriod() {
    if (!this.rotationDate) return false;
    return Date.now() - this.rotationDate < this.gracePeriod;
  }

  // Generate new token
  generateToken(payload, expiresIn = "1h") {
    return jwt.sign(payload, this.currentSecret, {
      expiresIn,
      issuer: process.env.JWT_ISSUER || "sovereign-core"
    });
  }

  // Refresh token if expiring soon
  refreshIfNeeded(token, threshold = 5 * 60 * 1000) {
    try {
      const decoded = this.verifyToken(token);
      const expiresIn = decoded.exp * 1000 - Date.now();

      if (expiresIn < threshold) {
        const newToken = this.generateToken({
          userId: decoded.userId,
          role: decoded.role
        });

        this.log({
          event: "TOKEN_REFRESHED",
          timestamp: new Date().toISOString(),
          userId: decoded.userId,
          oldExpiry: new Date(decoded.exp * 1000).toISOString()
        });

        return { refreshed: true, token: newToken };
      }

      return { refreshed: false, token };
    } catch (err) {
      throw new Error("Token refresh failed: " + err.message);
    }
  }

  log(entry) {
    const logDir = path.dirname(ROTATION_LOG);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    fs.appendFileSync(ROTATION_LOG, JSON.stringify(entry) + "\n");
  }
}

const jwtRotation = new JWTRotationManager();

module.exports = { jwtRotation };
