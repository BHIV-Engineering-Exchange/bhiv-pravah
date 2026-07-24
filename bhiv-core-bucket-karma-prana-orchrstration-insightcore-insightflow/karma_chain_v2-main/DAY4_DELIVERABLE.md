# DAY 4 DELIVERABLE - FAST-FORWARD NPC KARMA SIMULATION

## Files Created/Modified

### 1. scripts/fast_forward_npc_simulation.py
- **Purpose**: Implements NPC/simulated character with deterministic seed
- **Features**:
  - **Deterministic seed**: Reproducible simulation runs
  - **Time control**: Supports 2X, 5X, 10X, 20X speeds
  - **Karma evolution**: Tracks karma accumulation over time
  - **Signal emission**: Shows signals emitted during simulation
  - **Death event**: Triggers when karma falls below threshold
  - **Rebirth**: Occurs when karma improves significantly
  - **Carryover**: Sanchita → Prarabdha karma transfer between lives

### 2. NPCKarmaSimulator Class
- Simulates karma lifecycle for NPC characters
- Tracks karma history and events
- Processes death and rebirth events
- Emits canonical karma signals
- Integrates with Core authorization for irreversible actions

### 3. Speed Control
- **2X Speed**: Doubles simulation rate
- **5X Speed**: 5x faster processing
- **10X Speed**: 10x faster processing (demo speed)
- **20X Speed**: Maximum speed simulation

## Simulation Features

- **NPC Generation**: Creates deterministic NPC characters
- **Action Simulation**: Simulates various positive/negative actions
- **Karma Tracking**: Monitors karma score and band changes
- **Signal Monitoring**: Tracks all signals emitted
- **Lifecycle Events**: Death and rebirth processing
- **Karmic Carryover**: Sanchita karma transfer between lives

## Demo Instructions

To run the demo with 2 lives at ≥10X speed:

```bash
cd karma-tracker
python scripts/fast_forward_npc_simulation.py --demo
```

Or directly:
```bash
python -c "import asyncio; exec(open('scripts/fast_forward_npc_simulation.py').read()); asyncio.run(demo_two_lives_at_speed(speed=10.0))"
```

## Verification

- ✅ NPC simulation with deterministic seed
- ✅ Time control at 2X, 5X, 10X, 20X speeds
- ✅ Visible karma score evolution over time
- ✅ Signal emission tracking
- ✅ Death event triggering
- ✅ Rebirth processing
- ✅ Sanchita → Prarabdha carryover between lives
- ✅ Clear CLI output with timestamps