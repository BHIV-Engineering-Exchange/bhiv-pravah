import { io } from "socket.io-client";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:3000";

class SocketManager {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.connectionState = "disconnected";
    this.listeners = new Map();
  }

  connect() {
    const token = localStorage.getItem("token");
    
    if (!token) {
      console.warn("[SOCKET] No token - not connecting");
      return;
    }

    this.socket = io(BACKEND_URL, {
      autoConnect: true,
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: this.maxReconnectDelay,
      timeout: 20000,
      auth: { token }
    });

    this.setupEventHandlers();
    window.__socket = this.socket;
  }

  setupEventHandlers() {
    this.socket.on("connect", () => {
      this.connectionState = "connected";
      this.reconnectAttempts = 0;
      console.log("[SOCKET] Connected:", this.socket.id);
      this.emit("connection_state", { state: "connected" });
    });

    this.socket.on("disconnect", (reason) => {
      this.connectionState = "disconnected";
      console.warn("[SOCKET] Disconnected:", reason);
      this.emit("connection_state", { state: "disconnected", reason });

      if (reason === "io server disconnect") {
        // Server forced disconnect - try to reconnect
        this.reconnect();
      }
    });

    this.socket.on("connect_error", (error) => {
      this.connectionState = "error";
      this.reconnectAttempts++;
      
      console.error(`[SOCKET] Connection error (attempt ${this.reconnectAttempts}):`, error.message);
      this.emit("connection_state", { 
        state: "error", 
        error: error.message,
        attempt: this.reconnectAttempts 
      });

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error("[SOCKET] Max reconnection attempts reached");
        this.emit("connection_state", { state: "failed" });
      }
    });

    this.socket.on("reconnect", (attemptNumber) => {
      this.connectionState = "connected";
      this.reconnectAttempts = 0;
      console.log(`[SOCKET] Reconnected after ${attemptNumber} attempts`);
      this.emit("connection_state", { state: "reconnected", attempts: attemptNumber });
    });

    this.socket.on("reconnect_attempt", (attemptNumber) => {
      this.connectionState = "reconnecting";
      console.log(`[SOCKET] Reconnection attempt ${attemptNumber}`);
      this.emit("connection_state", { state: "reconnecting", attempt: attemptNumber });
    });

    this.socket.on("reconnect_failed", () => {
      this.connectionState = "failed";
      console.error("[SOCKET] Reconnection failed");
      this.emit("connection_state", { state: "failed" });
    });
  }

  reconnect() {
    if (this.socket && this.connectionState !== "connected") {
      const delay = Math.min(
        this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
        this.maxReconnectDelay
      );

      console.log(`[SOCKET] Reconnecting in ${delay}ms...`);
      
      setTimeout(() => {
        this.socket.connect();
      }, delay);
    }
  }

  refreshAuth() {
    const token = localStorage.getItem("token");
    if (this.socket && token) {
      this.socket.auth = { token };
      if (!this.socket.connected) {
        this.socket.connect();
      }
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.connectionState = "disconnected";
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback);
    }

    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn(`[SOCKET] Cannot emit ${event} - not connected`);
    }
  }

  getState() {
    return {
      connected: this.socket?.connected || false,
      state: this.connectionState,
      attempts: this.reconnectAttempts
    };
  }
}

const socketManager = new SocketManager();

export function refreshSocketAuth() {
  socketManager.refreshAuth();
}

export function getSocketState() {
  return socketManager.getState();
}

export default socketManager.socket || socketManager;
