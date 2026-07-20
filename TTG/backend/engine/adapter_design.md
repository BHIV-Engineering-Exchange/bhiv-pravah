# Engine Adapter Design Specification

## 1. Purpose

The **Engine Adapter** defines the control-plane contract between the **Text-to-Game (TTG)** system and an external game engine runtime.

Its purpose is to ensure that engine-ready, deterministic world data can be consumed safely by the engine without embedding any engine logic, rendering logic, or simulation behavior in the control plane. The engine is treated as a **black-box runtime target**.

---

## 2. Scope of Responsibility

The Engine Adapter is the authoritative gatekeeper for data flowing into the engine. It is responsible for:

* **Contract Ownership:** Owning and freezing the `engine schema v1.0`.
* **Validation:** Accepting world data that strictly conforms to the schema.
* **Data Integrity:** Ensuring all data passed downstream is **explicit**, **deterministic**, and **engine-agnostic**.
* **Single Interface:** Acting as the sole bridge between AI/control-plane systems and the engine.
* **Job Preparation:** Preparing schema-validated data for conversion into engine jobs.

> **The Adapter Guarantee:** The engine never receives free-form, partial, or ambiguous input.

---

## 3. Non-Responsibilities

To maintain strict boundary isolation, the Engine Adapter explicitly **does not**:

* Perform rendering or visualization.
* Execute physics, AI, or gameplay logic.
* Contain OpenGL, Unreal, or engine-specific code.
* Resolve asset file paths.
* Infer defaults or repair invalid data.
* Control engine update loops.

---

## 4. Schema Overview

The adapter enforces a minimal **Entity Component System (ECS)** style schema consisting of the following sections:

### 4.1 `schema_version`

Defines the contract version for compatibility tracking and safe evolution.

### 4.2 `world`

Defines global identity and physics context:

* **id:** Unique world identifier.
* **name:** Human-readable label.
* **gravity:** Global gravity vector.

### 4.3 `scene`

Defines scene-level environmental configuration (e.g., `ambientLight`, `skybox`). This applies globally and contains no entity-specific logic.

### 4.4 `entities`

Defines all runtime entities using pure ECS principles. Each entity consists of:

* An **ID** and a **Semantic Type** (player, npc, object).
* A **Transform** and a **Material**.
* A set of **Components** (Data only, never behavior).

### 4.5 `transform`

Defines explicit spatial state: **Position, Rotation, and Scale**.

### 4.6 `material`

Defines engine-agnostic visual properties: **Shader ID, Texture ID, and Base Color**.

### 4.7 `components`

Defines additional intent metadata:

* **mesh:** Symbolic identifier (e.g., `cube`, `sphere`).
* **collider:** Collision intent (e.g., `box`, `sphere`, `none`).
* **script:** Optional future behavior hook.

### 4.8 `quests`

High-level quest metadata reserved for future AI-driven systems. Included now to preserve forward compatibility.

---

## 5. Core Principles & Rules

### ECS Alignment

* **Entities** are identifiers.
* **Components** contain data only.
* **Systems/Logic** live exclusively in the engine.
* No inheritance or behavior is encoded in the JSON.

### Asset Resolution Rule (Critical)

`components.mesh` is treated as a **symbolic identifier**, not a file path.

* *Example:* `"mesh": "cube"`
* The **Engine** is responsible for mapping "cube" to the concrete asset (e.g., `assets/cube.txt`).

### Determinism Guarantees

Determinism is enforced via:

1. Explicit values for all fields (no implicit defaults).
2. Stable entity ordering.
3. Prohibition of timestamps or unseeded randomness.
4. Strict schema validation.

---

## 6. Validation & Policy

### Validation Strategy

All incoming world data must validate against the schema before forwarding.

* **Invalid data** is rejected early and logged.
* **No Auto-correction:** The adapter does not attempt to "fix" data.

### Visualization Policy

Any Three.js or preview visualization is **non-authoritative**. It exists for inspection only; the schema and engine execution are the sole sources of truth.

### Freeze & Versioning Policy

* Schema version is **fixed at v1.0**.
* Breaking changes are forbidden after freeze.
* Evolution must be explicit and additive.

---

## 7. Design Goal Summary

The Engine Adapter ensures that engine execution is **isolated, trusted, and auditable**. Correctness and stability take priority over flexibility to ensure future AI agents can integrate without breaking the system.

---
