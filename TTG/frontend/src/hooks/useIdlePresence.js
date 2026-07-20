import { useEffect, useRef } from "react";
import socket from "../socket/socket";

export default function useIdlePresence(status, setStatus) {
  const lastActiveTime = useRef(Date.now());

  useEffect(() => {
    const handleActivity = () => {
      if (status !== "active") {
        setStatus("active");
        socket.emit("presence", "active");
      }
      lastActiveTime.current = Date.now();
    };

    window.addEventListener("mousemove", handleActivity);
    window.addEventListener("keydown", handleActivity);

    const idleCheck = setInterval(() => {
      if (Date.now() - lastActiveTime.current > 5000 && status !== "idle") {
        setStatus("idle");
        socket.emit("presence", "idle");
      }
    }, 1000);

    return () => {
      window.removeEventListener("mousemove", handleActivity);
      window.removeEventListener("keydown", handleActivity);
      clearInterval(idleCheck);
    };
  }, [status]);
}
