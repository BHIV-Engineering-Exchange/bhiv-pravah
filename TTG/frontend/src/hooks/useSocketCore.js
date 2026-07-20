import { useEffect } from "react";
import socket from "../socket/socket";

export default function useSocketCore({
  setActionLog,
  setPresenceList,
  setAgentEvents,
  dispatchAgentEvent,
  setAgentNonces,
  setSignatureLog,
  setReplayAlerts,
  setHeartbeatStatus,
  setAuthContext,
  setCubeConfig,
}) {
  useEffect(() => {
    socket.on("action_update", action =>
      setActionLog(prev => [action, ...prev].slice(0, 200))
    );

    socket.on("agent_update", data => {
      setAgentEvents(prev => [data, ...prev].slice(0, 200));
      dispatchAgentEvent(data);
    });

    socket.on("agent_nonce", setAgentNonces);

    socket.on("action_error", err => {
      if (err?.error === "invalid_signature") {
        setSignatureLog(p => [{ ok: false, ts: Date.now() }, ...p]);
      }
      if (err?.error === "replay_detected") {
        setReplayAlerts(p => [{ ts: Date.now() }, ...p]);
      }
    });

    socket.on("agent_heartbeat_result", data => {
      setHeartbeatStatus(p => ({
        ...p,
        [data.agentId || "unknown"]: { ...data, ts: Date.now() }
      }));
    });

    socket.on("heartbeat_result", data => {
      setHeartbeatStatus(p => ({
        ...p,
        [data.userId || "unknown"]: { ...data, ts: Date.now() }
      }));
    });

    socket.on("presence_update", data => setPresenceList({ ...data }));
    socket.on("auth_context", setAuthContext);

    socket.on("world_update", (engineSchema) => {
      if (!engineSchema || typeof engineSchema !== 'object') {
        console.error("[SOCKET] Invalid world_update schema received");
        return;
      }
      
      // Extract cube preview data if present
      if (engineSchema._cubePreview) {
        setCubeConfig(engineSchema._cubePreview);
      } else {
        setCubeConfig(engineSchema);
      }
    });
 
    return () => {
      socket.removeAllListeners("action_update");
      socket.removeAllListeners("agent_update");
      socket.removeAllListeners("agent_nonce");
      socket.removeAllListeners("action_error");
      socket.removeAllListeners("agent_heartbeat_result");
      socket.removeAllListeners("heartbeat_result");
      socket.removeAllListeners("presence_update");
      socket.removeAllListeners("auth_context");
      socket.removeAllListeners("world_update");
    };
  }, []);
}
