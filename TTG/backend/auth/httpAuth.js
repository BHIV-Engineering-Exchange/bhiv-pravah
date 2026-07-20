const jwt = require("./jwt");

function verifyJwtMiddleware(requiredRoles = []) {
  return (req, res, next) => {
    const auth = req.headers.authorization;
    if (!auth || !auth.startsWith("Bearer "))
      return res.status(401).send("Missing token");

    const token = auth.slice(7);

    try {
      const decoded = jwt.verifyToken(token);

      if (requiredRoles.length && !requiredRoles.some(r => decoded.roles.includes(r))) {
        return res.status(403).send("Forbidden");
      }

      req.user = decoded;
      next();
    } catch (err) {
      return res.status(401).send("Invalid or expired token");
    }
  };
}

module.exports = { verifyJwtMiddleware };
