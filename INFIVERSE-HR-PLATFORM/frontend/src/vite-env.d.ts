/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_AGENT_SERVICE_URL?: string
  readonly VITE_LANGGRAPH_SERVICE_URL?: string
  readonly VITE_ENABLE_CONTROL_CENTER?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
