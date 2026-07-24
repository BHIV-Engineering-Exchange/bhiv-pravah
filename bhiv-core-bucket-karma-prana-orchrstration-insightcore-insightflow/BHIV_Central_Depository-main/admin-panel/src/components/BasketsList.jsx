import React, { useState, useEffect } from "react";
import ApiService from "../services/api";
import BasketCreator from "./BasketCreator";
import BasketRunner from "./BasketRunner";
import "./BasketsList.css";

const BasketsList = () => {
  const [baskets, setBaskets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBasket, setSelectedBasket] = useState(null);
  const [showCreator, setShowCreator] = useState(false);
  const [runningBasket, setRunningBasket] = useState(null);
  const [deletingBasket, setDeletingBasket] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  useEffect(() => {
    fetchBaskets();
  }, []);

  const fetchBaskets = async () => {
    try {
      setLoading(true);
      const data = await ApiService.fetchBaskets();
      setBaskets(data.baskets || []);
      setError(null);
    } catch (err) {
      setError("Failed to fetch baskets: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBasketClick = (basket) => {
    const basketId = basket.name || basket.basket_name || basket.filename;
    setSelectedBasket(selectedBasket === basketId ? null : basketId);
  };

  const getBasketName = (basket) => {
    return (
      basket.name || basket.basket_name || basket.filename || "Unnamed Basket"
    );
  };

  const getBasketId = (basket) => {
    return basket.name || basket.basket_name || basket.filename;
  };

  const formatAgentsList = (agents) => {
    if (!agents || !Array.isArray(agents)) return "No agents specified";
    return agents.join(", ");
  };

  const formatTestCases = (testCases) => {
    if (!testCases || !Array.isArray(testCases)) return null;
    return testCases;
  };

  const handleCreateBasket = () => {
    setShowCreator(true);
  };

  const handleCloseCreator = () => {
    setShowCreator(false);
  };

  const handleBasketCreated = (newBasket) => {
    // Refresh the baskets list
    fetchBaskets();
  };

  const handleRunBasket = (basket, event) => {
    event.stopPropagation(); // Prevent card selection when clicking run button
    setRunningBasket(basket);
  };

  const handleCloseRunner = () => {
    setRunningBasket(null);
  };

  const handleDeleteBasket = (basket, event) => {
    event.stopPropagation(); // Prevent card selection when clicking delete button
    const basketName = getBasketName(basket);
    setDeleteConfirm(basketName);
  };

  const confirmDeleteBasket = async () => {
    if (!deleteConfirm) return;

    try {
      setDeletingBasket(deleteConfirm);
      setError(null);

      // Call the delete API
      await ApiService.deleteBasket(deleteConfirm);

      // Refresh the baskets list
      await fetchBaskets();

      // Show success message
      setError(`✅ Basket "${deleteConfirm}" deleted successfully`);
      setTimeout(() => setError(null), 3000);
    } catch (err) {
      setError(`❌ Failed to delete basket: ${err.message}`);
    } finally {
      setDeletingBasket(null);
      setDeleteConfirm(null);
    }
  };

  const cancelDeleteBasket = () => {
    setDeleteConfirm(null);
  };

  if (loading) {
    return (
      <div className="baskets-container">
        <div className="loading">Loading baskets...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="baskets-container">
        <div className="error">
          {error}
          <button onClick={fetchBaskets} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="baskets-container">
      <div className="baskets-header">
        <h2>Available Baskets ({baskets.length})</h2>
        <div className="header-buttons">
          <button onClick={handleCreateBasket} className="create-basket-btn">
            ➕ Create Basket
          </button>
          <button onClick={fetchBaskets} className="refresh-btn">
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="baskets-grid">
        {baskets.map((basket, index) => {
          const basketId = getBasketId(basket);
          const isSelected = selectedBasket === basketId;

          return (
            <div
              key={basketId || index}
              className={`basket-card ${isSelected ? "selected" : ""}`}
              onClick={() => handleBasketClick(basket)}
            >
              <div className="basket-header">
                <div className="basket-title-section">
                  <h3>{getBasketName(basket)}</h3>
                  <div className="basket-meta">
                    {basket.source && (
                      <span className="source-tag">{basket.source}</span>
                    )}
                    {basket.execution_strategy && (
                      <span className="strategy-tag">
                        {basket.execution_strategy}
                      </span>
                    )}
                  </div>
                </div>
                <div className="basket-actions">
                  <button
                    onClick={(e) => handleRunBasket(basket, e)}
                    className="run-basket-btn"
                    title="Run this basket"
                    disabled={deletingBasket === getBasketName(basket)}
                  >
                    ▶ Run
                  </button>
                  <button
                    onClick={(e) => handleDeleteBasket(basket, e)}
                    className="delete-basket-btn"
                    title="Delete this basket"
                    disabled={deletingBasket === getBasketName(basket)}
                  >
                    {deletingBasket === getBasketName(basket) ? "🔄" : "🗑️"}
                  </button>
                </div>
              </div>

              <div className="basket-info">
                <div className="info-row">
                  <strong>Agents:</strong>
                  <span>{formatAgentsList(basket.agents)}</span>
                </div>

                {basket.execution_strategy && (
                  <div className="info-row">
                    <strong>Strategy:</strong>
                    <span>{basket.execution_strategy}</span>
                  </div>
                )}

                {basket.filename && (
                  <div className="info-row">
                    <strong>File:</strong>
                    <span className="filename">{basket.filename}</span>
                  </div>
                )}
              </div>

              {isSelected && (
                <div className="basket-details">
                  {basket.description && (
                    <div className="detail-section">
                      <h4>Description</h4>
                      <p>{basket.description}</p>
                    </div>
                  )}

                  <div className="detail-section">
                    <h4>Configuration</h4>
                    <pre className="config-code">
                      {JSON.stringify(
                        {
                          name: getBasketName(basket),
                          agents: basket.agents,
                          execution_strategy:
                            basket.execution_strategy || "sequential",
                          ...(basket.source && { source: basket.source }),
                        },
                        null,
                        2
                      )}
                    </pre>
                  </div>

                  {formatTestCases(basket.test_cases) && (
                    <div className="detail-section">
                      <h4>Test Cases</h4>
                      <div className="test-cases">
                        {formatTestCases(basket.test_cases).map(
                          (testCase, idx) => (
                            <div key={idx} className="test-case">
                              <h5>
                                {testCase.description || `Test Case ${idx + 1}`}
                              </h5>
                              <div className="test-details">
                                <div className="test-input">
                                  <strong>Input:</strong>
                                  <pre>
                                    {JSON.stringify(testCase.input, null, 2)}
                                  </pre>
                                </div>
                                <div className="test-expected">
                                  <strong>Expected:</strong>
                                  <pre>
                                    {JSON.stringify(testCase.expected, null, 2)}
                                  </pre>
                                </div>
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {baskets.length === 0 && (
        <div className="no-data">
          No baskets found. Make sure the backend is running and baskets are
          properly configured.
        </div>
      )}

      {showCreator && (
        <BasketCreator
          onClose={handleCloseCreator}
          onBasketCreated={handleBasketCreated}
        />
      )}

      {runningBasket && (
        <BasketRunner basket={runningBasket} onClose={handleCloseRunner} />
      )}

      {deleteConfirm && (
        <div className="modal-overlay">
          <div className="delete-confirmation-modal">
            <div className="modal-header">
              <h3>⚠️ Delete Basket</h3>
            </div>
            <div className="modal-content">
              <p>
                Are you sure you want to delete the basket{" "}
                <strong>"{deleteConfirm}"</strong>?
              </p>
              <div className="warning-text">
                <p>⚠️ This action will permanently:</p>
                <ul>
                  <li>Delete the basket configuration file</li>
                  <li>Clean up all execution logs from Redis</li>
                  <li>Remove all related data from MongoDB</li>
                  <li>Delete all log files for this basket</li>
                </ul>
                <p>
                  <strong>This action cannot be undone!</strong>
                </p>
              </div>
            </div>
            <div className="modal-actions">
              <button
                onClick={cancelDeleteBasket}
                className="cancel-btn"
                disabled={deletingBasket}
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteBasket}
                className="delete-confirm-btn"
                disabled={deletingBasket}
              >
                {deletingBasket ? "Deleting..." : "Delete Basket"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BasketsList;
