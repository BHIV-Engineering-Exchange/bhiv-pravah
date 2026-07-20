const express = require("express");
const router = express.Router();

const { createToken } = require("../auth/jwt");

router.post("/token", (req, res) => {
  const { userId } = req.body || {};

  if (!userId) return res.status(400).json({ error: "userId required" });

  // TEMPORARY role assignment 
  let role = "user";

  // Example: simple admin allowlist
  const ADMIN_USERS = ["admin", "testadmin", "root"];

  if (ADMIN_USERS.includes(userId)) {
    role = "admin";
  }

  const token = createToken(userId, [role]);

  res.json({ token });
});

router.get("/engine-token", (req, res) => {
  const jwt = require('jsonwebtoken');
  
  const token = jwt.sign(
    { 
      engineId: 'atharva_engine_01',
      role: 'engine'
    },
    process.env.JWT_SECRET,
    { 
      expiresIn: '365d',
      issuer: 'sovereign-core'
    }
  );
  
  res.json({ 
    token,
    engineId: 'atharva_engine_01',
    expiresIn: '365 days',
    usage: 'Use this token to connect engine to /engine namespace'
  });
});

router.get("/static-user-token", (req, res) => {
  const jwt = require('jsonwebtoken');
  
  const token = jwt.sign(
    { 
      sub: 'user_static_demo',
      roles: ['user']
    },
    process.env.JWT_SECRET,
    { 
      expiresIn: '365d',
      issuer: process.env.JWT_ISSUER || 'microbridge.internal'
    }
  );
  
  res.json({ 
    token,
    userId: 'user_static_demo',
    expiresIn: '365 days',
    usage: 'Permanent user token for dashboard access'
  });
});

module.exports = router;
