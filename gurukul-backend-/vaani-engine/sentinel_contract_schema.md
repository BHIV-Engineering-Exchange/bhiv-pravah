# Vaani Sentinel Contract Schema

This document defines the strict input and output schemas for the Vaani Sentinel Narrative Divergence Detector. The system is designed to be deterministic and structural, ensuring reproducible results for governance and audit purposes.

## 1. Strict Input Schema

All inputs to the Sentinel clustering engine must follow this structure:

| Field | Type | Description |
| :--- | :--- | :--- |
| `signal_id` | String | Unique identifier for the signal. |
| `source_id` | String | Identifier for the source of the statement. |
| `topic_id` | String | Identifier used for deterministic grouping. |
| `statement` | String | The actual claim or content (trimmed). |
| `confidence_level` | Float | (Optional) Provided confidence score (0-1). |
| `registry_reference` | String | Reference to the upstream governance registry. |

## 2. Strict Output Schema

The engine outputs a list of clusters, each following this structure:

| Field | Type | Description |
| :--- | :--- | :--- |
| `cluster_id` | String | Prefixed ID (`cluster-{topic_id}`). |
| `topic_id` | String | The original topic ID grouping. |
| `signals` | List | The sorted list of input signals in that cluster. |
| `divergence_score` | Float | Structural score (0-1) based on claim variance. |
| `truth_level` | Int | Classification level (0-4) based on consensus/diversity. |
| `contradiction_map` | Object | Map of unique statements to their sources. |
| `registry_reference` | String | Link to the BHIV registry (`bhiv://registry/cluster/{id}`). |
| `deterministic_hash` | String | SHA-256 hash of the sorted cluster JSON. |

## 3. Determinism Guarantees

- **No ML**: Only rule-based logic is applied.
- **Sorted Keys**: JSON output uses lexicographical key sorting.
- **Signal Sorting**: Signals within a cluster are sorted by `signal_id` for stability.
- **No Floating Jitter**: Scores are rounded to 4 decimal places.
