# ATHARVA_RUNTIME_CONTRACT_SPEC.md

**Phase 2 Deliverable — Contract Schema Design**
**Sprint: Arbitrary Contract Execution**
**Version: 1.0.0**

---

## Purpose

This document defines the generic execution contract that Atharva must
accept to execute any scenario without requiring new runtime code.

A contract submitted to Atharva must be self-contained. The runtime
reads it, constructs execution from it, and produces artifacts from it.
No demo selection. No scenario-specific code path. No template lookup.

---

## Design Principles

1. **No game_mode field** — game_mode is a demo selector, not a runtime
   parameter. It does not exist in this contract.

2. **No domain inference** — domain and scenario are metadata only.
   The runtime derives zero behavior from them.

3. **Entity type is open** — any string is a valid entity type. The
   runtime does not restrict to vessel/player/enemy/obstacle.

4. **All behavior is declared** — every behavior script and its
   parameters must be explicitly listed. Nothing is inferred from
   entity type or domain.

5. **All transitions are declared** — state transitions come from
   contract rules, not from code branches.

6. **All consequences are declared** — consequence rules live in the
   contract, not in a static rules file loaded at startup.

7. **Termination is declared** — the contract says when execution ends.
   The runtime does not decide this on its own.

8. **Fail-closed validation** — any missing required field rejects the
   contract before execution begins.

---

## Top-Level Contract Structure

```json
{
  "identity":    { ... },
  "entities":    [ ... ],
  "environment": { ... },
  "behaviors":   [ ... ],
  "transitions": [ ... ],
  "consequences":[ ... ],
  "termination": { ... },
  "telemetry":   { ... },
  "governance":  { ... }
}



Section 1 — identity
Required. Identifies this contract instance uniquely across the
entire system. Used for trace continuity, replay, and artifact lineage.

"identity": {
  "trace_id":     "trace_maritime_patrol_001",
  "execution_id": "exec_1720000000000_a1b2c3d4",
  "domain":       "maritime",
  "scenario":     "patrol_route",
  "version":      "1.0.0",
  "created_at":   1720000000000
}


Field	Required	Type	Description
trace_id	Yes	string	Globally unique. Flows through all artifacts and replay. Never mutated.
execution_id	Yes	string	Unique per execution run. One trace can have multiple executions.
domain	Yes	string	Metadata only. No logic derived from this. e.g. maritime, drone, logistics
scenario	Yes	string	Metadata only. No logic derived from this. e.g. patrol_route, swarm_scan
version	No	string	Contract schema version. Defaults to "1.0.0"
created_at	No	integer	Unix ms timestamp of contract creation
Rules:

trace_id and execution_id are mandatory. Contract is rejected without them.

domain and scenario are free strings. The runtime reads them as labels only.

No field in identity controls execution behavior.

Section 2 — entities
Required. Non-empty array.
Declares every entity that exists in the simulation. The runtime spawns
exactly what is listed here — no more, no less.

"entities": [
  {
    "id":        "vessel_alpha",
    "type":      "vessel",
    "position":  [25.10, 0.0, 55.20],
    "rotation":  [0.0, 45.0, 0.0],
    "velocity":  [0.0, 0.0, 0.0],
    "state":     "active",
    "behaviors": ["patrol_waypoints"],
    "meta": {
      "speed_knots": 14,
      "heading":     45,
      "callsign":    "ALPHA-01"
    }
  },
  {
    "id":        "restricted_zone_north",
    "type":      "zone",
    "position":  [25.30, 0.0, 55.35],
    "rotation":  [0.0, 0.0, 0.0],
    "velocity":  [0.0, 0.0, 0.0],
    "state":     "active",
    "behaviors": [],
    "meta": {
      "radius": 15.0,
      "label":  "Northern Exclusion Zone"
    }
  }
]


Field	Required	Type	Description
id	Yes	string	Unique within this contract. Alphanumeric, underscore, hyphen only.
type	Yes	string	Open string. Any value is accepted. vessel, drone, vehicle, sensor, zone, node, agent, marker — all valid.
position	Yes	number[3]	[x, y, z] world coordinates.
rotation	No	number[3]	[rx, ry, rz] in degrees. Defaults to [0, 0, 0].
velocity	No	number[3]	[vx, vy, vz] initial velocity. Defaults to [0, 0, 0].
state	No	string	Initial state. Defaults to "active". Any string accepted — runtime does not restrict states.
behaviors	No	string[]	List of behavior IDs from the behaviors section assigned to this entity.
meta	No	object	Arbitrary domain data. Passed through unchanged. Runtime derives no logic from this.
Rules:

entity.id must be unique within the contract.

entity.type is an open string — no enum restriction.

entity.state is an open string — no enum restriction.

behaviors[] references IDs declared in the behaviors section.

A zone entity must have meta.radius set for zone detection to work.

Section 3 — environment
Optional.
Declares physical simulation parameters. If omitted, defaults apply.
No game_mode. No scene_id. No skybox. Those are rendering concerns —
not runtime concerns.

"environment": {
  "gravity":        [0.0, 0.0, 0.0],
  "friction":       0.1,
  "bounce":         0.0,
  "air_resistance": 0.05,
  "tick_rate":      1,
  "collision_radius": 1.0
}


Field	Required	Type	Default	Description
gravity	No	number[3]	[0, -9.8, 0]	Gravity vector. Use [0,0,0] for maritime or drone domains.
friction	No	number	0.5	Surface friction coefficient 0–1.
bounce	No	number	0.3	Restitution coefficient 0–1.
air_resistance	No	number	0.1	Drag coefficient 0–1.
tick_rate	No	integer	1	Ticks per second (used for telemetry timestamp calculation).
collision_radius	No	number	1.0	Sphere radius used for collision detection between entities.
Rules:

All fields are optional with documented defaults.

No rendering fields (skybox, ambient_light, camera) are accepted here.

environment only controls physics simulation — not visual output.

Section 4 — behaviors
Required. Non-empty array.
Declares every behavior script available in this execution. Entities
reference behaviors by ID. The runtime executes the named script with
the given params.

"behaviors": [
  {
    "id":     "patrol_waypoints",
    "script": "patrol",
    "params": {
      "waypoints": [
        [25.10, 0.0, 55.20],
        [25.30, 0.0, 55.40],
        [25.50, 0.0, 55.10],
        [25.10, 0.0, 55.20]
      ],
      "speed":     2.0,
      "threshold": 0.5
    }
  },
  {
    "id":     "hold_position",
    "script": "anchor",
    "params": {}
  },
  {
    "id":     "move_to_port",
    "script": "move_to",
    "params": {
      "target":    [25.00, 0.0, 55.00],
      "speed":     3.0,
      "threshold": 1.0
    }
  },
  {
    "id":     "flee_threat",
    "script": "flee",
    "params": {
      "threat": [25.30, 0.0, 55.35],
      "speed":  4.0
    }
  }
]



Field	Required	Type	Description
id	Yes	string	Unique behavior identifier within this contract. Referenced by entity.behaviors[].
script	Yes	string	One of the supported runtime scripts: patrol, idle, move_to, flee, anchor, track
params	Yes	object	Parameters for the script. Shape depends on script. See script reference below.
Supported scripts and their params:

Script	Required params	Optional params	Description
patrol	waypoints (number[3][])	speed, threshold	Move through waypoints in order, loop
idle	—	—	Stay in place, velocity zeroed
move_to	target (number[3])	speed, threshold	Move toward target position
flee	threat (number[3])	speed	Move directly away from threat position
anchor	—	—	Lock in place, state set to stopped
track	target_id (string)	speed	Face and follow another entity by ID
Rules:

behavior.id must be unique within the contract.

behavior.script must be one of the six supported scripts.

Any entity that references a behavior ID not declared here will fail validation.

Section 5 — transitions
Optional.
Declares rules that drive state evolution during execution. Each
transition is a data declaration — trigger, condition, action. The
runtime evaluates these each tick. No transition logic lives in code.

"transitions": [
  {
    "id":      "flag_on_zone_entry",
    "trigger": "on_zone_enter",
    "condition": {
      "field":  "state",
      "op":     "eq",
      "value":  "active"
    },
    "action": {
      "type":   "flag_entity",
      "params": {
        "reason": "entered_restricted_zone"
      }
    },
    "enabled": true
  },
  {
    "id":      "stop_after_tick_20",
    "trigger": "on_tick",
    "condition": {
      "field":  "tick",
      "op":     "gte",
      "value":  20
    },
    "action": {
      "type":   "set_state",
      "params": {
        "state": "stopped"
      }
    },
    "enabled": true
  },
  {
    "id":      "emit_collision_alert",
    "trigger": "on_collision",
    "condition": {
      "field":  "state",
      "op":     "eq",
      "value":  "active"
    },
    "action": {
      "type":   "emit_event",
      "params": {
        "event_type": "collision_alert",
        "data":       { "severity": "high" }
      }
    },
    "enabled": true
  }
]



Field	Required	Type	Description
id	Yes	string	Unique rule identifier within this contract.
trigger	Yes	string	When to evaluate: on_tick, on_collision, on_zone_enter, on_zone_exit, on_state_change
condition.field	Yes	string	Entity field or "tick" to evaluate. Dot notation supported e.g. meta.patrol_index
condition.op	Yes	string	Comparison operator: eq, neq, gt, lt, gte, lte, in, not_in
condition.value	Yes	any	Value to compare against.
condition.target	No	string	Scope this condition to a specific entity_id. If omitted, evaluates against all entities.
action.type	Yes	string	One of: set_state, emit_event, flag_entity, block_entity, log
action.params	No	object	Parameters for the action.
enabled	No	boolean	Defaults to true. Set false to temporarily disable a rule.
Supported action types:

Action	params	Effect
set_state	state (string)	Changes entity.state to the given value
emit_event	event_type, data	Appends an event to the event log
flag_entity	reason	Marks entity as flagged in state_summary
block_entity	reason	Sets entity.state to stopped, marks as blocked
log	message	Appends a log entry to the event log
Rules:

transitions[] is optional. If omitted, no rules fire during execution.

Rules fire in declaration order. All matching rules fire per tick.

Rules are data — no code is executed. The runtime is the interpreter.

Section 6 — consequences
Optional.
Declares consequence rules that map simulation events to output actions.
Evaluated after each tick by the consequence engine. All consequence
logic comes from this section — not from a static rules file.

"consequences": [
  {
    "rule_id":     "zone_entry_alert",
    "on":          "zone_enter",
    "if": {
      "entities":       ["vessel_alpha"],
      "context_checks": {
        "zone_id": "restricted_zone_north"
      }
    },
    "then": [
      {
        "action":   "emit_alert",
        "priority": "high",
        "payload": {
          "alert_type": "zone_violation",
          "message":    "Vessel entered restricted zone"
        }
      }
    ],
    "description": "Alert when vessel_alpha enters the northern restricted zone"
  },
  {
    "rule_id": "collision_consequence",
    "on":      "collision",
    "if": {
      "context_checks": {
        "distance": { "operator": "lte", "value": 2.0 }
      }
    },
    "then": [
      {
        "action":   "emit_alert",
        "priority": "critical",
        "payload": {
          "alert_type": "proximity_critical",
          "message":    "Entities at collision distance"
        }
      },
      {
        "action":   "log_event",
        "priority": "medium",
        "payload": {
          "message": "Collision detected between entities"
        }
      }
    ],
    "description": "Critical alert on close collision"
  },
  {
    "rule_id": "mission_complete",
    "on":      "state_change",
    "if": {
      "context_checks": {
        "new_state": "stopped"
      },
      "state_checks": {
        "all_entities_stopped": true
      }
    },
    "then": [
      {
        "action":   "emit_event",
        "priority": "high",
        "payload": {
          "event_type": "mission_complete",
          "message":    "All entities have reached terminal state"
        }
      }
    ],
    "description": "Emit mission complete when all entities stop"
  }
]



Field	Required	Type	Description
rule_id	Yes	string	Unique consequence rule identifier.
on	Yes	string	Event type that triggers evaluation: zone_enter, collision, state_change, tick, entity_spawned
if.entities	No	string[]	Scope rule to specific entity IDs. If omitted, applies to all entities.
if.context_checks	No	object	Key-value checks against event context data. Supports operator objects.
if.state_checks	No	object	Key-value checks against current simulation state.
then	Yes	array	Ordered list of actions to execute when condition matches.
then[].action	Yes	string	Action name. Open string — emit_alert, log_event, emit_event, escalate, record
then[].priority	No	string	critical, high, medium, low. Affects execution order.
then[].payload	No	object	Data passed to the action handler.
description	No	string	Human-readable description of what this rule does.
Rules:

consequences[] is optional. If omitted, no consequence evaluation occurs.

Rules are evaluated in declaration order.

context_checks support both direct value equality and operator objects: { "operator": "lte", "value": 2.0 } using operators: gte, lte, gt, lt, eq, neq

Section 7 — termination
Required.
Declares the conditions under which execution ends. The runtime
checks these after every tick. Execution stops when any condition
is satisfied or when max_ticks is reached.

"termination": {
  "max_ticks": 50,
  "conditions": [
    {
      "id":    "all_stopped",
      "type":  "all_entities_state",
      "value": "stopped"
    },
    {
      "id":    "any_flagged",
      "type":  "any_entity_flagged",
      "value": true
    },
    {
      "id":    "tick_limit",
      "type":  "tick_reached",
      "value": 50
    }
  ],
  "on_termination": "emit_event",
  "emit_payload": {
    "event_type": "execution_terminated",
    "reason":     "termination_condition_met"
  }
}


Field	Required	Type	Description
max_ticks	Yes	integer	Hard upper limit on ticks. Execution always stops here even if no condition is met. Range: 1–1000.
conditions	No	array	List of termination conditions evaluated after each tick.
conditions[].id	Yes	string	Unique identifier for this condition.
conditions[].type	Yes	string	See condition types table below.
conditions[].value	Yes	any	Value to match against.
on_termination	No	string	Action on termination: emit_event, log, none. Defaults to none.
emit_payload	No	object	Payload for the termination event if on_termination is emit_event.
Supported termination condition types:

type	value	Stops when
tick_reached	integer	Current tick >= value
all_entities_state	string	All entities have state == value
any_entity_state	string	At least one entity has state == value
all_entities_flagged	boolean	All entities are flagged
any_entity_flagged	boolean	At least one entity is flagged
event_count_reached	integer	Total events emitted >= value
entity_count_below	integer	Active entity count < value
Rules:

max_ticks is mandatory. It is the safety ceiling.

conditions[] is optional. If omitted, execution runs for exactly max_ticks.

Conditions are evaluated in declaration order. First match terminates.

Section 8 — telemetry
Optional.
Declares what telemetry the runtime should emit and at what frequency.
If omitted, default telemetry fires at every tick.

"telemetry": {
  "enabled":    true,
  "interval":   1,
  "emit_on": [
    "tick",
    "state_change",
    "collision",
    "zone_enter",
    "zone_exit",
    "flag",
    "termination"
  ],
  "include_entity_snapshots": true,
  "include_transition_log":   true,
  "include_event_log":        true,
  "tags": {
    "mission_type": "patrol",
    "operator":     "sector_7_command"
  }
}


Field	Required	Type	Default	Description
enabled	No	boolean	true	Master switch for telemetry emission.
interval	No	integer	1	Emit telemetry every N ticks. 1 = every tick.
emit_on	No	string[]	["tick"]	Event types that trigger a telemetry snapshot.
include_entity_snapshots	No	boolean	true	Include full entity state in each telemetry record.
include_transition_log	No	boolean	true	Include transition log in final artifact.
include_event_log	No	boolean	true	Include full event log in final artifact.
tags	No	object	{}	Arbitrary key-value metadata attached to all telemetry records.
Rules:

telemetry section controls what the runtime records and emits — not what it executes. Disabling telemetry does not change simulation output.

tags are passed through to artifacts unchanged.

Section 9 — governance
Required.
Carries governance metadata required for artifact lineage, trace
continuity, and replay reconstruction. The runtime attaches this to
every artifact it writes.

"governance": {
  "submitted_by":   "pipeline_node_01",
  "authority":      "BHIV",
  "decision":       "ALLOW",
  "risk_level":     "low",
  "mitra_trace_id": "mitra_trace_abc123",
  "decided_at":     1720000000000,
  "contract_hash":  "sha256:a1b2c3d4e5f6...",
  "lineage": {
    "parent_trace_id":  null,
    "origin":           "direct_submission",
    "pipeline_version": "8.0.0"
  }
}


Field	Required	Type	Description
submitted_by	Yes	string	Identifier of the system or node that submitted this contract.
authority	No	string	Governance authority that approved this execution. e.g. BHIV, TANTRA
decision	No	string	Governance decision: ALLOW, FLAG, BLOCK. Defaults to ALLOW.
risk_level	No	string	Risk classification: low, medium, high, critical
mitra_trace_id	No	string	Trace ID assigned by the Mitra governance node if applicable.
decided_at	No	integer	Unix ms timestamp when governance decision was made.
contract_hash	No	string	SHA-256 hash of the contract body for integrity verification.
lineage.parent_trace_id	No	string	trace_id of the parent execution if this is a child run. Null for root.
lineage.origin	No	string	How this contract arrived: direct_submission, pipeline, replay, api
lineage.pipeline_version	No	string	Version of the pipeline that produced this contract.
Rules:

submitted_by is mandatory. All other governance fields are optional.

decision defaults to ALLOW. A contract with decision BLOCK must not be executed — the runtime rejects it at validation.

contract_hash is computed by the submitter and verified by the runtime before execution begins.

Complete Contract Example — Maritime Patrol
This is a complete, valid contract for a 5-vessel maritime patrol
scenario. No code changes are required to execute this.

{
  "identity": {
    "trace_id":     "trace_maritime_patrol_001",
    "execution_id": "exec_1720000000000_patrol",
    "domain":       "maritime",
    "scenario":     "patrol_route",
    "version":      "1.0.0",
    "created_at":   1720000000000
  },

  "entities": [
    {
      "id": "vessel_alpha", "type": "vessel",
      "position": [25.10, 0.0, 55.20], "rotation": [0.0, 45.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["patrol_route_a"],
      "meta": { "callsign": "ALPHA-01", "speed_knots": 14 }
    },
    {
      "id": "vessel_bravo", "type": "vessel",
      "position": [25.30, 0.0, 55.40], "rotation": [0.0, 135.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["patrol_route_b"],
      "meta": { "callsign": "BRAVO-01", "speed_knots": 8 }
    },
    {
      "id": "vessel_charlie", "type": "vessel",
      "position": [25.50, 0.0, 55.10], "rotation": [0.0, 270.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["patrol_route_c"],
      "meta": { "callsign": "CHARLIE-01", "speed_knots": 5 }
    },
    {
      "id": "vessel_delta", "type": "vessel",
      "position": [25.20, 0.0, 55.50], "rotation": [0.0, 0.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["hold_position"],
      "meta": { "callsign": "DELTA-01", "speed_knots": 0, "anchored": true }
    },
    {
      "id": "vessel_echo", "type": "vessel",
      "position": [25.40, 0.0, 55.30], "rotation": [0.0, 315.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["patrol_route_e"],
      "meta": { "callsign": "ECHO-01", "speed_knots": 11 }
    },
    {
      "id": "zone_restricted", "type": "zone",
      "position": [25.30, 0.0, 55.35], "rotation": [0.0, 0.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": [],
      "meta": { "radius": 15.0, "label": "Restricted Zone North" }
    }
  ],

  "environment": {
    "gravity":          [0.0, 0.0, 0.0],
    "friction":         0.1,
    "bounce":           0.0,
    "air_resistance":   0.05,
    "collision_radius": 2.0
  },

  "behaviors": [
    {
      "id": "patrol_route_a", "script": "patrol",
      "params": {
        "waypoints": [[25.10,0,55.20],[25.30,0,55.40],[25.10,0,55.20]],
        "speed": 2.0, "threshold": 0.5
      }
    },
    {
      "id": "patrol_route_b", "script": "patrol",
      "params": {
        "waypoints": [[25.30,0,55.40],[25.50,0,55.10],[25.30,0,55.40]],
        "speed": 1.5, "threshold": 0.5
      }
    },
    {
      "id": "patrol_route_c", "script": "patrol",
      "params": {
        "waypoints": [[25.50,0,55.10],[25.20,0,55.50],[25.50,0,55.10]],
        "speed": 1.0, "threshold": 0.5
      }
    },
    {
      "id": "hold_position", "script": "anchor",
      "params": {}
    },
    {
      "id": "patrol_route_e", "script": "patrol",
      "params": {
        "waypoints": [[25.40,0,55.30],[25.10,0,55.20],[25.40,0,55.30]],
        "speed": 1.8, "threshold": 0.5
      }
    }
  ],

  "transitions": [
    {
      "id": "flag_zone_entry",
      "trigger": "on_zone_enter",
      "condition": { "field": "state", "op": "eq", "value": "active" },
      "action": {
        "type": "flag_entity",
        "params": { "reason": "entered_restricted_zone" }
      },
      "enabled": true
    },
    {
      "id": "log_collision",
      "trigger": "on_collision",
      "condition": { "field": "state", "op": "eq", "value": "active" },
      "action": {
        "type": "emit_event",
        "params": { "event_type": "proximity_alert", "data": {} }
      },
      "enabled": true
    }
  ],

  "consequences": [
    {
      "rule_id": "zone_violation_alert",
      "on": "zone_enter",
      "if": { "context_checks": { "zone_id": "zone_restricted" } },
      "then": [
        {
          "action": "emit_alert", "priority": "high",
          "payload": { "alert_type": "zone_violation" }
        }
      ],
      "description": "Alert on any vessel entering the restricted zone"
    }
  ],

  "termination": {
    "max_ticks": 50,
    "conditions": [
      { "id": "tick_limit", "type": "tick_reached", "value": 50 }
    ],
    "on_termination": "emit_event",
    "emit_payload": { "event_type": "patrol_complete" }
  },

  "telemetry": {
    "enabled": true,
    "interval": 1,
    "emit_on": ["tick", "state_change", "zone_enter", "flag"],
    "include_entity_snapshots": true,
    "include_transition_log":   true,
    "include_event_log":        true,
    "tags": { "domain": "maritime", "scenario": "patrol_route" }
  },

  "governance": {
    "submitted_by": "pipeline_node_01",
    "authority":    "BHIV",
    "decision":     "ALLOW",
    "risk_level":   "low",
    "lineage": {
      "parent_trace_id":  null,
      "origin":           "direct_submission",
      "pipeline_version": "8.0.0"
    }
  }
}

# Complete Contract Example — Drone Swarm

A contract for 5 drones tracking a target. Identical runtime path — only the contract changes.

```json
{
  "identity": {
    "trace_id":     "trace_drone_swarm_001",
    "execution_id": "exec_1720000001000_swarm",
    "domain":       "drone",
    "scenario":     "swarm_track",
    "version":      "1.0.0",
    "created_at":   1720000001000
  },

  "entities": [
    {
      "id": "target_node", "type": "marker",
      "position": [50.0, 0.0, 50.0], "rotation": [0.0, 0.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["idle_hold"],
      "meta": { "label": "surveillance_target" }
    },
    {
      "id": "drone_01", "type": "drone",
      "position": [10.0, 5.0, 10.0], "rotation": [0.0, 0.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["track_target"],
      "meta": { "unit": "SWARM-01" }
    },
    {
      "id": "drone_02", "type": "drone",
      "position": [20.0, 5.0, 10.0], "rotation": [0.0, 0.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["track_target"],
      "meta": { "unit": "SWARM-02" }
    },
    {
      "id": "drone_03", "type": "drone",
      "position": [10.0, 5.0, 20.0], "rotation": [0.0, 0.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["track_target"],
      "meta": { "unit": "SWARM-03" }
    },
    {
      "id": "drone_04", "type": "drone",
      "position": [30.0, 5.0, 15.0], "rotation": [0.0, 0.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["track_target"],
      "meta": { "unit": "SWARM-04" }
    },
    {
      "id": "drone_05", "type": "drone",
      "position": [15.0, 5.0, 30.0], "rotation": [0.0, 0.0, 0.0],
      "velocity": [0.0, 0.0, 0.0], "state": "active",
      "behaviors": ["track_target"],
      "meta": { "unit": "SWARM-05" }
    }
  ],

  "environment": {
    "gravity":          [0.0, 0.0, 0.0],
    "friction":         0.0,
    "bounce":           0.0,
    "air_resistance":   0.02,
    "collision_radius": 1.5
  },

  "behaviors": [
    {
      "id": "idle_hold", "script": "idle",
      "params": {}
    },
    {
      "id": "track_target", "script": "track",
      "params": {
        "target_id": "target_node",
        "speed": 3.0
      }
    }
  ],

  "transitions": [
    {
      "id": "flag_on_collision",
      "trigger": "on_collision",
      "condition": { "field": "state", "op": "eq", "value": "active" },
      "action": {
        "type": "emit_event",
        "params": { "event_type": "swarm_collision", "data": { "severity": "medium" } }
      },
      "enabled": true
    }
  ],

  "consequences": [
    {
      "rule_id": "swarm_convergence_alert",
      "on": "collision",
      "if": {
        "context_checks": {
          "distance": { "operator": "lte", "value": 1.5 }
        }
      },
      "then": [
        {
          "action": "emit_alert", "priority": "medium",
          "payload": { "alert_type": "swarm_too_close", "message": "Drones within collision threshold" }
        }
      ],
      "description": "Alert when two drones come within collision distance"
    }
  ],

  "termination": {
    "max_ticks": 30,
    "conditions": [
      { "id": "tick_limit", "type": "tick_reached", "value": 30 }
    ],
    "on_termination": "emit_event",
    "emit_payload": { "event_type": "swarm_mission_complete" }
  },

  "telemetry": {
    "enabled": true,
    "interval": 1,
    "emit_on": ["tick", "collision", "state_change"],
    "include_entity_snapshots": true,
    "include_transition_log":   true,
    "include_event_log":        true,
    "tags": { "domain": "drone", "scenario": "swarm_track" }
  },

  "governance": {
    "submitted_by": "pipeline_node_01",
    "authority":    "BHIV",
    "decision":     "ALLOW",
    "risk_level":   "low",
    "lineage": {
      "parent_trace_id":  null,
      "origin":           "direct_submission",
      "pipeline_version": "8.0.0"
    }
  }
}



Validation Rules Summary
These rules are enforced by the runtime before execution begins. A contract that fails any P0 rule is rejected immediately.

Priority	Rule	Rejection message
P0	identity.trace_id is present and non-empty	trace_id is required
P0	identity.execution_id is present and non-empty	execution_id is required
P0	identity.domain is present and non-empty	domain is required
P0	identity.scenario is present and non-empty	scenario is required
P0	entities is a non-empty array	entities must be a non-empty array
P0	Every entity.id is unique within the contract	duplicate entity id: <id>
P0	Every entity.position is [x, y, z]	entity.<id>.position must be [x,y,z]
P0	behaviors is a non-empty array	behaviors must be a non-empty array
P0	Every behavior.id is unique within the contract	duplicate behavior id: <id>
P0	Every behavior.script is one of the 6 supported scripts	behavior.<id>.script is not supported
P0	Every entity.behaviors[] references a declared behavior id	entity.<id> references undeclared behavior: <bid>
P0	termination.max_ticks is present, integer, range 1–1000	termination.max_ticks is required (1–1000)
P0	governance.submitted_by is present and non-empty	governance.submitted_by is required
P0	governance.decision is not BLOCK	contract blocked by governance — execution refused
P1	Every transition.trigger is a valid trigger value	transition.<id>.trigger is not valid
P1	Every transition.condition.op is a valid operator	transition.<id>.condition.op is not valid
P1	Every transition.action.type is a valid action type	transition.<id>.action.type is not valid
P1	Every consequence.rule_id is unique	duplicate consequence rule_id: <id>
P2	Zone entities have meta.radius set	zone entity <id> missing meta.radius
P2	track behavior has target_id that references a declared entity	track behavior <id> references unknown entity: <eid>
Field Requirement Summary
Section	Required	Optional
identity	trace_id, execution_id, domain, scenario	version, created_at
entities	id, type, position	rotation, velocity, state, behaviors, meta
environment	— (entire section optional)	gravity, friction, bounce, air_resistance, tick_rate, collision_radius
behaviors	id, script, params	—
transitions	— (entire section optional)	id, trigger, condition, action, enabled
consequences	— (entire section optional)	rule_id, on, if, then, description
termination	max_ticks	conditions, on_termination, emit_payload
telemetry	— (entire section optional)	enabled, interval, emit_on, include_*, tags
governance	submitted_by	authority, decision, risk_level, mitra_trace_id, decided_at, contract_hash, lineage
How This Contract Maps to the Existing Runtime
No new runtime code is needed. The mapping is direct:

Contract section	Runtime component	File
identity	Passes through as trace_id + execution_id	contractAdapter.js
entities	Spawned via EntityRegistry.load()	EntityRegistry.js
environment	Sets physics context on SceneManager	SceneManager.js
behaviors	Executed by BehaviorExecutor.executeAll()	BehaviorExecutor.js
transitions	Evaluated by RuleEngine.evaluate() each tick	RuleEngine.js
consequences	Evaluated by consequenceCompiler.processEvent()	consequenceCompiler.js
termination	Checked by TickLoop after each tick	TickLoop.js
telemetry	Collected by SceneManager event log	SceneManager.js
governance	Attached to all artifacts by bucket writer	pipelineBucketWriter.js
What Changes in the Codebase to Accept This Contract
Only two changes are required. Everything else already works.

1. Widen entity type validation — SumScriptSchema.js

// BEFORE — closed enum
const ENTITY_TYPES = ['vessel', 'obstacle', 'zone', 'marker', 'agent'];

// AFTER — open string, minimum length 1
// Remove the ENTITY_TYPES enum check entirely.
// Replace with: if (!e.type || typeof e.type !== 'string') errors.push(...)


2. Widen entity state validation — SumScriptSchema.js

// BEFORE — closed enum
const ENTITY_STATES = ['active', 'idle', 'stopped', 'destroyed'];

// AFTER — open string
// Remove the ENTITY_STATES enum check entirely.
// Replace with: if (e.state !== undefined && typeof e.state !== 'string') errors.push(...)


3. Remove entity type enum from simulationContract.v1.json

// BEFORE
"type": { "enum": ["vessel", "obstacle", "zone", "marker", "agent"] }

// AFTER
"type": { "type": "string", "minLength": 1 }


These three changes unlock all 9 sections of this contract for arbitrary execution. No other runtime files require modification.