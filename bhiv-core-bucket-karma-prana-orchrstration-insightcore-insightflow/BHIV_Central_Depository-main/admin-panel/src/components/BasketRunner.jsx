import React, { useState } from "react";
import ApiService from "../services/api";
import "./BasketRunner.css";

const BasketRunner = ({ basket, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [inputData, setInputData] = useState("");

  // Authentication state for external API
  const [apiKey, setApiKey] = useState("test-api-key");
  const [username, setUsername] = useState("demo");
  const [password, setPassword] = useState("demo");
  const [jwtToken, setJwtToken] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState(null);

  const getBasketName = () => {
    return basket.name || basket.basket_name || basket.filename || "Unnamed Basket";
  };

  const handleRunBasket = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const basketName = getBasketName();
      console.log("Running basket:", basketName);

      // Parse input data if provided
      let parsedInputData = null;
      if (inputData.trim()) {
        try {
          parsedInputData = JSON.parse(inputData);
        } catch (parseError) {
          setError("Invalid JSON in input data. Please check your syntax.");
          setLoading(false);
          return;
        }
      }

      // Include JWT token if available
      if (jwtToken) {
        parsedInputData = parsedInputData || {};
        parsedInputData.jwt_token = jwtToken;
      }

      const response = await ApiService.runBasket(basketName, null, parsedInputData);
      setResult(response);
    } catch (err) {
      console.error("Error running basket:", err);
      setError(err.message || "Failed to run basket");
    } finally {
      setLoading(false);
    }
  };

  const handleAuthenticate = async () => {
    try {
      setAuthLoading(true);
      setAuthError(null);

      const response = await fetch("https://prompt-to-json-backend.onrender.com/token", {
        method: "POST",
        headers: {
          "X-API-Key": apiKey,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: username,
          password: password
        })
      });

      if (response.ok) {
        const data = await response.json();
        setJwtToken(data.access_token);
        console.log("Authentication successful");
      } else {
        const errorData = await response.json();
        setAuthError(errorData.detail || "Authentication failed");
      }
    } catch (err) {
      console.error("Authentication error:", err);
      setAuthError("Network error during authentication");
    } finally {
      setAuthLoading(false);
    }
  };

  const formatResult = (data) => {
    if (typeof data === "string") {
      return data;
    }
    return JSON.stringify(data, null, 2);
  };

  return (
    <div className="basket-runner-overlay">
      <div className="basket-runner-modal">
        <div className="basket-runner-header">
          <h2>Run Basket: {getBasketName()}</h2>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="basket-runner-content">
          {/* Authentication Section for External API */}
          {getBasketName().toLowerCase().includes('texttojson') || getBasketName().toLowerCase().includes('text_to_json') ? (
            <div className="auth-section">
              <h3>External API Authentication</h3>
              <p className="auth-help">
                Authenticate with the Prompt-to-JSON API to get a JWT token for the agent.
              </p>

              <div className="auth-form">
                <div className="auth-inputs">
                  <div className="input-group">
                    <label>API Key:</label>
                    <input
                      type="text"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter API key"
                    />
                  </div>

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

                <button
                  className="auth-btn"
                  onClick={handleAuthenticate}
                  disabled={authLoading}
                >
                  {authLoading ? 'Authenticating...' : 'Get JWT Token'}
                </button>
              </div>

              {authError && (
                <div className="auth-error">
                  Authentication Error: {authError}
                </div>
              )}

              {jwtToken && (
                <div className="jwt-display">
                  <label>JWT Token:</label>
                  <textarea
                    value={jwtToken}
                    onChange={(e) => setJwtToken(e.target.value)}
                    placeholder="JWT token will appear here"
                    rows={3}
                    readOnly
                  />
                  <p className="jwt-note">Token will be automatically included in basket execution.</p>
                </div>
              )}
            </div>
          ) : null}

          <div className="input-section">
            <h3>Input Data (Optional)</h3>
            <p className="input-help">
              Provide input data as JSON. Leave empty to use default values for testing.
            </p>
            <textarea
              className="input-data-textarea"
              value={inputData}
              onChange={(e) => setInputData(e.target.value)}
              placeholder={`Example for cashflow_analyzer:
{
  "transactions": [
    {"id": 1, "amount": 1000, "description": "Income"},
    {"id": 2, "amount": -500, "description": "Expense"}
  ]
}

Example for goal_recommender:
{
  "analysis": {
    "total": 500,
    "positive": 1000,
    "negative": -500
  }
}

Example for textToJson (generate action):
{
  "action": "generate",
  "prompt": "Create a specification for a modern web application"
}

Example for textToJson (evaluate action):
{
  "action": "evaluate",
  "spec": {
    "design_type": "web_app",
    "components": ["frontend", "backend"]
  },
  "prompt": "Evaluate this web application specification"
}

Example for textToJson (iterate action):
{
  "action": "iterate",
  "prompt": "Create an optimal specification through reinforcement learning",
  "n_iter": 3
}

Example for textToJson (all actions):
{
  "action": "all",
  "prompt": "Create a comprehensive specification",
  "n_iter": 2
}

Example for textToJson with JWT token:
{
  "action": "generate",
  "prompt": "Create a web app spec",
  "jwt_token": "your_jwt_token_here"
}`}
              rows={8}
            />
          </div>

          <div className="basket-content-grid">
            <div className="basket-info-section">
              <h3>Basket Information</h3>
              <div className="basket-details">
                <div className="info-item">
                  <strong>Name:</strong> {getBasketName()}
                </div>
                {basket.agents && (
                  <div className="info-item">
                    <strong>Agents:</strong> {Array.isArray(basket.agents) ? basket.agents.join(", ") : basket.agents}
                  </div>
                )}
                {basket.execution_strategy && (
                  <div className="info-item">
                    <strong>Strategy:</strong> {basket.execution_strategy}
                  </div>
                )}
                {basket.description && (
                  <div className="info-item">
                    <strong>Description:</strong> {basket.description}
                  </div>
                )}
              </div>

              <div className="basket-config">
                <h4>Configuration</h4>
                <pre className="config-display">
                  {JSON.stringify(
                    {
                      name: getBasketName(),
                      agents: basket.agents,
                      execution_strategy: basket.execution_strategy || "sequential",
                      ...(basket.source && { source: basket.source }),
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
            </div>

            <div className="output-section">
              <h3>Execution Output</h3>

              {loading && (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <span>Running basket...</span>
                </div>
              )}

              {error && (
                <div className="error-state">
                  <h4>Error</h4>
                  <div className="error-display">{error}</div>
                </div>
              )}

              {result && (
                <div className="output-state">
                  <h4>Result</h4>
                  <div className="output-display">
                    {formatResult(result)}
                  </div>
                </div>
              )}

              {!loading && !error && !result && (
                <div className="empty-state">
                  Click "Run Basket" to execute this basket and see the results here.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="basket-runner-footer">
          <button 
            className="run-btn" 
            onClick={handleRunBasket}
            disabled={loading}
          >
            {loading ? 'Running...' : 'Run Basket'}
          </button>
          <button className="cancel-btn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default BasketRunner;
