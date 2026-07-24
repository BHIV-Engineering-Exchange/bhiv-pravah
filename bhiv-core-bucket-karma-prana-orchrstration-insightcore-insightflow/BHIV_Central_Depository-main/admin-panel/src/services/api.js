const API_BASE_URL = "http://localhost:8000";

class ApiService {
  async fetchAgents() {
    try {
      const response = await fetch(`${API_BASE_URL}/agents`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching agents:", error);
      throw error;
    }
  }

  async fetchBaskets() {
    try {
      const response = await fetch(`${API_BASE_URL}/baskets`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching baskets:", error);
      throw error;
    }
  }

  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error checking health:", error);
      throw error;
    }
  }

  async runAgent(agentName, inputData, stateful = false) {
    try {
      const response = await fetch(`${API_BASE_URL}/run-agent`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent_name: agentName,
          input_data: inputData,
          stateful: stateful,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error running agent:", error);
      throw error;
    }
  }

  async runBasket(basketName, config = null, inputData = null) {
    try {
      const body = basketName
        ? {
            basket_name: basketName,
            ...(inputData && { input_data: inputData })
          }
        : { config: config };

      const response = await fetch(`${API_BASE_URL}/run-basket`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error running basket:", error);
      throw error;
    }
  }

  async createBasket(basketData) {
    try {
      const response = await fetch(`${API_BASE_URL}/create-basket`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(basketData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error creating basket:", error);
      throw error;
    }
  }

  async deleteBasket(basketName) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/baskets/${encodeURIComponent(basketName)}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }
      return await response.json();
    } catch (error) {
      console.error("Error deleting basket:", error);
      throw error;
    }
  }
}

export default new ApiService();
