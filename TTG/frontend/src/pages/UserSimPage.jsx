import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import io from "socket.io-client";
import CryptoJS from "crypto-js";
import "./UserSimPage.css"; 
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

// UTIL: SIGN ACTION

function signAction(type, payload) {
  try {
    const ts = Date.now();
    const nonce = Math.random().toString(36).substring(2, 12);
    const message = `${type}|${JSON.stringify(payload)}|${ts}|${nonce}`;
    const sig = CryptoJS.HmacSHA256(
      message,
      "HMAC_SECRET_987654321"
    ).toString(CryptoJS.enc.Hex);

    return { ts, nonce, sig };
  } catch (err) {
    console.error("[SIM] Signature generation failed:", err.message);
    throw new Error("Failed to sign action");
  }
}


// COMPONENT FOR EACH SIM USER

function SimUser({ label, userId }) {
  const [log, setLog] = useState([]);
  const [agents, setAgents] = useState([]);
  const [presence, setPresence] = useState("active");

  const socketRef = useRef(null);
  const lastActiveTime = useRef(Date.now());


  // INIT: Fetch User Token

  useEffect(() => {
    let socket;
  
    async function init() {
      const res = await fetch(`${BACKEND_URL}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId }),
      });
  
      const { token } = await res.json();
  
      socket = io(`${BACKEND_URL}`, {
        auth: { token },
        transports: ["websocket"],
      });
  
      socketRef.current = socket;
  
      socket.on("connect", () =>
        appendLog(`Connected as ${userId} (socket=${socket.id})`)
      );
  
      socket.on("action_update", (a) => {
        appendLog(`Action: ${a.type}`);
      });
  
      socket.on("agent_update", (a) => {
        appendLog(`Agent → ${a.agent}: ${a.message}`);
        setAgents((prev) => [a, ...prev].slice(0, 20));
      });
  
      socket.on("hint_deprioritized", (a) => {
        appendLog(`Hint Deprioritized → lockedFor = ${a.lockedFor}`);
        setAgents((prev) => [
          { agent: "HintAgent", reason: "spam_collision", ...a },
          ...prev,
        ]);
      });
  
      socket.on("nav_idle_prompt", () => {
        appendLog("NavAgent: Idle Timeout Triggered");
        setAgents((prev) => [
          {
            agent: "NavAgent",
            reason: "idle_timeout",
            message: "Idle detected by server",
          },
          ...prev,
        ]);
      });
    }
  
    init();
  
    return () => {
      if (socket) {
        socket.disconnect();
        socket = null;
      }
    };
  }, [userId]);
  

  // HELPER: ADD LOG LINE

  const appendLog = (txt) => {
    setLog((prev) => [txt, ...prev].slice(0, 30));
  };


  // SEND ACTIONS

  const sendAction = (type, payload) => {
    const s = socketRef.current;
    if (!s) return;

    const { ts, nonce, sig } = signAction(type, payload);
    s.emit("action", { type, payload, ts, nonce, sig });
  };


  // AUTO-IDLE BEHAVIOR

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const s = socketRef.current;

      if (!s) return;

      if (now - lastActiveTime.current > 5000 && presence !== "idle") {
        setPresence("idle");
        s.emit("presence", "idle");
        appendLog("Auto Idle Triggered");
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [presence]);

  const markActive = () => {
    const s = socketRef.current;
    if (!s) return;

    lastActiveTime.current = Date.now();

    if (presence !== "active") {
      setPresence("active");
      s.emit("presence", "active");
      appendLog("Marked Active");
    }
  };

 
  // UI

  return (
    <div
      className="sim-user"
      onMouseMove={markActive}
      onKeyDown={markActive}
      tabIndex={0}
    >
      <div className="user-header">
        <h3>{label}</h3>
        <span className={`status-badge ${presence}`}>
          {presence === "active" ? "🟢" : "🟡"} {presence.toUpperCase()}
        </span>
      </div>
      <p className="user-id">{userId}</p>

      <div className="section">
        <h4>Actions</h4>
        <div className="btns">
          <button onClick={() => sendAction("click", null)}>
            👆 Click
          </button>
          <button onClick={() => sendAction("interact", null)}>
            🤝 Interact
          </button>
          <button onClick={() => sendAction("inspect", null)}>
            🔍 Inspect
          </button>
          <button onClick={() => sendAction("speak", "hello")}>
            💬 Speak
          </button>
          <button
            className="spam-btn"
            onClick={() => {
              for (let i = 0; i < 5; i++) {
                setTimeout(() => sendAction("click", null), i * 70);
              }
            }}
          >
            ⚡ Spam Click x5
          </button>
          <button
            className="idle-btn"
            onClick={() => socketRef.current.emit("presence", "idle")}
          >
            😴 Force Idle
          </button>
        </div>
      </div>

      <div className="section">
        <h4>🤖 Agent Events</h4>
        <div className="agent-list">
          {agents.length === 0 ? (
            <div className="empty-state">No agent events yet</div>
          ) : (
            agents.map((a, i) => (
              <div key={i} className="agent-item">
                <span className="agent-name">{a.agent}</span>
                <span className="agent-msg">{a.message || a.reason}</span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="section">
        <h4>📋 Activity Logs</h4>
        <div className="log-box">
          {log.length === 0 ? (
            <div className="empty-state">No logs yet</div>
          ) : (
            log.map((l, i) => (
              <div key={i} className="log-line">
                <span className="log-bullet">▸</span> {l}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}


// MAIN PAGE: SHOW TWO USERS

export default function UserSimPage() {
  const navigate = useNavigate();

  return (
    <div className="sim-page-container">
      <button className="home-btn" onClick={() => navigate("/")}>
        🏠 Back to Dashboard
      </button>

      <h1 className="sim-title">User Simulator - Real-Time Testing</h1>
      <p className="sim-subtitle">
        Interact with two simultaneous user sessions and observe agent behaviors in real-time
      </p>

      <div className="sim-grid">
        <SimUser label="USER A" userId="userA" />
        <SimUser label="USER B" userId="userB" />
      </div>
    </div>
  );
}

