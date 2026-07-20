import { useEffect } from "react";
import socket from "../socket/socket";

export default function useHeartbeat() {
  useEffect(() => {
    const interval = setInterval(() => {
      socket.emit("heartbeat", { ts: Date.now() });
    }, 30000);

    return () => clearInterval(interval);
  }, []);
}
