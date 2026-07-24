
- **API Key Management**: Secure environment-based API key handling for all services
- **Dynamic Discovery**: Automatic agent registration and capability detection
- **Standardized Interface**: Consistent input/output format across all agents

### 🧺 **Intelligent Basket Orchestration**
- **Multi-Agent Workflows**: Chain multiple AI agents in sequential or parallel execution
- **Data Flow Management**: Seamless data passing between agents in workflows
- **Execution Strategies**: Support for sequential, parallel, and custom execution patterns
- **Workflow Templates**: Pre-built baskets for common AI operations

### 💬 **Inter-Agent Communication**
- **Event Bus System**: Real-time communication between agents during execution
- **State Management**: Persistent state sharing across agent interactions
- **Message Passing**: Structured messaging system for agent coordination
- **Dependency Resolution**: Automatic handling of agent dependencies

#### 🏛️ **Governance & Ownership**
- **BHIV Bucket v1**: Formal ownership and custodianship structure
- **Primary Owner**: Ashmit (final authority on integrations and policies)
- **Artifact Management**: Approved/rejected artifact classes for data storage
- **Versioning**: Semantic versioning with clear upgrade paths
- **Governance API**: Endpoints for validation and compliance

## 🏗️ **Enterprise-Grade Architecture**
- **FastAPI Backend**: High-performance REST API with automatic documentation
- **MongoDB Integration**: Persistent storage for logs, state, and execution history
- **Redis Caching**: High-speed caching with graceful fallback mechanisms
- **React Admin Panel**: Modern web interface for management and monitoring
- **Comprehensive Logging**: Multi-level logging with rotation and monitoring

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (Recommended: 3.11+)
- **MongoDB** (local installation or MongoDB Atlas)
- **Redis** (optional, for enhanced performance)
- **Node.js 16+** (for admin panel)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd AI_integration

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database URLs

# Install admin panel dependencies (optional)
cd admin-panel
npm install
cd ..
```

### Environment Setup
Create a `.env` file in the root directory:
```env
# Database Configuration
MONGODB_URI=mongodb://localhost:27017/ai_integration
REDIS_HOST=localhost
REDIS_PORT=6379

# AI Service API Keys
OPENAI_API_KEY=sk-your-openai-key
GROQ_API_KEY=gsk_your-groq-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_AI_API_KEY=your-google-ai-key

# Server Configuration
FASTAPI_PORT=8000
```

### Start the Platform
```bash
# Start the FastAPI server
python main.py

# In another terminal, start the admin panel (optional)
cd admin-panel
npm run dev
```

## 📁 Project Architecture

```
AI_integration/
├── agents/                 # 🤖 AI Agent Implementations
│   ├── agent_registry.py   # Agent discovery and management
│   ├── agent_runner.py     # Agent execution engine
│   ├── base_agent.py       # Base agent class
│   └── [domain]/           # Domain-specific agents
│       ├── agent_spec.json # Agent specification
│       └── [agent].py      # Agent implementation
├── admin-panel/            # 🖥️ React Management Interface
│   ├── src/components/     # React components
│   ├── src/services/       # API service layer
│   └── package.json        # Frontend dependencies
├── baskets/               # 🧺 Workflow Definitions
│   ├── basket_manager.py   # Basket execution engine
│   └── *.json             # Basket configurations
├── communication/         # 📡 Inter-Agent Communication
│   └── event_bus.py       # Event system
├── database/             # 🗄️ Database Layer
│   └── mongo_db.py       # MongoDB client
├── logs/                 # 📝 Application Logs
├── tests/                # 🧪 Test Suite
├── utils/                # 🛠️ Utilities
│   ├── logger.py         # Logging system
│   └── redis_service.py  # Redis integration
├── main.py               # 🚀 FastAPI Server
└── requirements.txt      # Python dependencies
```

## 🤖 Current Agent Ecosystem

### Available Agents by Domain:
- **Finance** (3 agents): `cashflow_analyzer`, `goal_recommender`, `financial_coordinator`
- **Automotive** (3 agents): `auto_diagnostics`, `vehicle_maintenance`, `fuel_efficiency`
- **Education** (5 agents): `vedic_quiz_agent`, `sanskrit_parser`, `gurukul_*`
- **Workflow** (1 agent): `workflow_agent`

### Example Multi-Agent Workflow:
```json
{
  "basket_name": "financial_analysis",
  "agents": ["cashflow_analyzer", "goal_recommender"],
  "execution_strategy": "sequential",
  "description": "Analyze transactions and provide recommendations"
}
```

**Result**: Cashflow analysis flows seamlessly to goal recommendations!

## 🔧 How to Add New AI Agents

### Step 1: Create Agent Directory Structure
```bash
mkdir -p agents/your_agent_name
cd agents/your_agent_name
```

### Step 2: Create Agent Specification (`agent_spec.json`)
```json
{
    "name": "your_agent_name",
    "domains": ["your_domain"],
    "module_path": "agents.your_agent_name.your_agent_name",
    "capabilities": {
        "chainable": true,
        "memory_access": true
    },
    "input_schema": {
        "required": ["input_field"],
        "properties": {
            "input_field": {
                "type": "string",
                "description": "Description of input"
            }
        }
    },
    "output_schema": {
        "properties": {
            "result": {
                "type": "object",
                "description": "Agent output"
            }
        }
    },
    "sample_input": {
        "input_field": "sample value"
    },
    "sample_output": {
        "result": {"processed": "sample value"}
    }
}
```

### Step 3: Implement Agent with API Key Integration

Create `your_agent_name.py`:

```python
import os
from typing import Dict
from dotenv import load_dotenv
from utils.logger import logger

# Load environment variables
load_dotenv()

async def process(input_data: Dict) -> Dict:
    """
    Main agent processing function.
    This function will be called by the basket manager.
    """
    try:
        # Load API key from environment
        api_key = os.getenv("YOUR_API_KEY")
        if not api_key:
            raise ValueError("YOUR_API_KEY not set in .env file")

        # Initialize your AI client (example with OpenAI)
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)

        # Extract input data
        user_input = input_data.get("input_field", "")

        # Process with AI service
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        # Return structured result
        result = {
            "result": {
                "processed": response.choices[0].message.content,
                "model_used": "gpt-4",
                "input_received": user_input
            }
        }

        logger.info(f"Agent processed successfully: {user_input[:50]}...")
        return result

    except Exception as e:
        logger.error(f"Agent processing failed: {e}")
        return {"error": str(e)}
```

4. **Install and start Redis (Recommended):**

   **Option A: Using Docker (Recommended)**
   ```bash
   docker run -d --name ai-redis -p 6379:6379 redis:alpine
   ```

   **Option B: Windows Installation**
   ```bash
   # Using Chocolatey
   choco install redis-64

   # Or download from: https://github.com/microsoftarchive/redis/releases
   ```

   **Option C: macOS Installation**
   ```bash
   brew install redis
   redis-server
   ```

5. **Install and start MongoDB (Optional):**
   ```bash
   # Using Docker (Recommended)
   docker run -d --name ai-mongodb -p 27017:27017 mongo:latest

   # Or install locally from: https://www.mongodb.com/try/download/community
   ```

6. **Start the backend server:**
   ```bash
   python main.py
   ```

   You should see:
   ```
   Redis connected successfully at localhost:6379
   Successfully connected to MongoDB
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

### Step 2: Frontend Setup

1. **Open a new terminal and navigate to the admin panel:**
   ```bash
   cd AI_integration/admin-panel
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the frontend development server:**
   ```bash
   npm run dev
0   ```

   You should see:
   ```
   Local:   http://localhost:5173/
   ```

### Step 3: Verification

1. **Check backend health:**
   ```bash
   curl http://localhost:8000/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "services": {
       "mongodb": "connected",
       "redis": "connected",
       "socketio": "disabled"
     }
   }
   ```

2. **Check available agents:**
   ```bash
   curl http://localhost:8000/agents
   ```

3. **Open the admin panel:**
   - Navigate to http://localhost:5173 in your browser
   - You should see the basket creation interface

### Step 4: Test the System

1. **Test a simple basket via API:**
   ```bash
   # Create a basket
   curl -X POST "http://localhost:8000/create-basket" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "test_cashflow",
       "description": "Test cashflow analysis",
       "agents": ["cashflow_analyzer"],
       "execution_strategy": "sequential"
     }'

   # Run the basket
   curl -X POST "http://localhost:8000/run-basket" \
     -H "Content-Type: application/json" \
     -d '{
       "basket_name": "test_cashflow",
       "input_data": {
         "transactions": [
           {"id": 1, "amount": 1000, "description": "Income"},
           {"id": 2, "amount": -500, "description": "Expense"}
         ]
       }
     }'
   ```

2. **Test via the web interface:**
   - Go to http://localhost:5173 (or check actual port from npm output)
   - Select an existing basket from the list
   - Add input data (optional - see detailed testing section below)
   - Run the basket and view results

## 🧪 **Comprehensive Testing Guide**

### **Frontend Testing (Recommended)**

#### **Step 1: Open Admin Panel**
- Navigate to http://localhost:5173 (or the port shown in npm output)
- You should see the AI Integration Platform interface

#### **Step 2: Test with Default Data (No Input Required)**
1. **Select any basket** from the dropdown (e.g., "working_test", "goal_test", "coordinator_test")
2. **Leave the "Input Data" field empty**
3. **Click "Run Basket"**
4. **View results** - agents will use built-in sample data

#### **Step 3: Create Custom Baskets (Optional)**
1. **Click "Create New Basket"** in the admin panel
2. **Fill in basket details:**
   - Name: e.g., "my_custom_workflow"
   - Description: e.g., "My custom financial workflow"
   - Select agents: Choose from available agents
   - Execution strategy: Sequential or Parallel
3. **Save the basket**
4. **Test your new basket** with the steps below

#### **Step 4: Test with Custom Input Data**
Copy and paste these JSON examples into the "Input Data" textarea:

**For Cashflow Analyzer (working_test basket):**
```json
{
  "transactions": [
    {"id": 1, "amount": 2500, "description": "Monthly Salary"},
    {"id": 2, "amount": -1200, "description": "Rent Payment"},
    {"id": 3, "amount": -300, "description": "Groceries"},
    {"id": 4, "amount": -150, "description": "Utilities"},
    {"id": 5, "amount": 500, "description": "Freelance Income"}
  ]
}
```

**For Goal Recommender (goal_test basket):**
```json
{
  "analysis": {
    "total": 1000,
    "positive": 100000,
    "negative": -500
  }
}
```

**For Financial Coordinator (coordinator_test basket):**
```json
{
  "action": "get_transactions"
}
```

**For Chained Execution (finance_daily_check basket):**
```json
{
  "transactions": [
    {"id": 1, "amount": 3000, "description": "Salary"},
    {"id": 2, "amount": -1000, "description": "Rent"},
    {"id": 3, "amount": -200, "description": "Food"},
    {"id": 4, "amount": -100, "description": "Transport"}
  ]
}
```

### **Backend API Testing (Postman/cURL)**

#### **Step 1: Health Check**
```bash
curl http://localhost:8000/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "services": {
    "mongodb": "disconnected",
    "redis": "connected",
    "socketio": "disabled"
  }
}
```

#### **Step 2: List Available Agents**
```bash
curl http://localhost:8000/agents
```

#### **Step 3: Test Individual Agents**

**Test Cashflow Analyzer:**
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "working_test",
    "input_data": {
      "transactions": [
        {"id": 1, "amount": 2500, "description": "Monthly Salary"},
        {"id": 2, "amount": -1200, "description": "Rent Payment"},
        {"id": 3, "amount": -300, "description": "Groceries"}
      ]
    }
  }'
```

**Test Goal Recommender:**
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "goal_test",
    "input_data": {
      "analysis": {
        "total": 1000,
        "positive": 100000,
        "negative": -500
      }
    }
  }'
```

**Test Financial Coordinator:**
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "coordinator_test",
    "input_data": {
      "action": "get_transactions"
    }
  }'
```

**Test Chained Execution:**
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "finance_daily_check",
    "input_data": {
      "transactions": [
        {"id": 1, "amount": 3000, "description": "Salary"},
        {"id": 2, "amount": -1000, "description": "Rent"}
      ]
    }
  }'
```

#### **Step 4: Test with Default Data (No Input)**
All agents now support running without input data:

```bash
# Test any basket without input_data
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{"basket_name": "working_test"}'

curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{"basket_name": "goal_test"}'

curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{"basket_name": "finance_daily_check"}'
```

### **Postman Testing**

#### **Import Collection:**
1. **Create a new Postman collection** called "AI Integration Platform"
2. **Add these requests:**

**Request 1: Health Check**
- Method: `GET`
- URL: `http://localhost:8000/health`

**Request 2: List Agents**
- Method: `GET`
- URL: `http://localhost:8000/agents`

**Request 3: Run Cashflow Analyzer**
- Method: `POST`
- URL: `http://localhost:8000/run-basket`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "basket_name": "working_test",
  "input_data": {
    "transactions": [
      {"id": 1, "amount": 2500, "description": "Monthly Salary"},
      {"id": 2, "amount": -1200, "description": "Rent Payment"}
    ]
  }
}
```

**Request 4: Run Goal Recommender**
- Method: `POST`
- URL: `http://localhost:8000/run-basket`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "basket_name": "goal_test",
  "input_data": {
    "analysis": {
      "total": 1000,
      "positive": 100000,
      "negative": -500
    }
  }
}
```

**Request 5: Run Chained Execution**
- Method: `POST`
- URL: `http://localhost:8000/run-basket`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "basket_name": "finance_daily_check",
  "input_data": {
    "transactions": [
      {"id": 1, "amount": 3000, "description": "Salary"},
      {"id": 2, "amount": -1000, "description": "Rent"}
    ]
  }
}
```

**Request 6: Test Default Data**
- Method: `POST`
- URL: `http://localhost:8000/run-basket`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "basket_name": "working_test"
}
```

## 📖 API Usage & Agent Input Formats

### Health Check
```bash
curl http://localhost:8000/health
```

### List Available Agents
```bash
curl http://localhost:8000/agents
```

### Agent Input Formats

Each agent requires specific input formats. Here are the working examples:

#### 1. Cashflow Analyzer
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "test_cashflow",
    "input_data": {
      "transactions": [
        {"id": 1, "amount": 1000, "description": "Income"},
        {"id": 2, "amount": -500, "description": "Expense"}
      ]
    }
  }'
```

#### 2. Goal Recommender
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "goal_test",
    "input_data": {
      "analysis": {
        "total": 1000,
        "positive": 100000,
        "negative": -500
      }
    }
  }'
```

#### 3. Financial Coordinator
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "coordinator_test",
    "input_data": {
      "action": "get_transactions"
    }
  }'
```

#### 4. Chained Execution (Cashflow → Goal Recommender)
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "finance_analysis",
    "input_data": {
      "transactions": [
        {"id": 1, "amount": 2000, "description": "Salary"},
        {"id": 2, "amount": -800, "description": "Rent"}
      ]
    }
  }'
```

### Create Custom Baskets
```bash
curl -X POST "http://localhost:8000/create-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_workflow",
    "description": "Custom financial workflow",
    "agents": ["cashflow_analyzer", "goal_recommender"],
    "execution_strategy": "sequential"
  }'
```

## 🔧 Adding a New Agent

Follow these steps to add a new agent to the platform:

### Step 1: Create Agent Directory
```bash
mkdir agents/your_agent_name
```

### Step 2: Create Agent Specification
Create `agents/your_agent_name/agent_spec.json`:

```json
{
    "name": "your_agent_name",
    "domains": ["your_domain"],
    "module_path": "agents.your_agent_name.your_agent_name",
    "capabilities": {
        "chainable": true,
        "memory_access": false
    },
    "input_schema": {
        "required": ["input_field"],
        "properties": {
            "input_field": {
                "type": "string",
                "description": "Description of input"
            }
        }
    },
    "output_schema": {
        "properties": {
            "result": {
                "type": "object",
                "description": "Description of output"
            }
        }
    },
    "sample_input": {
        "input_field": "sample value"
    },
    "sample_output": {
        "result": {"processed": "sample value"}
    }
}
```

### Step 3: Implement Agent Logic
Create `agents/your_agent_name/your_agent_name.py`:

```python
"""
Your Agent Name
Description of what this agent does
"""

from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

async def process(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process input data and return results
    """
    try:
        # Extract input
        input_field = input_data.get("input_field")

        if not input_field:
            raise ValueError("Missing required input_field")

        logger.info(f"Processing your_agent_name with input: {input_field}")

        # Your agent logic here
        result = {
            "processed": f"Processed: {input_field}",
            "status": "completed"
        }

        logger.info("your_agent_name completed successfully")
        return {"result": result}

    except Exception as e:
        logger.error(f"Error in your_agent_name: {e}")
        return {"error": f"your_agent_name failed: {str(e)}"}
```

**Important Notes:**
- Use `async def process()` as the main function (not a class)
- Import `get_logger` from `utils.logger`
- Always include proper error handling
- Return results in a consistent format

### Step 4: Create a Basket (Optional)
Create `baskets/your_basket_name.json`:

```json
{
    "basket_name": "your_basket_name",
    "agents": ["your_agent_name"],
    "execution_strategy": "sequential",
    "description": "Description of your basket workflow"
}
```

### Step 5: Test Your Agent
```bash
# Test the agent directly
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "your_basket_name",
    "input_data": {
      "input_field": "test value"
    }
  }'
```

### Step 6: Restart the Application
```bash
# Stop the current server (Ctrl+C)
# Restart to load the new agent
python main.py
```

## 🧪 Testing

### Run System Tests
```bash
python test_logging_system.py
```

### Test Individual Components
```bash
# Test agent registry
python -c "from agents.agent_registry import AgentRegistry; r = AgentRegistry('agents'); print(f'Loaded {len(r.agents)} agents')"

# Test MongoDB connection
python -c "from database.mongo_db import MongoDBClient; m = MongoDBClient(); print(f'MongoDB connected: {m.db is not None}')"

# Test Redis connection
python -c "from utils.redis_service import RedisService; r = RedisService(); print(f'Redis connected: {r.is_connected()}')"
```

### Validate Agent Specifications
```bash
# Check if all agents load correctly
curl http://localhost:8000/agents | python -m json.tool
*in vs terminal copy paste only till agents. 
```

## 📊 Enhanced Logging & Monitoring

### Log Files Structure
- **`logs/application.log`** - Main application logs
- **`logs/errors.log`** - Error logs only
- **`logs/executions.log`** - Agent execution tracking
- **`logs/basket_runs/`** - Individual basket execution logs
  - `{basket_name}_{execution_id}.log` - Detailed logs for each basket run

### Individual Basket Logs
Each basket execution creates a dedicated log file with detailed tracking:

```bash
# Example: View logs for a specific basket execution
cat logs/basket_runs/test_cashflow_1751692235_6fd591c9.log
```

Sample basket log content:
```
2025-07-05 10:40:35 - INFO - BASKET_INITIALIZED - test_cashflow - 1751692235_6fd591c9
2025-07-05 10:40:35 - INFO - BASKET_START - test_cashflow - Agents: ['cashflow_analyzer']
2025-07-05 10:40:35 - INFO - BASKET_EXECUTION_START - Input: {"transactions": [...]}
2025-07-05 10:40:35 - INFO - AGENT_START - cashflow_analyzer - Step 1/1
2025-07-05 10:40:40 - INFO - AGENT_COMPLETE - cashflow_analyzer - Duration: 4.36s
2025-07-05 10:40:40 - INFO - BASKET_COMPLETE - Duration: 4.51s - Result: {...}
```

### Real-time Monitoring
```bash
# Watch application logs
tail -f logs/application.log

# Watch execution logs
tail -f logs/executions.log

# Watch error logs
tail -f logs/errors.log

# Watch specific basket execution
tail -f logs/basket_runs/your_basket_name_*.log
```

### MongoDB Logs
If MongoDB is connected, logs are also stored in the database:
```javascript
// Connect to MongoDB and view logs
use ai_integration
db.logs.find().sort({timestamp: -1}).limit(10)
```

### Health Monitoring
```bash
# Check system health
curl http://localhost:8000/health

# Expected healthy response:
{
  "status": "healthy",
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "socketio": "disabled"
  }
}
```

### **Testing Results & Expected Outputs**

#### **Frontend Testing Results**
When testing through the web interface, you should see:

**Successful Execution Example:**
```json
{
  "analysis": {
    "total": 1500,
    "positive": 2500,
    "negative": -1000
  },
  "execution_metadata": {
    "execution_id": "1751699312_89ce24ad",
    "basket_name": "working_test",
    "agents_executed": ["cashflow_analyzer"],
    "strategy": "sequential"
  }
}
```

**Chained Execution Example:**
```json
{
  "recommendations": ["Increase savings"],
  "execution_metadata": {
    "execution_id": "1751699343_8e8e866f",
    "basket_name": "finance_daily_check",
    "agents_executed": ["cashflow_analyzer", "goal_recommender"],
    "strategy": "sequential"
  }
}
```

#### **Backend API Testing Results**

**Cashflow Analyzer Response:**
```json
{
  "analysis": {
    "total": 850,
    "positive": 2500,
    "negative": -1650
  },
  "execution_metadata": {
    "execution_id": "unique_id",
    "basket_name": "working_test",
    "agents_executed": ["cashflow_analyzer"],
    "strategy": "sequential"
  }
}
```

**Goal Recommender Response:**
```json
{
  "recommendations": ["Increase savings", "Reduce expenses"],
  "execution_metadata": {
    "execution_id": "unique_id",
    "basket_name": "goal_test",
    "agents_executed": ["goal_recommender"],
    "strategy": "sequential"
  }
}
```

**Financial Coordinator Response:**
```json
{
  "success": true,
  "transactions": [
    {
      "_id": "6857b29c9e0fee48ea44d7de",
      "amount": 1000,
      "description": "wfh",
      "type": "income",
      "createdAt": "2025-06-22T07:37:00.520Z",
      "__v": 0
    }
  ],
  "execution_metadata": {
    "execution_id": "unique_id",
    "basket_name": "coordinator_test",
    "agents_executed": ["financial_coordinator"],
    "strategy": "sequential"
  }
}
```

#### **Log File Monitoring**
After running tests, check these log files:

**Individual Basket Logs:**
```bash
# View latest basket execution
ls -la logs/basket_runs/
cat logs/basket_runs/working_test_*.log
```

**Application Logs:**
```bash
# View recent application activity
tail -20 logs/application.log
```

**Error Logs (if any issues):**
```bash
# Check for any errors
tail -10 logs/errors.log
```

#### **Performance Metrics**
Typical execution times:
- **Single Agent**: 0.1-2 seconds
- **Chained Execution**: 0.2-5 seconds
- **Financial Coordinator**: 1-30 seconds (depends on external API calls)

#### **Troubleshooting Test Results**

**If Frontend Shows "Input incompatible" Error:**
1. Check that you're using the correct JSON format
2. Ensure JSON is valid (use a JSON validator)
3. Try running without input data (uses defaults)

**If Backend Returns 404 Error:**
1. Check that the basket name exists: `curl http://localhost:8000/baskets`
2. Verify the basket is properly configured
3. Check server logs for detailed error messages

**If Execution Takes Too Long:**
1. Check if MongoDB connection is timing out (this is optional)
2. Verify Redis is running (improves performance)
3. Check network connectivity for financial_coordinator agent

## 🔧 Configuration

### Environment Variables
Create a `.env` file for configuration:
```env
# Database Configuration
MONGODB_URI=mongodb://localhost:27017/ai_integration
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging Configuration
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Agent Configuration
Each agent can be configured through its `agent_spec.json` file:
- **`capabilities.chainable`** - Can be used in baskets
- **`capabilities.memory_access`** - Requires state management
- **`input_schema`** - Defines required input format
- **`output_schema`** - Defines expected output format

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

#### 1. "No module named 'aiohttp'" Error
**Problem:** Financial coordinator agent fails with missing dependency
```bash
{"error":"Basket execution failed: No module named 'aiohttp'"}
```
**Solution:**
```bash
pip install aiohttp
```

#### 2. "Input incompatible" Errors
**Problem:** Agent rejects input data
```bash
{"error":"Basket execution failed: Input incompatible for cashflow_analyzer"}
```
**Solution:** Use correct input format for each agent:
- **cashflow_analyzer**: `{"transactions": [...]}`
- **goal_recommender**: `{"analysis": {...}}`
- **financial_coordinator**: `{"action": "get_transactions"}`

#### 3. Redis Connection Issues
**Problem:** Health check shows `"redis": "disconnected"`
**Solutions:**
```bash
# Option 1: Install Redis with Docker
docker run -d --name ai-redis -p 6379:6379 redis:alpine

# Option 2: Install Redis locally (Windows)
choco install redis-64

# Option 3: Install Redis locally (macOS)
brew install redis && redis-server
```
**Note:** System works without Redis, but performance is better with it.

#### 4. Port 8000 Already in Use
**Problem:** `[Errno 10048] error while attempting to bind on address`
**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>
```

#### 5. Frontend Not Loading
**Problem:** Admin panel doesn't start or shows errors
**Solutions:**
```bash
# Navigate to admin panel directory
cd AI_integration/admin-panel

# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Start development server
npm run dev
```

#### 6. Agent Not Loading
**Problem:** Agent doesn't appear in `/agents` endpoint
**Solutions:**
- Check `agent_spec.json` syntax with JSON validator
- Verify `module_path` matches file structure
- Ensure agent file has `async def process()` function
- Restart the backend server after adding new agents

#### 7. MongoDB Connection Issues
**Problem:** MongoDB shows as disconnected
**Solutions:**
```bash
# Start MongoDB with Docker
docker run -d --name ai-mongodb -p 27017:27017 mongo:latest

# Or check if local MongoDB service is running
# Windows: services.msc -> MongoDB
# macOS: brew services start mongodb-community
```
**Note:** System works without MongoDB, but logs won't be persisted.

### Debug Mode
Enable detailed logging:
```python
# In utils/logger.py, change log level:
console_handler.setLevel(logging.DEBUG)
```

### Validation Commands
```bash
# Test agent registry
python -c "from agents.agent_registry import AgentRegistry; r = AgentRegistry('agents'); print(f'Loaded {len(r.agents)} agents')"

# Test MongoDB connection
python -c "from database.mongo_db import MongoDBClient; m = MongoDBClient(); print(f'MongoDB connected: {m.db is not None}')"

# Test Redis connection
python -c "from utils.redis_service import RedisService; r = RedisService(); print(f'Redis connected: {r.is_connected()}')"

# Validate all agents load correctly
curl http://localhost:8000/agents | python -m json.tool
```

## 🤝 Contributing

1. Follow the agent creation steps above
2. Ensure comprehensive logging in your agents
3. Add proper error handling
4. Test your agent thoroughly
5. Update documentation as needed

## 🎯 Available Agents & Input Formats

### Finance Domain

#### `cashflow_analyzer` ✅ Tested & Working
**Purpose:** Analyzes financial transactions and calculates totals
**Input Format:**
```json
{
  "transactions": [
    {"id": 1, "amount": 1000, "description": "Income"},
    {"id": 2, "amount": -500, "description": "Expense"}
  ]
}
```
**Output:** `{"analysis": {"total": 500, "positive": 1000, "negative": -500}}`

#### `goal_recommender` ✅ Tested & Working
**Purpose:** Provides financial goal recommendations based on analysis
**Input Format:**
```json
{
  "analysis": {
    "total": 500,
    "positive": 1000,
    "negative": -500
  }
}
```
**Output:** `{"recommendations": ["Increase savings"]}`

#### `financial_coordinator` ✅ Tested & Working
**Purpose:** Coordinates financial operations and transactions
**Input Format:**
```json
{
  "action": "get_transactions"
}
```
**Output:** `{"success": true, "transactions": [...]}`
**Note:** Requires `aiohttp` dependency: `pip install aiohttp`

### Automotive Domain
- **`auto_diagnostics`** - Diagnoses vehicle issues from error codes
- **`vehicle_maintenance`** - Schedules and tracks vehicle maintenance
- **`fuel_efficiency`** - Analyzes and improves fuel efficiency

### Education Domain
- **`vedic_quiz_agent`** - Interactive Vedic knowledge quizzes
- **`sanskrit_parser`** - Parses and analyzes Sanskrit text
- **`gurukul_*`** - Various educational agents (anomaly, feedback, trend)

### Workflow Domain
- **`workflow_agent`** - Optimizes business workflows

## 🔄 Available Baskets & Working Examples

### Pre-configured Workflows ✅ Tested & Working

#### `finance_daily_check` - Financial Analysis Chain
**Agents:** cashflow_analyzer → goal_recommender
**Input Format:**
```json
{
  "transactions": [
    {"id": 1, "amount": 2000, "description": "Salary"},
    {"id": 2, "amount": -800, "description": "Rent"},
    {"id": 3, "amount": -200, "description": "Groceries"}
  ]
}
```
**Flow:** Analyzes transactions → Provides goal recommendations
**Test Command:**
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "finance_daily_check",
    "input_data": {
      "transactions": [
        {"id": 1, "amount": 2000, "description": "Salary"},
        {"id": 2, "amount": -800, "description": "Rent"}
      ]
    }
  }'
```

### Other Available Baskets
- **`auto_complete_checkup`** - Complete vehicle analysis (auto_diagnostics → vehicle_maintenance → fuel_efficiency)
- **`gurukul_practice`** - Educational practice session
- **`workflow_optimizer`** - Business workflow optimization

## 🔍 Advanced Usage

### Custom Basket Execution
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "basket_name": "custom_workflow",
      "agents": ["agent1", "agent2"],
      "execution_strategy": "sequential"
    },
    "input_data": {
      "your_data": "here"
    }
  }'
```

### Parallel Execution (Future Feature)
```json
{
    "basket_name": "parallel_analysis",
    "agents": ["agent1", "agent2", "agent3"],
    "execution_strategy": "parallel"
}
```

## 📈 Performance Tips

1. **Use Redis** for better performance and state management
2. **Monitor logs** to identify bottlenecks
3. **Optimize agent logic** for faster execution
4. **Use appropriate execution strategies** (sequential vs parallel)
5. **Implement caching** in agents when appropriate

## 🔐 Security Considerations

1. **Input Validation** - All inputs are validated against schemas
2. **Error Handling** - Sensitive information is not exposed in errors
3. **Logging** - Logs are sanitized to prevent information leakage
4. **Future**: Agent routes will be secured with authentication

## � Quick Start Summary

### Minimal Setup (Backend Only)
```bash
cd AI_integration
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install aiohttp
python main.py
```

### Full Setup (Backend + Frontend + Redis)
```bash
# Terminal 1: Backend
cd AI_integration
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install aiohttp
docker run -d --name ai-redis -p 6379:6379 redis:alpine
python main.py

# Terminal 2: Frontend
cd AI_integration/admin-panel
npm install
npm run dev

# Terminal 3: Test
curl http://localhost:8000/health
# Open http://localhost:5173 in browser
```

### Working Test Commands
```bash
# Test cashflow analyzer
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{"basket_name": "test_cashflow", "input_data": {"transactions": [{"id": 1, "amount": 1000, "description": "Test"}]}}'

# Test chained execution
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{"basket_name": "finance_daily_check", "input_data": {"transactions": [{"id": 1, "amount": 2000, "description": "Salary"}]}}'
```

## �📞 Support

For issues and questions:
1. **Check the troubleshooting section above** - covers all common issues
2. **Review logs** for detailed error messages:
   - `logs/application.log` - General application logs
   - `logs/basket_runs/{basket_name}_{execution_id}.log` - Specific basket execution logs
3. **Verify agent input formats** - each agent has specific requirements
4. **Test with provided working examples** first
5. **Check system health**: `curl http://localhost:8000/health`

### System Status Indicators
- **"status": "healthy"** - All systems working
- **"status": "degraded"** - Some optional services unavailable (Redis/MongoDB)
- **"redis": "connected"** - Enhanced performance enabled
- **"mongodb": "connected"** - Persistent logging enabled

## 📋 **Quick Reference Guide**

### **Essential URLs**
- **Backend API**: http://localhost:8000
- **Frontend Admin Panel**: http://localhost:5173 (check npm output for actual port)
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs (FastAPI auto-docs)

### **Quick Test Commands**

#### **Frontend Testing (Copy-Paste Ready)**
1. **Open**: http://localhost:5173
2. **Select basket**: working_test, goal_test, coordinator_test, or finance_daily_check
3. **Input examples** (paste into "Input Data" field):

**Cashflow Analyzer:**
```json
{"transactions": [{"id": 1, "amount": 2500, "description": "Salary"}, {"id": 2, "amount": -1200, "description": "Rent"}]}
```

**Goal Recommender:**
```json
{"analysis": {"total": 1000, "positive": 100000, "negative": -500}}
```

**Financial Coordinator:**
```json
{"action": "get_transactions"}
```

**Or leave empty for default data!**

#### **Backend Testing (cURL Commands)**

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Test with Custom Data:**
```bash
curl -X POST "http://localhost:8000/run-basket" -H "Content-Type: application/json" -d '{"basket_name": "working_test", "input_data": {"transactions": [{"id": 1, "amount": 1000, "description": "Test"}]}}'
```

**Test with Default Data:**
```bash
curl -X POST "http://localhost:8000/run-basket" -H "Content-Type: application/json" -d '{"basket_name": "working_test"}'
```

**Test Chained Execution:**
```bash
curl -X POST "http://localhost:8000/run-basket" -H "Content-Type: application/json" -d '{"basket_name": "finance_daily_check"}'
```

### **Log Monitoring Commands**
```bash
# Watch real-time logs
tail -f logs/application.log

# View latest basket execution
ls -la logs/basket_runs/ | tail -5

# Check for errors
tail -10 logs/errors.log

# View specific basket log
cat logs/basket_runs/working_test_*.log | tail -20
```

### **Troubleshooting Checklist**
- [ ] Backend running on port 8000
- [ ] Frontend running (check npm output for port)
- [ ] Redis connected (optional but recommended)
- [ ] Valid JSON format in input data
- [ ] Correct basket name selected
- [ ] Check logs for detailed error messages

### **Working Baskets List**
- ✅ **working_test** - Single cashflow analyzer
- ✅ **goal_test** - Single goal recommender
- ✅ **coordinator_test** - Single financial coordinator
- ✅ **finance_daily_check** - Chained: cashflow → goal recommender
- ✅ **chained_test** - Chained: cashflow → goal recommender
- ✅ **multi_agent_test** - Multi-agent workflow

**All baskets work with both custom input data and default data (no input required)!** 🎉

## 🌟 **Enhanced Features**

### **Dual Input Support**
- **Frontend & API Compatible**: All agents work seamlessly from both web interface and API calls
- **Default Data Fallback**: No input required - agents provide sample data automatically
- **Flexible Input Validation**: Agents accept optional parameters with intelligent defaults

### **Advanced Logging System**
- **Individual Basket Logs**: Each execution gets its own detailed log file
- **Real-time Monitoring**: Watch executions in real-time with tail commands
- **Execution Metadata**: Track performance, timing, and execution flow
- **Error Tracking**: Comprehensive error logging with full stack traces

### **Production-Ready Architecture**
- **Redis Integration**: Enhanced performance and caching
- **MongoDB Support**: Persistent logging and data storage (optional)
- **Health Monitoring**: Real-time system status checks
- **Graceful Degradation**: System works even if optional services are unavailable

### **Developer-Friendly**
- **Hot Reload**: Frontend updates automatically during development
- **API Documentation**: Auto-generated docs at `/docs` endpoint
- **Comprehensive Testing**: Both unit tests and integration tests supported
- **Extensible Design**: Easy to add new agents and modify existing ones

### **User Experience**
- **Intuitive Web Interface**: Clean, modern React-based admin panel
- **Copy-Paste Ready Examples**: All sample inputs provided in documentation
- **Instant Feedback**: Real-time execution results and error messages
- **Visual Basket Management**: Create, edit, and run baskets through web UI

This platform is designed for both developers and end-users, providing enterprise-grade reliability with ease of use! 🚀

---

## 🔧 Complete Guide: Adding New AI Agents

### Step 4: Add Environment Variables

Add your API key to the `.env` file:
```env
# Your new agent's API key
YOUR_API_KEY=your_actual_api_key_here

# Other supported AI services
OPENAI_API_KEY=sk-your-openai-key
GROQ_API_KEY=gsk_your-groq-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_AI_API_KEY=your-google-ai-key
```

### Step 5: Create Baskets Using Your Agent

Create `baskets/your_workflow.json`:
```json
{
  "basket_name": "your_workflow",
  "agents": [
    "your_agent_name",
    "another_agent"
  ],
  "execution_strategy": "sequential",
  "description": "Custom workflow with your new agent"
}
```

### Step 6: Test Your Agent

```bash
# Test via API
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "your_workflow",
    "input_data": {
      "input_field": "test input"
    }
  }'
```

## 🔌 AI Service Integration Examples

### OpenAI Integration
```python
from openai import AsyncOpenAI
import os

async def process(input_data: Dict) -> Dict:
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": input_data.get("prompt", "")}]
    )
    return {"result": response.choices[0].message.content}
```

### Groq Integration
```python
from groq import AsyncGroq
import os

async def process(input_data: Dict) -> Dict:
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    response = await client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": input_data.get("prompt", "")}]
    )
    return {"result": response.choices[0].message.content}
```

### Anthropic Integration
```python
import anthropic
import os

async def process(input_data: Dict) -> Dict:
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = await client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": input_data.get("prompt", "")}]
    )
    return {"result": response.content[0].text}
```

### Google AI Integration
```python
import google.generativeai as genai
import os

async def process(input_data: Dict) -> Dict:
    genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model = genai.GenerativeModel('gemini-pro')
    response = await model.generate_content_async(input_data.get("prompt", ""))
    return {"result": response.text}
```

## 🔄 Agent Communication Patterns

### Sequential Execution (Default)
```
Agent A → Agent B → Agent C
```
Data flows from one agent to the next in order.

### Parallel Execution (Supported)
```
        ┌─ Agent B ─┐
Agent A ┤           ├─ Merge Results
        └─ Agent C ─┘
```
Multiple agents process simultaneously.

### Event-Driven Communication
```python
# In your agent implementation
from communication.event_bus import EventBus

async def process(input_data: Dict) -> Dict:
    # Send message to another agent
    await event_bus.publish("target_agent_input", {
        "sender": "your_agent_name",
        "content": {"data": "message"}
    })

    return {"result": "processed"}
```

## 🧺 Available Pre-Built Baskets

### Finance Domain
- **`finance_daily_check`** - Daily financial analysis workflow
  - Agents: `cashflow_analyzer` → `goal_recommender`
  - Input: Transaction data
  - Output: Financial analysis with recommendations

- **`working_test`** - Simple cashflow analysis test
  - Agents: `cashflow_analyzer`
  - Input: Any data (uses sample transactions)
  - Output: Financial analysis

### Multi-Agent Workflows
- **`chained_test`** - Multi-agent financial workflow
  - Agents: `cashflow_analyzer` → `goal_recommender`
  - Demonstrates agent chaining and data flow

### Educational Domain
- **`gurukul_practice`** - Educational practice session
  - Agents: `vedic_quiz_agent` → `sanskrit_parser`
  - Focus: Vedic knowledge and Sanskrit learning

## 🚀 Advanced Features

### State Management
```python
# Stateful agent example
async def process(input_data: Dict) -> Dict:
    # Access previous state
    previous_state = input_data.get("previous_state", {})

    # Process with state
    result = {"processed": "data", "state": {"key": "value"}}

    return result
```

### Error Handling
```python
async def process(input_data: Dict) -> Dict:
    try:
        # Your processing logic
        result = await some_ai_service(input_data)
        return {"result": result}
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return {"error": str(e)}
```

### Input Validation
```python
async def process(input_data: Dict) -> Dict:
    # Validate required fields
    required_fields = ["field1", "field2"]
    for field in required_fields:
        if field not in input_data:
            return {"error": f"Missing required field: {field}"}

    # Process validated input
    return {"result": "processed"}
```

## 📊 Monitoring and Logging

### Comprehensive Logging
- **Application Logs**: `logs/application.log`
- **Error Logs**: `logs/errors.log`
- **Execution Logs**: `logs/executions.log`
- **Individual Basket Logs**: `logs/basket_runs/`

### Health Monitoring
```bash
# Check system health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "socketio": "disabled"
  }
}
```

### Execution Tracking
Every basket execution gets:
- Unique execution ID
- Individual log file
- Performance metrics
- Error tracking
- State persistence

## 🎯 Best Practices

### Agent Development
1. **Always use async/await** for AI service calls
2. **Handle errors gracefully** with try/catch blocks
3. **Log important events** using the provided logger
4. **Validate inputs** before processing
5. **Return consistent output format**

### API Key Security
1. **Never hardcode API keys** in your code
2. **Use environment variables** for all secrets
3. **Add keys to .env file** and .gitignore
4. **Rotate keys regularly** for security

### Performance Optimization
1. **Use Redis caching** for frequently accessed data
2. **Implement connection pooling** for database operations
3. **Monitor execution times** and optimize slow agents
4. **Use parallel execution** when agents are independent

---

## 🎉 Conclusion

The AI Integration Platform provides a **complete solution** for orchestrating multiple AI agents in complex workflows. With its modular architecture, comprehensive logging, and easy integration patterns, you can:

✅ **Integrate any AI service** with standardized patterns
✅ **Create complex workflows** with multiple agents
✅ **Monitor and debug** with comprehensive logging
✅ **Scale horizontally** with Redis and MongoDB
✅ **Manage through web UI** with the React admin panel

**Ready to build your AI agent ecosystem? Start with the Quick Start guide above!** 🚀
