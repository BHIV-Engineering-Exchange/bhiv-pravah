# PRANA System Overview

## Purpose

High-level overview: what PRANA is, what PRANA is not, why PRANA is safe boring infrastructure.

## What PRANA Is

### Observational Telemetry System
- Observes user interaction signals
- Emits cognitive state telemetry
- Observational only (no interpretation, analysis, or decisions)

### Deterministic State Engine
- Converts signal patterns to cognitive states
- Same inputs → Same outputs
- No randomness, adaptation, or learning

### Non-Invasive Infrastructure
- No application code changes
- No user experience impact
- No performance degradation
- Invisible to users and applications

### Ephemeral Operation
- Discrete 2-second observation windows
- No persistent state between windows
- Each window operates independently

### Failure-Tolerant Design
- Fail-open safely
- Failures → Silent operation cessation
- No application impact

## What PRANA Is Not

- **Not a Control System:** No application behavior control
- **Not an Intelligence Engine:** No intent, behavior, or productivity inference
- **Not a UX Trigger:** No user experience changes or notifications
- **Not a Decision-Maker:** No decisions about system behavior
- **Not an Analyzer:** No behavior, intent, or productivity analysis

## Observability vs Control

### Observability
- Observe system behavior through telemetry
- Enable monitoring and analysis
- Do not affect system behavior

### Control
- Change system behavior based on observations
- Enforce policies or rules
- Modify user experience

**PRANA Boundary:** PRANA operates entirely in observability domain. Never crosses into control domain.

## Why PRANA Is Safe

- **Fail-Open:** All failures → Silent cessation, no application impact
- **Non-Invasive:** No application, UX, or performance impact
- **Deterministic:** Predictable, no unexpected behavior
- **Ephemeral:** No persistent impact

## Why PRANA Is Boring Infrastructure

- **Infrastructure:** Silent background operation, not a feature
- **Boring:** Predictable, reliable, uneventful
- **Maintenance-Free:** No maintenance, configuration, or monitoring
- **Simple:** Single focused purpose (emit telemetry)

## PRANA's Role

- **Telemetry Provider:** Emits cognitive state telemetry
- **Infrastructure Component:** Enables other systems silently
- **Observability Enabler:** Provides telemetry for monitoring and analysis

## Architecture Principles

- **Observational Only:** Observe signals, emit states, no interpretation
- **Deterministic:** Same inputs → Same outputs, no adaptation
- **Non-Invasive:** No application, UX, or performance impact
- **Ephemeral:** No persistent state
- **Failure-Tolerant:** Fail-open safely

## Contract Guarantees

- Observational guarantee
- Deterministic guarantee
- Non-invasive guarantee
- Ephemeral guarantee
- Failure-tolerant guarantee
