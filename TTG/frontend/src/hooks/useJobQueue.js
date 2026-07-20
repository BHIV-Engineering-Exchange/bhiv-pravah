import { useEffect } from "react";
import socket from "../socket/socket";

export default function useJobQueue(setJobHistory, setEngineStatus, setLastTelemetry, onSimResult) {
  useEffect(() => {
    function onJobStatus(job) {
      setJobHistory(prev => {
        const idx = prev.findIndex(j => j.id === job.jobId);
        if (idx >= 0) {
          const updated = [...prev];
          updated[idx] = { ...updated[idx], ...job, id: job.jobId };
          return updated;
        }
        return [{ ...job, id: job.jobId }, ...prev];
      });
    }

    function onEngineStatus(status) {
      if (setEngineStatus) setEngineStatus(status);
    }

    function onEngineTelemetry(telemetry) {
      if (setLastTelemetry) setLastTelemetry(telemetry);
    }

    function onSimResultEvent(data) {
      if (onSimResult && data?.simResult) {
        onSimResult(data.simResult, data.from_prompt || null, null);
      }
    }

    socket.on("job_status",      onJobStatus);
    socket.on("engine_status",   onEngineStatus);
    socket.on("engine_telemetry",onEngineTelemetry);
    socket.on("sim_result",      onSimResultEvent);

    return () => {
      socket.off("job_status",      onJobStatus);
      socket.off("engine_status",   onEngineStatus);
      socket.off("engine_telemetry",onEngineTelemetry);
      socket.off("sim_result",      onSimResultEvent);
    };
  }, [setJobHistory, setEngineStatus, setLastTelemetry, onSimResult]);
}
