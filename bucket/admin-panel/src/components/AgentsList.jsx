import React, { useState, useEffect } from "react";
import ApiService from "../services/api";
import AgentRunner from "./AgentRunner";
import "./AgentsList.css";

const AgentsList = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [runningAgent, setRunningAgent] = useState(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const data = await ApiService.fetchAgents();
      setAgents(data);
      setError(null);
    } catch (err) {
      setError("Failed to fetch agents: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAgentClick = (agent) => {
    setSelectedAgent(selectedAgent?.name === agent.name ? null : agent);
  };

  const handleRunAgent = (agent, event) => {
    event.stopPropagation(); // Prevent card expansion
    setRunningAgent(agent);
  };

  const handleCloseRunner = () => {
    setRunningAgent(null);
  };

  const formatCapabilities = (capabilities) => {
    if (!capabilities) return "None";
    return Object.entries(capabilities)
      .map(([key, value]) => `${key}: ${value}`)
      .join(", ");
  };

  const formatSchema = (schema) => {
    if (!schema) return "Not specified";
    return JSON.stringify(schema, null, 2);
  };

  if (loading) {
    return (
      <div className="agents-container">
        <div className="loading">Loading agents...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="agents-container">
        <div className="error">
          {error}
          <button onClick={fetchAgents} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="agents-container">
      <div className="agents-header">
        <h2>Available Agents ({agents.length})</h2>
        <button onClick={fetchAgents} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      <div className="agents-grid">
        {agents.map((agent, index) => (
          <div
            key={agent.name || index}
            className={`agent-card ${
              selectedAgent?.name === agent.name ? "selected" : ""
            }`}
            onClick={() => handleAgentClick(agent)}
          >
            <div className="agent-header">
              <div className="agent-title-section">
                <h3>{agent.name || "Unnamed Agent"}</h3>
                <div className="agent-domains">
                  {agent.domains?.map((domain, idx) => (
                    <span key={idx} className="domain-tag">
                      {domain}
                    </span>
                  ))}
                </div>
              </div>
              <button
                className="run-agent-btn"
                onClick={(e) => handleRunAgent(agent, e)}
                title="Run this agent"
              >
                ▶ Run
              </button>
            </div>

            <div className="agent-info">
              <div className="info-row">
                <strong>Capabilities:</strong>
                <span>{formatCapabilities(agent.capabilities)}</span>
              </div>

              {agent.module_path && (
                <div className="info-row">
                  <strong>Module:</strong>
                  <span className="module-path">{agent.module_path}</span>
                </div>
              )}
            </div>

            {selectedAgent?.name === agent.name && (
              <div className="agent-details">
                <div className="schema-section">
                  <h4>Input Schema</h4>
                  <pre className="schema-code">
                    {formatSchema(agent.input_schema)}
                  </pre>
                </div>

                <div className="schema-section">
                  <h4>Output Schema</h4>
                  <pre className="schema-code">
                    {formatSchema(agent.output_schema)}
                  </pre>
                </div>

                {agent.sample_input && (
                  <div className="schema-section">
                    <h4>Sample Input</h4>
                    <pre className="schema-code">
                      {JSON.stringify(agent.sample_input, null, 2)}
                    </pre>
                  </div>
                )}

                {agent.sample_output && (
                  <div className="schema-section">
                    <h4>Sample Output</h4>
                    <pre className="schema-code">
                      {JSON.stringify(agent.sample_output, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {agents.length === 0 && (
        <div className="no-data">
          No agents found. Make sure the backend is running and agents are
          properly configured.
        </div>
      )}

      {runningAgent && (
        <AgentRunner agent={runningAgent} onClose={handleCloseRunner} />
      )}
    </div>
  );
};

export default AgentsList;
