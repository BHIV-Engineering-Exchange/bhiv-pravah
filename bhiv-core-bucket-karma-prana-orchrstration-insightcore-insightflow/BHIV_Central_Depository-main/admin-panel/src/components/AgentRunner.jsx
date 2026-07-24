import React, { useState } from 'react';
import ApiService from '../services/api';
import './AgentRunner.css';

const AgentRunner = ({ agent, onClose }) => {
  const [inputData, setInputData] = useState('');
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Special handling for textToJson agent
  const [selectedEndpoint, setSelectedEndpoint] = useState('token');
  const [apiKey, setApiKey] = useState('test-api-key');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [prompt, setPrompt] = useState('');
  const [spec, setSpec] = useState('');
  const [nIter, setNIter] = useState(3);
  const [jwtToken, setJwtToken] = useState('');

  // Pre-populate with sample input if available
  React.useEffect(() => {
    if (agent.sample_input) {
      setInputData(JSON.stringify(agent.sample_input, null, 2));
    }
  }, [agent]);

  const handleRun = async () => {
    if (agent.name === 'textToJson') {
      await handleTextToJsonRun();
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setOutput(null);

      let parsedInput;
      try {
        parsedInput = JSON.parse(inputData);
      } catch (e) {
        throw new Error('Invalid JSON input. Please check your input format.');
      }

      const result = await ApiService.runAgent(agent.name, parsedInput, false);
      setOutput(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTextToJsonRun = async () => {
    try {
      setLoading(true);
      setError(null);
      setOutput(null);

      const baseUrl = 'https://prompt-to-json-backend.onrender.com';
      let url = `${baseUrl}/${selectedEndpoint}`;
      let body = {};
      let headers = {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      };

      if (selectedEndpoint === 'token') {
        body = { username, password };
      } else if (selectedEndpoint === 'generate') {
        body = { prompt };
        if (jwtToken) headers['Authorization'] = `Bearer ${jwtToken}`;
      } else if (selectedEndpoint === 'evaluate') {
        let parsedSpec;
        try {
          parsedSpec = JSON.parse(spec);
        } catch (e) {
          throw new Error('Invalid JSON in spec field.');
        }
        body = { spec: parsedSpec, prompt };
        if (jwtToken) headers['Authorization'] = `Bearer ${jwtToken}`;
      } else if (selectedEndpoint === 'iterate') {
        body = { prompt, n_iter: parseInt(nIter) };
        if (jwtToken) headers['Authorization'] = `Bearer ${jwtToken}`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(`HTTP ${response.status}: ${errorData.detail || errorData.message || 'Request failed'}`);
      }

      const data = await response.json();
      setOutput(data);

      // If token endpoint, save the JWT
      if (selectedEndpoint === 'token' && data.access_token) {
        setJwtToken(data.access_token);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setInputData(e.target.value);
  };

  const getDefaultInput = () => {
    if (agent.name === 'financial_coordinator') {
      return {
        "action": "get_transactions"
      };
    }
    return agent.sample_input || {};
  };

  const loadSampleInput = () => {
    setInputData(JSON.stringify(getDefaultInput(), null, 2));
  };

  const formatOutput = (data) => {
    if (typeof data === 'string') {
      try {
        return JSON.stringify(JSON.parse(data), null, 2);
      } catch {
        return data;
      }
    }
    return JSON.stringify(data, null, 2);
  };

  return (
    <div className="agent-runner-overlay">
      <div className="agent-runner-modal">
        <div className="agent-runner-header">
          <h2>Run Agent: {agent.name}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="agent-runner-content">
          {agent.name === 'textToJson' ? (
            <div className="texttojson-section">
              <h3>Text-to-JSON API Interface</h3>
              <p>Interact directly with the Prompt-to-JSON API endpoints.</p>

              <div className="endpoint-selection">
                <label>Select Endpoint:</label>
                <select
                  value={selectedEndpoint}
                  onChange={(e) => setSelectedEndpoint(e.target.value)}
                  className="endpoint-select"
                >
                  <option value="token">Token (Authentication)</option>
                  <option value="generate">Generate (Create Spec)</option>
                  <option value="evaluate">Evaluate (Score Spec)</option>
                  <option value="iterate">Iterate (RL Training)</option>
                </select>
              </div>

              <div className="api-key-section">
                <label>API Key:</label>
                <input
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter API key"
                  className="api-key-input"
                />
              </div>

              {selectedEndpoint === 'token' && (
                <div className="endpoint-inputs">
                  <div className="input-group">
                    <label>Username:</label>
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Enter username"
                    />
                  </div>
                  <div className="input-group">
                    <label>Password:</label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter password"
                    />
                  </div>
                </div>
              )}

              {(selectedEndpoint === 'generate' || selectedEndpoint === 'evaluate' || selectedEndpoint === 'iterate') && (
                <div className="endpoint-inputs">
                  <div className="input-group">
                    <label>Prompt:</label>
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="Enter prompt..."
                      rows={3}
                    />
                  </div>
                  {selectedEndpoint === 'evaluate' && (
                    <div className="input-group">
                      <label>Spec (JSON):</label>
                      <textarea
                        value={spec}
                        onChange={(e) => setSpec(e.target.value)}
                        placeholder='{"design_type": "web_app", ...}'
                        rows={5}
                      />
                    </div>
                  )}
                  {selectedEndpoint === 'iterate' && (
                    <div className="input-group">
                      <label>Number of Iterations:</label>
                      <input
                        type="number"
                        value={nIter}
                        onChange={(e) => setNIter(e.target.value)}
                        min="1"
                        max="10"
                      />
                    </div>
                  )}
                  {jwtToken && (
                    <div className="jwt-display">
                      <label>JWT Token (auto-filled):</label>
                      <textarea value={jwtToken} readOnly rows={2} />
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="input-section">
              <div className="input-header">
                <h3>Input Data</h3>
                <button
                  className="sample-btn"
                  onClick={loadSampleInput}
                  type="button"
                >
                  Load Sample
                </button>
              </div>

              <textarea
                value={inputData}
                onChange={handleInputChange}
                placeholder="Enter JSON input data..."
                className="input-textarea"
                rows={10}
              />

              {agent.input_schema && (
                <div className="schema-info">
                  <h4>Expected Input Schema:</h4>
                  <pre className="schema-display">
                    {JSON.stringify(agent.input_schema, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          <div className="output-section">
            <h3>Output</h3>
            
            {loading && (
              <div className="loading-state">
                <div className="spinner"></div>
                <span>Running agent...</span>
              </div>
            )}

            {error && (
              <div className="error-state">
                <h4>Error:</h4>
                <pre className="error-display">{error}</pre>
              </div>
            )}

            {output && (
              <div className="output-state">
                <h4>Result:</h4>
                <pre className="output-display">
                  {formatOutput(output)}
                </pre>
              </div>
            )}

            {!loading && !error && !output && (
              <div className="empty-state">
                Click "Run Agent" to see the output here
              </div>
            )}
          </div>
        </div>

        <div className="agent-runner-footer">
          <button
            className="run-btn"
            onClick={handleRun}
            disabled={loading || (agent.name !== 'textToJson' && !inputData.trim())}
          >
            {loading ? 'Running...' : agent.name === 'textToJson' ? `Call ${selectedEndpoint.toUpperCase()}` : 'Run Agent'}
          </button>
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentRunner;
