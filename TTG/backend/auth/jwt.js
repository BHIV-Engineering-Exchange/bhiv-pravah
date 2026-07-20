const jwt = require("jsonwebtoken");
const { JWT_SECRET, JWT_ISSUER, JWT_EXP } = require("../config");

function createToken(userId, roles = "user") {
  const payload = {
    sub: userId,  
    roles,  
  };

  return jwt.sign(payload, JWT_SECRET, {
    issuer: JWT_ISSUER,
    expiresIn: JWT_EXP,
  });
}

function verifyToken(token) {
  return jwt.verify(token, JWT_SECRET, {
    issuer: JWT_ISSUER
  });
}

module.exports = {
  createToken,
  verifyToken,
};
