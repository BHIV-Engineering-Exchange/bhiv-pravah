const express = require("express");
const cors = require("cors");

const authRoutes = require("./routes/authRoutes");
const ActionEvent = require("./models/ActionEvent");
const { verifyToken } = require("./auth/jwt");
const { setEngineConnected } = require("./jobQueue");

const app = express();

app.use(cors({
  origin: "http://localhost:5173",
  credentials: true
}));
app.use(express.json());

// AUTH
app.use("/auth", authRoutes);

// ADMIN MIDDLEWARE
function requireAdminHttp(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader) return res.status(401).json({ error: "missing_token" });

  const token = authHeader.split(" ")[1];
  try {
    const decoded = verifyToken(token);
    if (!decoded.roles || !decoded.roles.includes("admin")) {
      return res.status(403).json({ error: "admin_only" });
    }
    next();
  } catch {
    return res.status(401).json({ error: "invalid_token" });
  }
}

// HEALTH
app.get("/health", (req, res) => {
  res.json({ status: "ok", ts: Date.now() });
});

// SECURITY STATUS
app.get("/security/status", requireAdminHttp, (req, res) => {
  res.json({ ok: true, ts: Date.now() });
});

// ACTION LOG
app.get("/actions", requireAdminHttp, async (req, res) => {
  const actions = await ActionEvent
    .find({})
    .sort({ serverTs: -1 })
    .limit(200);
  res.json(actions);
});

// ENGINE CONTROL (for testing failures)
app.post("/engine/disconnect", requireAdminHttp, (req, res) => {
  setEngineConnected(false);
  res.json({ ok: true, message: "Engine disconnected" });
});

app.post("/engine/reconnect", requireAdminHttp, (req, res) => {
  setEngineConnected(true);
  res.json({ ok: true, message: "Engine reconnected" });
});

module.exports = app;
