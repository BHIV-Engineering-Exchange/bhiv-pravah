package main

// AgentInfo represents an agent identity from the Agent Registry.
type AgentInfo struct {
	AgentID           string
	AgentRole         string
	ClassificationMax string // Clearance ceiling (L0-L4)
	Status            string // ACTIVE, SUSPENDED, REVOKED, TERMINATED
}

// ResourceInfo represents a resource identity from the Resource Registry.
type ResourceInfo struct {
	ResourceID     string
	ResourceType   string
	Classification string // Truth classification (L0-L4)
}

// RegistryInterface provides deterministic stubs for Agent and Resource lookup.
// In production, these query canonical registries. No network. No cache. No side effects.
type RegistryInterface struct {
	agents    map[string]*AgentInfo
	resources map[string]*ResourceInfo
}

// NewRegistryInterface creates the registry with deterministic stub data.
func NewRegistryInterface() *RegistryInterface {
	return &RegistryInterface{
		agents: map[string]*AgentInfo{
			// Governance agents - L4 clearance (constitutional layer)
			"gov-agent-001":   {"gov-agent-001", "governance_agent", "L4", "ACTIVE"},
			"gov-agent-002":   {"gov-agent-002", "governance_agent", "L4", "ACTIVE"},
			// Standard agents - L2 clearance (sensitive internal)
			"std-agent-001":   {"std-agent-001", "standard_agent", "L2", "ACTIVE"},
			"std-agent-002":   {"std-agent-002", "standard_agent", "L2", "ACTIVE"},
			"std-agent-003":   {"std-agent-003", "standard_agent", "L1", "ACTIVE"},
			// Audit agents - L4 clearance (can read all decision traces)
			"audit-agent-001": {"audit-agent-001", "audit_agent", "L4", "ACTIVE"},
			"audit-agent-002": {"audit-agent-002", "audit_agent", "L4", "ACTIVE"},
			// Safety monitors - L3 clearance (governance-critical)
			"safety-mon-001":  {"safety-mon-001", "safety_monitor", "L3", "ACTIVE"},
			// Data processors - L1 clearance (operational data only)
			"data-proc-001":   {"data-proc-001", "data_processor", "L1", "ACTIVE"},
			"data-proc-002":   {"data-proc-002", "data_processor", "L1", "ACTIVE"},
			// Orchestrators - L2 clearance (limited scope)
			"orch-001":        {"orch-001", "orchestrator", "L2", "ACTIVE"},
			// Lifecycle test agents
			"suspended-agent": {"suspended-agent", "standard_agent", "L2", "SUSPENDED"},
			"revoked-agent":   {"revoked-agent", "standard_agent", "L2", "REVOKED"},
			"terminated-agent":{"terminated-agent", "standard_agent", "L2", "TERMINATED"},
		},
		resources: map[string]*ResourceInfo{
			// L4 - Constitutional truth layer
			"policy-reg-001":  {"policy-reg-001", "policy_registry", "L4"},
			"policy-reg-002":  {"policy-reg-002", "policy_registry", "L4"},
			// L3 - Governance-critical data
			"agent-reg-001":   {"agent-reg-001", "agent_registry", "L3"},
			"trace-001":       {"trace-001", "decision_trace", "L3"},
			"trace-002":       {"trace-002", "decision_trace", "L3"},
			"model-reg-001":   {"model-reg-001", "model_registry", "L3"},
			"audit-log-001":   {"audit-log-001", "audit_log", "L3"},
			// L2 - Sensitive internal data
			"config-001":      {"config-001", "configuration", "L2"},
			"config-002":      {"config-002", "configuration", "L2"},
			// L1 - Internal operational data
			"ops-data-001":    {"ops-data-001", "operational_data", "L1"},
			"ops-data-002":    {"ops-data-002", "operational_data", "L1"},
			"analytics-001":   {"analytics-001", "analytics", "L1"},
			// L0 - Public information
			"public-api-001":  {"public-api-001", "public_api", "L0"},
		},
	}
}

// GetAgent returns agent info or nil if not found. Nil causes PDP to DENY (fail-closed).
func (ri *RegistryInterface) GetAgent(agentID string) *AgentInfo {
	return ri.agents[agentID]
}

// GetResource returns resource info or nil if not found. Nil causes PDP to DENY (fail-closed).
func (ri *RegistryInterface) GetResource(resourceID string) *ResourceInfo {
	return ri.resources[resourceID]
}

// GetAllAgents returns the full agent map for determinism verification.
func (ri *RegistryInterface) GetAllAgents() map[string]*AgentInfo {
	return ri.agents
}

// GetAllResources returns the full resource map for determinism verification.
func (ri *RegistryInterface) GetAllResources() map[string]*ResourceInfo {
	return ri.resources
}
