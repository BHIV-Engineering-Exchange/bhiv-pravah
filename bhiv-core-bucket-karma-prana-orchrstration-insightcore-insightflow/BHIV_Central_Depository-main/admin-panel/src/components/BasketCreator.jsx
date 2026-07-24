import React, { useState, useEffect } from 'react';
import ApiService from '../services/api';
import './BasketCreator.css';

const BasketCreator = ({ onClose, onBasketCreated }) => {
  const [basketName, setBasketName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [executionStrategy, setExecutionStrategy] = useState('sequential');
  const [availableAgents, setAvailableAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [agentsLoading, setAgentsLoading] = useState(true);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      setAgentsLoading(true);
      const agents = await ApiService.fetchAgents();
      setAvailableAgents(agents);
    } catch (err) {
      setError('Failed to fetch agents: ' + err.message);
    } finally {
      setAgentsLoading(false);
    }
  };

  const handleAgentToggle = (agentName) => {
    setSelectedAgents(prev => {
      if (prev.includes(agentName)) {
        return prev.filter(name => name !== agentName);
      } else {
        return [...prev, agentName];
      }
    });
  };

  const handleCreate = async () => {
    if (!basketName.trim()) {
      setError('Basket name is required');
      return;
    }

    if (selectedAgents.length === 0) {
      setError('At least one agent must be selected');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const basketData = {
        name: basketName.trim(),
        description: description.trim(),
        agents: selectedAgents,
        execution_strategy: executionStrategy
      };

      const result = await ApiService.createBasket(basketData);
      
      if (result.success) {
        onBasketCreated && onBasketCreated(result.basket);
        onClose();
      } else {
        setError('Failed to create basket');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const moveAgentUp = (index) => {
    if (index > 0) {
      const newAgents = [...selectedAgents];
      [newAgents[index - 1], newAgents[index]] = [newAgents[index], newAgents[index - 1]];
      setSelectedAgents(newAgents);
    }
  };

  const moveAgentDown = (index) => {
    if (index < selectedAgents.length - 1) {
      const newAgents = [...selectedAgents];
      [newAgents[index], newAgents[index + 1]] = [newAgents[index + 1], newAgents[index]];
      setSelectedAgents(newAgents);
    }
  };

  const removeAgent = (agentName) => {
    setSelectedAgents(prev => prev.filter(name => name !== agentName));
  };

  return (
    <div className="basket-creator-overlay">
      <div className="basket-creator-modal">
        <div className="basket-creator-header">
          <h2>Create New Basket</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="basket-creator-content">
          <div className="form-section">
            <div className="form-group">
              <label htmlFor="basketName">Basket Name *</label>
              <input
                id="basketName"
                type="text"
                value={basketName}
                onChange={(e) => setBasketName(e.target.value)}
                placeholder="Enter basket name..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter basket description..."
                className="form-textarea"
                rows={3}
              />
            </div>

            <div className="form-group">
              <label htmlFor="executionStrategy">Execution Strategy</label>
              <select
                id="executionStrategy"
                value={executionStrategy}
                onChange={(e) => setExecutionStrategy(e.target.value)}
                className="form-select"
              >
                <option value="sequential">Sequential</option>
                <option value="parallel">Parallel (Future)</option>
              </select>
            </div>
          </div>

          <div className="agents-section">
            <div className="available-agents">
              <h3>Available Agents</h3>
              {agentsLoading ? (
                <div className="loading">Loading agents...</div>
              ) : (
                <div className="agents-list">
                  {availableAgents.map((agent) => (
                    <div
                      key={agent.name}
                      className={`agent-item ${selectedAgents.includes(agent.name) ? 'selected' : ''}`}
                      onClick={() => handleAgentToggle(agent.name)}
                    >
                      <div className="agent-info">
                        <span className="agent-name">{agent.name}</span>
                        <div className="agent-domains">
                          {agent.domains?.map((domain, idx) => (
                            <span key={idx} className="domain-tag">{domain}</span>
                          ))}
                        </div>
                      </div>
                      <div className="agent-checkbox">
                        {selectedAgents.includes(agent.name) ? '✓' : '+'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="selected-agents">
              <h3>Selected Agents ({selectedAgents.length})</h3>
              {selectedAgents.length === 0 ? (
                <div className="empty-selection">
                  No agents selected. Click on agents from the left to add them.
                </div>
              ) : (
                <div className="selected-list">
                  {selectedAgents.map((agentName, index) => (
                    <div key={agentName} className="selected-agent-item">
                      <span className="execution-order">{index + 1}</span>
                      <span className="agent-name">{agentName}</span>
                      <div className="agent-controls">
                        <button
                          onClick={() => moveAgentUp(index)}
                          disabled={index === 0}
                          className="move-btn"
                          title="Move up"
                        >
                          ↑
                        </button>
                        <button
                          onClick={() => moveAgentDown(index)}
                          disabled={index === selectedAgents.length - 1}
                          className="move-btn"
                          title="Move down"
                        >
                          ↓
                        </button>
                        <button
                          onClick={() => removeAgent(agentName)}
                          className="remove-btn"
                          title="Remove"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </div>

        <div className="basket-creator-footer">
          <button 
            className="create-btn" 
            onClick={handleCreate}
            disabled={loading || !basketName.trim() || selectedAgents.length === 0}
          >
            {loading ? 'Creating...' : 'Create Basket'}
          </button>
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default BasketCreator;
