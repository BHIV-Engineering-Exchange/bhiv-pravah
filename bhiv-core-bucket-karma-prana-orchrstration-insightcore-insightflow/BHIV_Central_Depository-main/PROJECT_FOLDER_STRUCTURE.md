# 📁 COMPLETE PROJECT FOLDER STRUCTURE

## 🌳 Full Directory Tree (Root to Depth)

```
BHIV_Central_Depository-main/
│
├── 📂 agents/                                    # AI Agent Implementations
│   ├── 📄 agent_registry.py                     # Agent discovery & registration system
│   ├── 📄 agent_runner.py                       # Agent execution engine with state management
│   ├── 📄 base_agent.py                         # Base class for agent implementations
│   │
│   ├── 📂 auto_diagnostics/                     # Automotive diagnostics agent
│   │   ├── 📄 agent_spec.json                   # Agent metadata & schema
│   │   └── 📄 auto_diagnostics.py               # Agent implementation
│   │
│   ├── 📂 cashflow_analyzer/                    # Financial transaction analyzer
│   │   ├── 📄 agent_spec.json
│   │   └── 📄 cashflow_analyzer.py
│   │
│   ├── 📂 financial_coordinator/                # Financial operations coordinator
│   │   ├── 📄 agent_spec.json
│   │   └── 📄 financial_coordinator.py
│   │
│   ├── 📂 fuel_efficiency/                      # Vehicle fuel optimization
│   │   └── 📄 agent_spec.json
│   │
│   ├── 📂 goal_recommender/                     # Financial goal recommendations
│   │   ├── 📄 agent_spec.json
│   │   └── 📄 goal_recommender.py
│   │
│   ├── 📂 gurukul/                              # Education domain agents
│   │   ├── 📄 __init__.py
│   │   │
│   │   ├── 📂 gurukul_anomaly/                  # Anomaly detection
│   │   │   ├── 📄 agent_spec.json
│   │   │   └── 📄 gurukul_anomaly.py
│   │   │
│   │   ├── 📂 gurukul_feedback/                 # Feedback processing
│   │   │   ├── 📄 agent_spec.json
│   │   │   └── 📄 gurukul_feedback.py
│   │   │
│   │   └── 📂 gurukul_trend/                    # Trend analysis
│   │       ├── 📄 agent_spec.json
│   │       └── 📄 gurukul_trend.py
│   │
│   ├── 📂 law_agent/                            # Legal query processing
│   │   ├── 📄 agent_spec.json
│   │   ├── 📄 law_agent.py
│   │   └── 📄 law_agent_ui.html                 # UI for law agent
│   │
│   ├── 📂 sanskrit_parser/                      # Sanskrit text analysis
│   │   ├── 📄 agent_spec.json
│   │   └── 📄 sanskrit_parser.py
│   │
│   ├── 📂 textToJson/                           # Text to JSON conversion
│   │   ├── 📄 agent_spec.json
│   │   ├── 📄 main_api.py
│   │   └── 📄 text_to_json.py
│   │
│   ├── 📂 vedic_quiz_agent/                     # Interactive Vedic quizzes
│   │   ├── 📄 agent_spec.json
│   │   └── 📄 vedic_quiz_agent.py
│   │
│   ├── 📂 vehicle_maintenance/                  # Vehicle maintenance scheduling
│   │   ├── 📄 agent_spec.json
│   │   └── 📄 vehicle_maintenance.py
│   │
│   └── 📂 workflow/                             # Business workflow optimization
│       ├── 📄 agent_spec.json
│       ├── 📄 ai_agent.py
│       └── 📄 workflow_main.py
│
├── 📂 admin-panel/                              # React Frontend Admin Interface
│   ├── 📂 public/                               # Static assets
│   │   └── 📄 vite.svg
│   │
│   ├── 📂 src/                                  # Source code
│   │   ├── 📂 assets/                           # Images & static files
│   │   │   └── 📄 react.svg
│   │   │
│   │   ├── 📂 components/                       # React components
│   │   │   ├── 📄 AdminDashboard.jsx            # Main dashboard
│   │   │   ├── 📄 AdminDashboard.css
│   │   │   ├── 📄 AgentRunner.jsx               # Single agent executor
│   │   │   ├── 📄 AgentRunner.css
│   │   │   ├── 📄 AgentsList.jsx                # Agent listing view
│   │   │   ├── 📄 AgentsList.css
│   │   │   ├── 📄 BasketCreator.jsx             # Create new baskets
│   │   │   ├── 📄 BasketCreator.css
│   │   │   ├── 📄 BasketRunner.jsx              # Execute baskets
│   │   │   ├── 📄 BasketRunner.css
│   │   │   ├── 📄 BasketsList.jsx               # Basket listing view
│   │   │   ├── 📄 BasketsList.css
│   │   │   ├── 📄 DarkModeToggle.jsx            # Theme switcher
│   │   │   └── 📄 DarkModeToggle.css
│   │   │
│   │   ├── 📂 services/                         # API client layer
│   │   │   └── 📄 api.js                        # HTTP service for backend
│   │   │
│   │   ├── 📄 App.jsx                           # Root component
│   │   ├── 📄 App.css
│   │   ├── 📄 index.css                         # Global styles
│   │   └── 📄 main.jsx                          # Entry point
│   │
│   ├── 📄 .gitignore
│   ├── 📄 eslint.config.js                      # ESLint configuration
│   ├── 📄 index.html                            # HTML template
│   ├── 📄 package.json                          # NPM dependencies
│   ├── 📄 package-lock.json
│   ├── 📄 README.md                             # Frontend documentation
│   ├── 📄 README_ADMIN_PANEL.md
│   └── 📄 vite.config.js                        # Vite build config
│
├── 📂 baskets/                                  # Workflow Definitions
│   ├── 📄 basket_manager.py                     # Basket orchestration engine
│   ├── 📄 Cashflow + Law agnet.json             # Combined workflow
│   ├── 📄 chained_test.json                     # Chained agent test
│   ├── 📄 coordinator_test.json                 # Coordinator test
│   ├── 📄 enhanced_logging_test.json            # Logging test
│   ├── 📄 error_logging_test.json               # Error handling test
│   ├── 📄 final_logging_test.json               # Final logging test
│   ├── 📄 finance_daily_check.json              # Daily financial workflow
│   ├── 📄 financial_operations.json             # Financial ops workflow
│   ├── 📄 goal_test.json                        # Goal recommender test
│   ├── 📄 gurukul_practice.json                 # Education workflow
│   ├── 📄 Law agent.json                        # Law agent workflow
│   ├── 📄 law_agent_test.json                   # Law agent test
│   ├── 📄 multi_agent_test.json                 # Multi-agent test
│   ├── 📄 test_basket.json                      # General test basket
│   ├── 📄 test_cashflow.json                    # Cashflow test
│   ├── 📄 text_to_json_test.json                # Text conversion test
│   ├── 📄 textTOjson.json                       # Text to JSON workflow
│   ├── 📄 workflow_optimizer.json               # Workflow optimization
│   └── 📄 working_test.json                     # Working test basket
│
├── 📂 cli_tool/                                 # Command Line Interface
│   └── 📄 agent_cli.py                          # CLI for agent management
│
├── 📂 communication/                            # Inter-Agent Communication
│   └── 📄 event_bus.py                          # Pub/Sub event system
│
├── 📂 database/                                 # Database Layer
│   └── 📄 mongo_db.py                           # MongoDB client & operations
│
├── 📂 docs/                                     # Documentation
│   ├── 📄 DATABASE_TEST_README.md               # Database testing guide
│   ├── 📄 integration_notes.md                  # Integration notes
│   ├── 📄 SUPABASE_SETUP_README.md              # Supabase setup guide
│   ├── 📄 SUPABASE_STORAGE_README.md            # Storage configuration
│   └── 📄 TASK_LOGGER_README.md                 # Task logging guide
│
├── 📂 integration/                              # External integrations
│   ├── 📄 app.js                                # Integration app
│   ├── 📄 index.html                            # Integration UI
│   ├── 📄 package.json
│   ├── 📄 package-lock.json
│   ├── 📄 server.js                             # Integration server
│   └── 📄 style.css
│
├── 📂 logs/                                     # Application Logs (Generated)
│   ├── 📄 application.log                       # Main application log
│   ├── 📄 errors.log                            # Error-only log
│   ├── 📄 executions.log                        # Execution tracking log
│   └── 📂 basket_runs/                          # Individual basket logs
│       └── 📄 {basket_name}_{execution_id}.log  # Per-execution logs
│
├── 📂 scripts/                                  # Utility Scripts
│   ├── 📂 supabase/                             # Supabase scripts
│   │   ├── 📄 backup_schedule.js                # Backup automation
│   │   ├── 📄 execute_sql.js                    # SQL execution
│   │   ├── 📄 generate_lead_report.js           # Report generation
│   │   ├── 📄 production_readiness.js           # Production checks
│   │   ├── 📄 supabase_setup.js                 # Initial setup
│   │   └── 📄 supabase_storage_setup.js         # Storage setup
│   │
│   └── 📂 utils/                                # Utility scripts
│       ├── 📄 sample_task_logging.js            # Logging examples
│       └── 📄 task_logger.js                    # Task logger utility
│
├── 📂 test_results/                             # Test Output
│   └── 📄 junit.xml                             # JUnit test results
│
├── 📂 tests/                                    # Test Suite
│   ├── 📂 sample_inputs/                        # Test input data
│   │   ├── 📄 cashflow_analyzer_input.json
│   │   ├── 📄 financial_coordinator_input.json
│   │   ├── 📄 goal_recommender_input.json
│   │   ├── 📄 sanskrit_parser_input.json
│   │   └── 📄 vedic_quiz_agent_input.json
│   │
│   ├── 📂 test_results/                         # Test results
│   │   ├── 📄 db_test_report_*.json             # Database test reports
│   │   └── ...
│   │
│   ├── 📄 __init__.py
│   ├── 📄 requirements.txt                      # Test dependencies
│   ├── 📄 run_tests.py                          # Test runner
│   ├── 📄 supabase_db_tests.js                  # Database tests
│   ├── 📄 test_basket_manager.py                # Basket tests
│   ├── 📄 test_integration.py                   # Integration tests
│   ├── 📄 test_redis_service.py                 # Redis tests
│   ├── 📄 test_results.json                     # Test results
│   ├── 📄 test_setup.js                         # Test setup
│   ├── 📄 test_teardown.js                      # Test cleanup
│   └── 📄 TESTING_DOCUMENTATION.md              # Testing guide
│
├── 📂 utils/                                    # Utility Modules
│   ├── 📄 logger.py                             # Centralized logging system
│   └── 📄 redis_service.py                      # Redis client & operations
│
├── 📄 .gitignore                                # Git ignore rules
├── 📄 agents_and_baskets.yaml                   # Agent/basket configuration
├── 📄 auto_fix.js                               # Auto-fix utility
├── 📄 BUGS_AND_ERRORS.md                        # Known issues
├── 📄 check_database.js                         # Database checker
├── 📄 COMPREHENSIVE_PROJECT_ANALYSIS.md         # Full project analysis
├── 📄 create_evaluations_table.sql              # SQL schema
├── 📄 create_iterations_table.sql               # SQL schema
├── 📄 create_specs_table.sql                    # SQL schema
├── 📄 docker-compose.yml                        # Docker configuration
├── 📄 execute_fix.js                            # Fix executor
├── 📄 fix_foreign_keys.sql                      # SQL fixes
├── 📄 main.py                                   # 🚀 FastAPI Server Entry Point
├── 📄 PROJECT_STATUS.md                         # Project status report
├── 📄 readme.md                                 # Main documentation
├── 📄 requirements.txt                          # Python dependencies
├── 📄 STARTUP_GUIDE.md                          # Startup instructions
├── 📄 supabase_credentials_*.enc                # Encrypted credentials
├── 📄 SUPABASE_SUCCESS_REPORT.md                # Supabase report
├── 📄 test_complete_system.py                   # System test
├── 📄 test_law_agent_api.py                     # Law agent test
├── 📄 test_law_agent_integration.py             # Law agent integration
├── 📄 test_logging_system.py                    # Logging test
└── 📄 view_data.js                              # Data viewer
```

---

## 📊 Folder Purpose Summary

### **Core Application Folders**

| Folder | Purpose | Key Files |
|--------|---------|-----------|
| `agents/` | AI agent implementations | `agent_registry.py`, `agent_runner.py`, `base_agent.py` |
| `baskets/` | Workflow definitions | `basket_manager.py`, `*.json` configs |
| `utils/` | Shared utilities | `logger.py`, `redis_service.py` |
| `database/` | Database layer | `mongo_db.py` |
| `communication/` | Event system | `event_bus.py` |

### **Frontend Folders**

| Folder | Purpose | Key Files |
|--------|---------|-----------|
| `admin-panel/` | React frontend | Root of frontend app |
| `admin-panel/src/components/` | UI components | `BasketRunner.jsx`, `AgentsList.jsx` |
| `admin-panel/src/services/` | API client | `api.js` |

### **Configuration & Documentation**

| Folder | Purpose | Key Files |
|--------|---------|-----------|
| `docs/` | Documentation | Setup guides, integration notes |
| `tests/` | Test suite | Test files, sample inputs |
| `scripts/` | Utility scripts | Supabase scripts, utilities |

### **Generated/Runtime Folders**

| Folder | Purpose | Generated By |
|--------|---------|--------------|
| `logs/` | Application logs | Logger system |
| `logs/basket_runs/` | Individual basket logs | BasketManager |
| `test_results/` | Test outputs | Test runner |

---

## 🎯 Key File Locations Quick Reference

### **Entry Points**
- **Backend Server**: `main.py` (Port 8000)
- **Frontend App**: `admin-panel/src/main.jsx` (Port 5173)

### **Core Logic**
- **Agent Discovery**: `agents/agent_registry.py`
- **Agent Execution**: `agents/agent_runner.py`
- **Workflow Orchestration**: `baskets/basket_manager.py`
- **Logging System**: `utils/logger.py`
- **Redis Operations**: `utils/redis_service.py`
- **MongoDB Operations**: `database/mongo_db.py`

### **Configuration**
- **Environment Variables**: `.env` (create from template)
- **Agent/Basket Config**: `agents_and_baskets.yaml`
- **Python Dependencies**: `requirements.txt`
- **Frontend Dependencies**: `admin-panel/package.json`

### **Agent Specifications**
- **Pattern**: `agents/{agent_name}/agent_spec.json`
- **Implementation**: `agents/{agent_name}/{agent_name}.py`

### **Basket Definitions**
- **Location**: `baskets/{basket_name}.json`
- **Format**: JSON with agents array and execution strategy

---

## 📝 File Naming Conventions

### **Agents**
```
agents/{agent_name}/
├── agent_spec.json      # Lowercase, underscore-separated
└── {agent_name}.py      # Matches folder name
```

### **Baskets**
```
baskets/{basket_name}.json   # Lowercase, underscore-separated
```

### **Components**
```
admin-panel/src/components/
├── ComponentName.jsx        # PascalCase
└── ComponentName.css        # Matches JSX name
```

### **Logs**
```
logs/
├── application.log          # Static name
├── errors.log              # Static name
├── executions.log          # Static name
└── basket_runs/
    └── {basket_name}_{timestamp}_{uuid}.log  # Dynamic
```

---

## 🔍 How to Navigate the Project

### **To Add a New Agent**
1. Navigate to: `agents/`
2. Create folder: `agents/new_agent/`
3. Add files: `agent_spec.json`, `new_agent.py`

### **To Create a Basket**
1. Navigate to: `baskets/`
2. Create file: `baskets/new_basket.json`

### **To Modify Frontend**
1. Navigate to: `admin-panel/src/components/`
2. Edit component: `ComponentName.jsx`

### **To Check Logs**
1. Navigate to: `logs/`
2. View: `application.log` or `basket_runs/{basket}_{id}.log`

### **To Run Tests**
1. Navigate to: `tests/`
2. Run: `python run_tests.py`

---

## 📦 Dependencies Location

### **Backend Dependencies**
- **File**: `requirements.txt` (root)
- **Install**: `pip install -r requirements.txt`

### **Frontend Dependencies**
- **File**: `admin-panel/package.json`
- **Install**: `cd admin-panel && npm install`

### **Test Dependencies**
- **File**: `tests/requirements.txt`
- **Install**: `pip install -r tests/requirements.txt`

---

## 🎨 Visual Folder Hierarchy

```
ROOT (BHIV_Central_Depository-main)
│
├── BACKEND (Python/FastAPI)
│   ├── agents/          → AI Agents
│   ├── baskets/         → Workflows
│   ├── utils/           → Utilities
│   ├── database/        → DB Layer
│   ├── communication/   → Events
│   └── main.py          → Server
│
├── FRONTEND (React/Vite)
│   └── admin-panel/
│       └── src/
│           ├── components/  → UI
│           └── services/    → API
│
├── INFRASTRUCTURE
│   ├── logs/            → Runtime logs
│   ├── tests/           → Test suite
│   ├── scripts/         → Utilities
│   └── docs/            → Documentation
│
└── CONFIGURATION
    ├── .env             → Environment
    ├── requirements.txt → Python deps
    └── *.yaml, *.json   → Configs
```

---

## ✅ Folder Structure Checklist

Use this to verify your project structure:

- [ ] `agents/` contains agent folders with `agent_spec.json`
- [ ] `baskets/` contains `basket_manager.py` and `*.json` files
- [ ] `admin-panel/src/` contains `components/` and `services/`
- [ ] `utils/` contains `logger.py` and `redis_service.py`
- [ ] `logs/` directory exists (created automatically)
- [ ] `main.py` exists in root
- [ ] `requirements.txt` exists in root
- [ ] `.env` file created (from template)

---

**This structure supports**:
✅ Easy agent addition  
✅ Clear separation of concerns  
✅ Scalable architecture  
✅ Simple navigation  
✅ Maintainable codebase
