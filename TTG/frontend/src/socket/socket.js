import { io } from "socket.io-client";
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

function getToken() {
  return localStorage.getItem("token");
}

const socket = io(BACKEND_URL, {
  autoConnect: false,
  transports: ["websocket"],
  auth: {
    token: getToken(),
  },
});

// expose socket for debugging
window.__socket = socket;

export function refreshSocketAuth() {
  const token = getToken();
  socket.auth = { token };

  if (!token) {
    console.warn("[SOCKET] No token — not connecting");
    return;
  }

  if (!socket.connected) {
    socket.connect();
  }
}

export default socket;
