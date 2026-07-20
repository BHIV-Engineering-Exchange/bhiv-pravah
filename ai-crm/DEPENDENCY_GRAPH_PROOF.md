# Dependency Graph Proof

## Blockage propagation proof
```json
{
  "input_blocked": "approve_order",
  "impacted": [
    { "id": "approve_order", "status": "blocked", "reason": "governance_hold" },
    { "id": "route_sarathi", "status": "blocked", "reason": "governance_hold" },
    { "id": "execution_participation", "status": "blocked", "reason": "governance_hold" },
    { "id": "telemetry_emit", "status": "blocked", "reason": "governance_hold" }
  ]
}
```

## Impact scoring examples
```json
{
  "total_score": 9,
  "node_scores": [
    { "id": "approve_order", "score": 6, "downstreamCount": 3 },
    { "id": "route_sarathi", "score": 3, "downstreamCount": 1 }
  ]
}
```

## Dependency analysis outputs
```json
{
  "node_id": "route_sarathi",
  "upstream": ["approve_order"],
  "downstream": ["execution_participation", "telemetry_emit"]
}
```

## Escalation recommendations
```json
[
  { "node_id": "approve_order", "score": 6, "recommendation": "escalate_within_window" },
  { "node_id": "route_sarathi", "score": 3, "recommendation": "monitor" }
]
```
