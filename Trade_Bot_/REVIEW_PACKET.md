# REVIEW PACKET - Phase 6 Live Market Behavior Check

Date: 2026-05-09
System: Samruddhi / Trade Bot
Reviewer focus: structured decision support, stop logic, observation, trade management, execution flow, fallback states, and safe-mode behavior.

## Executive Status

The system is partially ready for controlled review.

Working locally:
- Core Python syntax compile passes for prediction, API, HFT execution, shadow execution, and live-execution bridge files.
- HFT verification now passes: fee model, risk throttling, shadow execution, and shadow pipeline routing all execute.
- MCP execution bridge now delegates to `LiveTradingExecutor.place_order()` instead of paper simulation.
- Root health check completes when `PYTHONIOENCODING=utf-8` is set.
- Existing trained model files are present: 25 model artifacts across intraday, short, and long horizons.

Blocked or conditional:
- Today is Saturday, 2026-05-09, so NSE live execution must remain blocked by market-hours controls.
- Local health check reports missing dependencies: `PyJWT` and `scikit-learn`.
- No `.env` file and no `MONGO_URI` are present locally, so real auth database and user demat credential checks cannot be proven in this workspace.
- Real broker order placement cannot be proven without valid Dhan client credentials and an open market session.

## Verified Commands

1. Syntax check:
   `python -m py_compile backend/core/mcp_adapter.py backend/api_server.py backend/market_intelligence.py backend/live_price_validator.py backend/hft2/backend/live_executor.py backend/hft2/backend/broker_adapter.py backend/hft2/backend/mcp_server/tools/execution_tool.py backend/hft2/backend/hft/execution_router.py`

   Result: PASS.

2. HFT verification:
   `python backend/hft2/backend/hft/verify_hft.py`

   Result: PASS after fixes.

   Observed output:
   - Fee model calculated intraday buy, intraday sell, and delivery buy fees.
   - Risk gate blocked after max trades per minute.
   - Risk gate blocked after max loss per minute.
   - Shadow execution filled or partially filled with slippage and fees.
   - Pipeline accepted a tick and routed a shadow order.

3. Health check:
   `$env:PYTHONIOENCODING='utf-8'; python system_health_check.py`

   Result: 6/7 checks passed.

   Remaining issue:
   - Missing packages: `PyJWT`, `scikit-learn`.

4. MCP live bridge unit check:
   Dummy `LiveTradingExecutor.place_order()` returned:
   `DUMMY123 FILLED 2 100.0`

   Result: PASS for bridge wiring. This did not place a real order.

## Exact Demo Flow

Use this flow for a controlled reviewer demo. Keep the first pass in safe/shadow mode unless the market is open and Dhan credentials are confirmed.

1. Start backend.
   - Main API: `backend/api_server.py`
   - HFT backend: `backend/hft2/backend/web_backend.py` when using HFT2 routes.

2. Confirm service health.
   - `GET /tools/health`
   - `GET /api/status`
   - Expected surface: system status, model counts, cache paths, timestamp.

3. Confirm market data.
   - `GET /live/price/RELIANCE.NS`
   - `GET /data/transparency/RELIANCE.NS`
   - Expected surface: live/cached data source, timestamp, market state, freshness, price comparison.

4. Generate decision support.
   - `POST /tools/predict`
   - Example body:
     ```json
     {
       "symbols": ["RELIANCE.NS"],
       "horizon": "intraday",
       "risk_profile": "moderate",
       "stop_loss_pct": 2.0,
       "capital_risk_pct": 1.0,
       "drawdown_limit_pct": 5.0
     }
     ```

5. Review the prediction packet.
   - Show action: LONG, SHORT, or HOLD.
   - Show confidence.
   - Show predicted return.
   - Show current/live price override.
   - Show `decision_support`.
   - Show `plain_language_summary`.
   - Show `data_status`.

6. Explain entry logic.
   - Entry is not an unconditional command.
   - Entry is valid only when action is LONG or SHORT, confidence is acceptable, live price is fresh, market state is normal, and risk filters are not active.
   - HOLD means no trade entry.

7. Explain stop logic.
   - Prediction request carries stop-loss input.
   - Live executor uses configured `stop_loss_pct`, default 5 percent if no config override exists.
   - Short-sell stop is above entry; long stop is below entry.
   - Daily loss and trade count checks must pass before order placement.

8. Show observation.
   - Use data transparency and prediction enrichment.
   - Surface: market context, exhaustion risk, breakout quality, data warnings, live price timestamp.
   - Reviewer should see the system observing before acting.

9. Show trade management.
   - In safe mode: submit a shadow order through HFT pipeline and show fill, slippage, fee impact, and risk-gate behavior.
   - In live mode: order goes through `LiveTradingExecutor.place_order()` and then records to database/portfolio manager.
   - Active orders endpoint: `GET /api/active_orders`.
   - Portfolio endpoint: `GET /api/portfolio` or `GET /api/bot-data`.

10. Show exit reasoning.
   - Exit can be stop loss, take profit, manual sell, daily loss protection, market-hours block, no holding to sell, or broker rejection.
   - For shorts: exit is buy-to-cover before intraday square-off.
   - For longs: exit is sell from current holding.

## Entry Points

Primary API entry points:
- `GET /tools/health`
- `POST /tools/predict`
- `POST /tools/scan_all`
- `POST /tools/analyze`
- `GET /live/price/{symbol}`
- `GET /data/transparency/{symbol}`
- `POST /portfolio/update`

HFT / execution entry points:
- `GET /api/status`
- `GET /api/bot-data`
- `POST /api/order`
- `POST /api/mcp/execute`
- `GET /api/active_orders`
- `POST /api/execute-signal`
- `GET /api/live-status`

Internal execution components:
- `backend/core/mcp_adapter.py`
- `backend/market_intelligence.py`
- `backend/live_price_validator.py`
- `backend/hft2/backend/live_executor.py`
- `backend/hft2/backend/mcp_server/tools/execution_tool.py`
- `backend/hft2/backend/hft/execution_router.py`
- `backend/hft2/backend/hft/pipeline.py`

## Fallback States

Data fallback:
- Cached data is used when historical cache exists.
- Live price validator attempts live source and exposes metadata.
- Data transparency endpoint shows cache/live mismatch.

Prediction fallback:
- If data fetch fails, prediction returns an error per symbol.
- If feature calculation or model training fails, the symbol is skipped or returned with explicit error.
- If prediction fails, response includes a prediction error instead of silent execution.

Execution fallback:
- Market closed: order is rejected before broker placement.
- Missing Dhan credentials: live executor raises clear credential error.
- Broker rejection: order response is marked failed with broker message.
- No holding on sell: sell is rejected.
- Daily trade or loss limit reached: execution is blocked.

System fallback:
- If HFT2 proxy is unreachable, main API returns 503/504.
- If auth DB is missing, auth-dependent endpoints cannot be proven locally.
- If UTF-8 console is not set on Windows, health checker output can crash due Unicode symbols.

## Safe Mode Flow

Safe mode for review means no real broker order.

1. Use HFT shadow pipeline:
   - `HFTPipeline.process_tick()`
   - `HFTPipeline.submit_shadow_order()`

2. Execution router guarantee:
   - `ExecutionRouter` is configured as `SHADOW_ONLY`.
   - `allow_live_broker=False`.
   - Any non-shadow mode raises an exception.

3. Reviewer surface:
   - Tick accepted.
   - Feature vector created with deterministic hash.
   - Risk gate checked.
   - Shadow simulator applies slippage.
   - Fee model calculates Indian-market fees.
   - Order is filled, partially filled, open, or rejected.

4. Safe-mode result:
   - No broker call.
   - No demat impact.
   - Full decision/execution rehearsal is visible.

## Live Execution Sequence

Live execution is permitted only when credentials, market hours, and risk checks pass.

1. User links demat account.
   - Dhan client ID and access token are loaded from user config/MongoDB.

2. Bot initializes live mode.
   - `LiveTradingExecutor` validates credentials are present.
   - Portfolio manager switches to live mode.

3. User requests order.
   - Manual order: `POST /api/order`
   - MCP order: `POST /api/mcp/execute`

4. Pre-trade checks.
   - BUY/SELL enabled flags.
   - Market open.
   - Daily trade count.
   - Daily loss limit.
   - Funds/holding availability.
   - Quantity adjustment.

5. Broker call.
   - `LiveTradingExecutor.place_order()`
   - Dhan `place_order()` is called with symbol, side, quantity, order type, and product type.

6. Post-trade management.
   - Order ID captured.
   - Trade recorded to DB.
   - Pending/executed order state updated.
   - Portfolio state refreshed.
   - Active orders can be queried.

7. Exit.
   - Manual sell, stop loss, take profit, daily protection, broker rejection, or intraday square-off logic.

## Entry, Stop, Observation, Management, Exit

Entry:
- Entry begins with prediction/analyze response, not with direct broker placement.
- Entry should be accepted only when action, confidence, data freshness, market state, and risk checks align.
- HOLD blocks entry.

Stop logic:
- Long stop: below entry, based on configured stop percentage or provided stop level.
- Short stop: above entry, default 3 percent above if not provided.
- Daily loss protection blocks further trading when breached.

Observation:
- Live price metadata, data freshness, market context, breakout/exhaustion risk, and plain-language summary are visible.
- The system explains elevated risk instead of hiding it.

Trade management:
- Shadow mode records fills, fees, slippage, position state, and risk-gate decisions.
- Live mode records broker order IDs, DB trades, pending/executed state, and portfolio changes.

Exit reasoning:
- Exit is explainable by trigger: stop, target, manual sell, no position, market closed, broker rejection, or safety halt.
- For controlled demo, use shadow exit first; use live exit only during open market with verified credentials.

## API, Calculation, Execution Status

API connection:
- Main FastAPI routes compile.
- HFT proxy/main routing compiles.
- Health endpoint available.
- Local auth DB and real Dhan connection not verified because credentials/environment are absent.

Calculation:
- Fee calculation verified through HFT test.
- Risk throttling verified through HFT test.
- Feature vector contract fixed and verified through pipeline test.
- Prediction model artifacts are present.

Execution:
- Shadow execution verified.
- Execution router safe mode verified by code path.
- MCP live bridge verified with dummy executor.
- Real broker execution not performed because today is Saturday and no Dhan credentials are available locally.

## Fixes Applied During Review

- Added `FeeModel` compatibility wrapper for single-leg fee calculations.
- Fixed risk throttle enum from missing `MAX_TRADES_LIMIT` to `MAX_TRADES_MINUTE`.
- Added SELL support to shadow simulator side enum.
- Changed shadow simulator to use `FeeModel` for single-leg fills.
- Added `SlippageModel` compatibility alias.
- Added `QueuePosition` compatibility alias.
- Fixed HFT pipeline regime detector call, feature vector creation, feature hash, and regime mapping.
- Initialized MCP execution order stores.
- Replaced MCP paper-simulation live path with a real bridge to `LiveTradingExecutor.place_order()`.

## Reviewer Checklist

- [x] Exact demo flow documented.
- [x] Entry points documented.
- [x] Fallback states documented.
- [x] Safe mode flow documented.
- [x] Live execution sequence documented.
- [x] Entry/stop/observation/management/exit reasoning documented.
- [x] Local shadow execution verified.
- [x] MCP live bridge verified with dummy executor.
- [ ] Real broker connection verified with valid Dhan credentials.
- [ ] Live market order verified during NSE market hours.
- [ ] Missing dependencies installed: `PyJWT`, `scikit-learn`.

## Final Readiness Decision

Safe/shadow demo: READY.

Live market execution demo: CONDITIONALLY READY. It requires:
- NSE market open.
- Valid Dhan client ID and access token.
- Required dependencies installed.
- `.env`/MongoDB/user config available.
- Human approval before any live order.
