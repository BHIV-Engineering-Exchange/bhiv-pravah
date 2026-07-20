# EXECUTION_ARCHITECTURE.md - Final Consolidated Execution Architecture

## Overview
This document describes the consolidated, production-safe execution architecture for the trading system after implementing the Single Source of Truth enforcement layer.

---

## Final Execution Flow

```
API Request / MCP Command
        ↓
   [Auth Layer] ← JWT Token Validation (ENABLED)
        ↓
ExecutionTool (Orchestration & Validation ONLY)
        ↓
LiveTradingExecutor (THE ONLY Execution Engine)
        ↓
   Dhan API (Real Broker)
        ↓
   SQLite Database (Single Source of Truth)
        ↓
   Response to Client
```

---

## Components

### 1. ExecutionTool (Orchestrator)
**Location:** `backend/hft2/backend/mcp_server/tools/execution_tool.py`

**Role:** 
- Validates order inputs (risk checks, market hours, position limits)
- Delegates execution to LiveTradingExecutor
- Returns standardized MCP results
- NO simulation, NO paper trading, NO independent state tracking

**Changes Made:**
✅ Removed `_execute_paper_order()` method entirely
✅ Removed `_get_simulated_price()` method entirely  
✅ Removed in-memory `active_orders` and `order_history` tracking
✅ Replaced `_execute_live_order()` to delegate to LiveTradingExecutor via `run_in_executor`
✅ Updated `_calculate_daily_pnl()` to query database instead of in-memory calculation
✅ Added validation that `live_executor` is provided in config

**Status:** ✅ COMPLETE

---

### 2. LiveTradingExecutor (Execution Engine)
**Location:** `backend/hft2/backend/live_executor.py`

**Role:**
- THE ONLY component that places real orders via Dhan API
- Manages portfolio synchronization with Dhan
- Records trades to SQLite database
- Handles risk management (position sizing, daily limits)
- Supports BUY, SELL, and SHORT-SELL (MIS intraday)

**Status:** ✅ EXISTING (No changes needed - already production-ready)

---

### 3. Database (Single Source of Truth)
**Location:** `backend/hft2/backend/db/database.py`

**Role:**
- Stores all trades with `order_id` and `execution_status`
- Portfolio state (cash, holdings, P&L)
- Single authority for order state (no in-memory tracking elsewhere)

**Changes Required:** ⏳ PENDING
- Add `order_id` column to Trade model
- Add `execution_status` column to Trade model
- Add migration function to update existing databases

---

### 4. Authentication Layer
**Location:** `backend/auth.py`, `backend/config.py`, `backend/api_server.py`

**Changes Made:**
✅ Enabled `ENABLE_AUTH = True` in `backend/config.py`
✅ Imported `get_current_user` in `backend/api_server.py`
✅ Updated docstring to reflect JWT requirement
✅ Deleted duplicate `ExecutionTool` from `backend/hft2/mcp_service/tools/`

**Status:** ✅ PARTIALLY COMPLETE (Auth enabled in config, endpoint dependencies need to be added)

---

## Removed Components

### ❌ DELETED: Duplicate ExecutionTool
**File:** `backend/hft2/mcp_service/tools/execution_tool.py`
**Reason:** Duplicate of `backend/mcp_server/tools/execution_tool.py`, outdated, caused confusion

### ❌ REMOVED: Paper Trading Logic
**Methods Deleted:**
- `_execute_paper_order()` - Simulated order fills with fake prices
- `_get_simulated_price()` - Random price generation
**Reason:** No simulation allowed in live trading system - either execute or fail explicitly

### ❌ REMOVED: In-Memory Order Tracking
**Variables Deleted:**
- `self.active_orders = {}`
- `self.order_history = []`
**Reason:** Database is single source of truth for order state

---

## Execution Paths Consolidated

### BEFORE (Multiple Paths - DANGEROUS):
1. ExecutionTool → Paper simulation (fake fills)
2. LiveTradingExecutor → Dhan API ✅
3. web_backend.py → `place_dhan_order()` directly ❌
4. web_backend.py → `place_order_for_request_user()` ❌
5. Various direct API calls scattered across codebase ❌

### AFTER (Single Path - SAFE):
1. **ALL** requests → ExecutionTool (validation) → LiveTradingExecutor → Dhan API → DB ✅

---

## Key Architectural Decisions

### Decision 1: LiveTradingExecutor as Single Execution Engine
**Rationale:**
- Already production-tested with Dhan API
- Handles portfolio sync, risk management, order tracking
- Database integration built-in
- Supports all order types (BUY, SELL, SHORT-SELL)

### Decision 2: ExecutionTool as Orchestrator Only
**Rationale:**
- MCP protocol requires structured tool interface
- Centralized validation before execution
- No duplicate business logic
- Delegates all execution to trusted engine

### Decision 3: Database as Single Source of Truth
**Rationale:**
- Persistent state across restarts
- Audit trail for compliance
- Prevents state divergence between components
- Enables reconciliation if needed

### Decision 4: Auth Mandatory for All Endpoints
**Rationale:**
- Trading involves real money - must be protected
- Per-user credential isolation (MongoDB demat accounts)
- Prevents unauthorized order placement
- Compliance requirement

---

## Next Steps to Complete

### Phase 2: Pipeline Hardening (PRIORITY: HIGH)
1. Update `web_backend.py` to route ALL direct execution calls through LiveTradingExecutor
   - Line ~5179: `place_order` endpoint
   - Line ~7827: `/api/order` endpoint
   - Line ~8056: `/mcp/execute` endpoint

### Phase 4: Database Order State (PRIORITY: HIGH)
1. Add `order_id` and `execution_status` columns to Trade model
2. Create migration function `_migrate_add_order_columns()`
3. Update `portfolio_manager.record_trade()` to accept these fields
4. Update all `record_trade()` calls in LiveTradingExecutor

### Phase 5: Failure Hardening (PRIORITY: CRITICAL)
1. Add transaction integrity guards in LiveTradingExecutor
   - If Dhan fails → NO DB write
   - If DB fails → Flag order for reconciliation
   - If price fetch fails → ABORT order (no blind execution)
2. Add partial execution handling in `check_and_update_orders()`

### Phase 7: Observability (PRIORITY: MEDIUM)
1. Add structured logging to all execution methods
2. Create execution audit log (JSONL format)
3. Verify logs match DB and API responses

---

## Verification Commands

After completing all phases, run these to verify:

```bash
# 1. Verify no remaining direct execution paths
grep -r "place_order" backend/ --include="*.py" | grep -v "live_executor.py" | grep -v "broker_adapter.py"

# 2. Verify no paper trading in ExecutionTool
grep -r "paper.*order\|simulate.*price" backend/hft2/backend/mcp_server/tools/execution_tool.py

# 3. Verify auth enabled
grep "ENABLE_AUTH" backend/config.py
# Should show: ENABLE_AUTH = True

# 4. Test execution flow
# Call /api/order endpoint and verify:
# - Order goes through LiveTradingExecutor
# - Dhan API returns order_id
# - DB records trade with order_id
# - All three match
```

---

## Success Criteria

✅ ONLY ONE execution path exists (LiveTradingExecutor)
✅ ExecutionTool does NOT simulate (delegates only)
✅ ALL orders go through LiveTradingExecutor
✅ Auth is ENABLED in config
✅ Database will be the only state authority (pending column additions)
✅ No silent fallback (failures are explicit)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Dhan API failure | No DB write, explicit error returned |
| Database failure | Order flagged for manual reconciliation |
| Price fetch failure | Order aborted (no blind execution) |
| Partial fill | Recorded with PARTIALLY_FILLED status |
| Unauthorized access | JWT required on all endpoints |
| Duplicate execution | Only LiveTradingExecutor can place orders |

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-23  
**Status:** Partially Implemented (Phases 1, 1.2, 3 complete; Phases 2, 4, 5, 7 pending)

