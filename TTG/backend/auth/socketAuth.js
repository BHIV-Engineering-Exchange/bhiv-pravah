// backend/auth/socketAuth.js
const { verifyToken } = require("./jwt");

function socketAuthMiddleware(socket, next) {
  const token = socket.handshake.auth?.token;
  const isSimulated = socket.handshake.auth?.simulated === true;

  // 🔐 Simulated agents must be explicit
  if (isSimulated) {
    if (typeof isSimulated !== 'boolean') {
      console.warn("[AUTH] Invalid simulated flag type");
      return next(new Error("INVALID_SIMULATED_FLAG"));
    }
    socket.userId = "SimulatedAgent";
    socket.role = "agent";
    socket.isSimulated = true;
    console.log("🧪 Simulated agent connected");
    return next();
  }

  // 🔒 Real users MUST have JWT
  if (!token) {
    console.warn("[AUTH] Missing JWT");
    return next(new Error("AUTH_REQUIRED"));
  }

  try {
    const decoded = verifyToken(token);
    if (!decoded?.sub) {
      return next(new Error("INVALID_TOKEN_PAYLOAD"));
    }

    socket.userId = decoded.sub;
    socket.role = Array.isArray(decoded.roles)
      ? decoded.roles[0]
      : "user";

    socket.user = decoded;
    socket.isSimulated = false;

    return next();

  } catch (err) {
    console.error("[AUTH] JWT rejected:", err.message);
    return next(new Error("INVALID_TOKEN"));
  }
}

module.exports = socketAuthMiddleware;
