import { useState, useReducer } from "react";
import { useNavigate } from "react-router-dom";

import "./index.css";

import ActionsPanel from "./components/ActionsPanel";
import ActionLogPanel from "./components/ActionLogPanel";
import PresencePanel from "./components/PresencePanel";
import AgentPanel from "./components/AgentPanel";
import CubePreview from "./components/CubePreview";
import JsonConfigPanel from "./components/JsonConfigPanel";
import JobQueuePanel from "./components/JobQueuePanel";
import SecurityPanel from "./components/SecurityPanel";
import UserPreferencePanel from "./components/UserPreferencePanel";
import DemoModePanel from "./components/DemoModePanel";
import IntentInputPanel from "./components/IntentInputPanel";
import GameTelemetryPanel from "./components/GameTelemetryPanel";
import ExecutionMonitor from "./components/ExecutionMonitor";
import NicaiPanel from "./components/NicaiPanel";
import SamruddhiPanel from "./components/SamruddhiPanel";
import SimModal from "./components/SimRenderer/SimModal";

import { agentsReducer, initialAgentsState } from "./state/agentsReducer";

import useJwtAuth from "./hooks/useJwtAuth";
import useIdlePresence from "./hooks/useIdlePresence";
import useHeartbeat from "./hooks/useHeartbeat";
import useJobQueue from "./hooks/useJobQueue";
import useSocketCore from "./hooks/useSocketCore";

function App() {
  const navigate = useNavigate();

  const [status, setStatus] = useState("active");
  const [presenceList, setPresenceList] = useState({});
  const [actionLog, setActionLog] = useState([]);
  const [jobHistory, setJobHistory] = useState([]);
  const [agentEvents, setAgentEvents] = useState([]);
  const [engineStatus, setEngineStatus] = useState(null);
  const [lastTelemetry, setLastTelemetry] = useState(null);

  const [agentNonces, setAgentNonces] = useState({});
  const [signatureLog, setSignatureLog] = useState([]);
  const [replayAlerts, setReplayAlerts] = useState([]);
  const [heartbeatStatus, setHeartbeatStatus] = useState({});
  const [authContext, setAuthContext] = useState(null);

  const [previewConfig, setPreviewConfig] = useState({
    color: "#66ffdd",
    size: 1,
  });

  const [cubeConfig, setCubeConfig] = useState({
    schema_version: "1.0",
    world: { id: "world_default", name: "Default", gravity: [0, -9.8, 0] },
    scene: { id: "scene_default", ambientLight: [1, 1, 1], skybox: "default" },
    entities: [{
      id: "cube_01",
      type: "object",
      transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
      material: { shader: "standard", texture: "none", color: [0.4, 1, 0.87] },
      components: { mesh: "cube", collider: "box", script: "" }
    }],
    quests: []
  });

  // Sim modal state — open over dashboard without unmounting it
  const [simModal, setSimModal] = useState({
    open: false, simResult: null, fromPrompt: null, compiledSchema: null
  });

  const [agents, dispatchAgentEvent] = useReducer(
    agentsReducer,
    initialAgentsState
  );

  useJwtAuth();
  useIdlePresence(status, setStatus);
  useHeartbeat();
  useJobQueue(setJobHistory, setEngineStatus, setLastTelemetry, (simResult, fromPrompt, compiledSchema) => {
    setSimModal({ open: true, simResult, fromPrompt, compiledSchema });
  });

  useSocketCore({
    setActionLog,
    setPresenceList,
    setAgentEvents,
    dispatchAgentEvent,
    setAgentNonces,
    setSignatureLog,
    setReplayAlerts,
    setHeartbeatStatus,
    setAuthContext,
    setCubeConfig: (engineSchema) => {
      setCubeConfig(engineSchema);
    },
  });

  return (
    <div className="min-h-screen">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -left-20 h-80 w-80 rounded-full bg-sky-500/25 blur-3xl" />
        <div className="absolute -top-20 right-0 h-96 w-96 rounded-full bg-violet-500/25 blur-3xl" />
        <div className="absolute bottom-[-6rem] left-1/3 h-96 w-96 rounded-full bg-indigo-500/20 blur-3xl" />
      </div>

      <div
        className={[
          "app-root relative mx-auto max-w-[1400px]",
          "px-4 sm:px-6 lg:px-8 py-10 sm:py-12",
          "font-['Poppins','Inter','Segoe_UI',sans-serif]",
          "transition-all duration-300",
        ].join(" ")}
      >
        <div
          className={[
            "relative z-10 mb-8",
            "flex flex-col md:flex-row md:items-center items-start",
            "justify-between gap-4",
          ].join(" ")}
        >
          <div>
            <h1
              className="
                text-[28px] md:text-[42px] font-bold tracking-tight
                bg-gradient-to-br from-sky-400 via-violet-400 to-cyan-400
                bg-clip-text text-transparent
                drop-shadow-[0_0_24px_rgba(56,189,248,0.35)]
              "
            >
              TTG - Dashboard
            </h1>
          </div>

          <div className="flex gap-3 flex-wrap">
            <button
              onClick={() => navigate("/simulate")}
              className="
                relative z-10 w-full md:w-auto
                px-6 py-3 rounded-2xl font-semibold text-white
                bg-gradient-to-br from-indigo-500 to-violet-500
                shadow-lg shadow-indigo-500/30
                transition-all duration-300
                hover:-translate-y-0.5 hover:scale-[1.02]
                active:scale-[0.98]
                flex items-center justify-center gap-2
              "
            >
              <span>🧪</span>
              <span>Open User Simulator (2 Users)</span>
            </button>
          </div>
        </div>

        <div className="relative z-10 mb-6 grid gap-6 grid-cols-1 md:grid-cols-2">
          <IntentInputPanel
            onGameGenerated={setCubeConfig}
            engineStatus={engineStatus}
            userId={authContext?.userId}
            onSimulate={(simResult, fromPrompt, compiledSchema) =>
              setSimModal({ open: true, simResult, fromPrompt, compiledSchema })
            }
          />
          <GameTelemetryPanel />
        </div>

        <div
          className="
            relative z-10
            grid gap-6
            grid-cols-1
            sm:grid-cols-1
            md:grid-cols-2
            xl:grid-cols-3
          "
        >
          <DemoModePanel />

          <CubePreview config={cubeConfig} />

          <JsonConfigPanel
            previewConfig={previewConfig}
            onConfigChange={setPreviewConfig}
          />

          <JobQueuePanel
            jobHistory={jobHistory}
            setJobHistory={setJobHistory}
            engineStatus={engineStatus}
            lastTelemetry={lastTelemetry}
          />

          <ExecutionMonitor />

          {authContext?.role === "admin" && (
            <SecurityPanel
              agentNonces={agentNonces}
              signatureLog={signatureLog}
              replayAlerts={replayAlerts}
              heartbeatStatus={heartbeatStatus}
            />
          )}

          <ActionsPanel compactMode={false} soundEnabled={true} />

          <AgentPanel agents={agents} recentEvents={agentEvents} />

          <ActionLogPanel actionLog={actionLog} />

          <PresencePanel presenceList={presenceList} />

          <NicaiPanel />

          <SamruddhiPanel />

          <UserPreferencePanel />
        </div>
      </div>

      {/* Sim Modal — renders over dashboard without unmounting it */}
      {simModal.open && (
        <SimModal
          simResult={simModal.simResult}
          fromPrompt={simModal.fromPrompt}
          compiledSchema={simModal.compiledSchema}
          onClose={() => setSimModal({ open: false, simResult: null, fromPrompt: null, compiledSchema: null })}
        />
      )}
    </div>
  );
}

export default App;
