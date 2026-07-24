import React, { useState, useEffect } from "react";
import AgentsList from "./AgentsList";
import BasketsList from "./BasketsList";
import DarkModeToggle from "./DarkModeToggle";
import ApiService from "../services/api";
import "./AdminDashboard.css";

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState("agents");
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);

  useEffect(() => {
    checkHealth();
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      setHealthLoading(true);
      const health = await ApiService.checkHealth();
      setHealthStatus(health);
    } catch (error) {
      setHealthStatus({
        status: "error",
        message: "Failed to connect to backend",
      });
    } finally {
      setHealthLoading(false);
    }
  };

  const getHealthStatusColor = (status) => {
    switch (status) {
      case "healthy":
        return "#28a745";
      case "degraded":
        return "#ffc107";
      case "unhealthy":
        return "#dc3545";
      case "error":
        return "#dc3545";
      default:
        return "#6c757d";
    }
  };

  const getHealthStatusText = (status) => {
    switch (status) {
      case "healthy":
        return "All systems operational";
      case "degraded":
        return "Some services unavailable";
      case "unhealthy":
        return "System issues detected";
      case "error":
        return "Cannot connect to backend";
      default:
        return "Unknown status";
    }
  };

  return (
    <div className="admin-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>AI Integration Admin Panel</h1>
          <div className="header-right">
            <div className="health-status">
              {healthLoading ? (
                <div className="health-loading">Checking...</div>
              ) : (
                <div
                  className="health-indicator"
                  style={{
                    backgroundColor: getHealthStatusColor(healthStatus?.status),
                  }}
                  title={getHealthStatusText(healthStatus?.status)}
                >
                  <span className="health-dot"></span>
                  <span className="health-text">
                    {getHealthStatusText(healthStatus?.status)}
                  </span>
                </div>
              )}
            </div>
            <DarkModeToggle />
          </div>
        </div>

        <nav className="dashboard-nav">
          <button
            className={`nav-tab ${activeTab === "agents" ? "active" : ""}`}
            onClick={() => setActiveTab("agents")}
          >
            🤖 Agents
          </button>
          <button
            className={`nav-tab ${activeTab === "baskets" ? "active" : ""}`}
            onClick={() => setActiveTab("baskets")}
          >
            🗂️ Baskets
          </button>
        </nav>
      </header>

      <main className="dashboard-content">
        {healthStatus?.status === "error" && (
          <div className="connection-error">
            <h3>⚠️ Backend Connection Error</h3>
            <p>
              Cannot connect to the AI Integration backend at
              http://localhost:8000
            </p>
            <p>Please ensure:</p>
            <ul>
              <li>The FastAPI server is running (python main.py)</li>
              <li>The server is accessible at http://localhost:8000</li>
              <li>CORS is properly configured</li>
            </ul>
            <button onClick={checkHealth} className="retry-connection-btn">
              🔄 Retry Connection
            </button>
          </div>
        )}

        {healthStatus?.status !== "error" && (
          <>
            {activeTab === "agents" && <AgentsList />}
            {activeTab === "baskets" && <BasketsList />}
          </>
        )}

        {healthStatus?.services && (
          <div className="services-status">
            <h3>Service Status</h3>
            <div className="services-grid">
              {Object.entries(healthStatus.services).map(
                ([service, status]) => (
                  <div key={service} className="service-item">
                    <span className="service-name">{service}</span>
                    <span
                      className={`service-status ${status}`}
                      style={{
                        color: status === "connected" ? "#28a745" : "#dc3545",
                      }}
                    >
                      {status}
                    </span>
                  </div>
                )
              )}
            </div>
          </div>
        )}
      </main>

      <footer className="dashboard-footer">
        <p>AI Integration Platform - Admin Panel</p>
        <p>Backend: http://localhost:8000 | Frontend: http://localhost:5173</p>
      </footer>
    </div>
  );
};

export default AdminDashboard;
