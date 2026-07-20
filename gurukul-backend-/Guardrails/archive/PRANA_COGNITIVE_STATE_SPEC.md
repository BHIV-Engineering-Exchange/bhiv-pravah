# PRANA Cognitive State Specification

## Purpose

Complete enumeration of allowed cognitive states. States represent signal-level observations only. No intent, behavior, motivation, or productivity inference.

## State Definitions

### IDLE
**Signals:** Zero interaction signals in observation window  
**NOT:** User away, distracted, unproductive, or inactive

### ACTIVE
**Signals:** Keyboard, mouse, touch, or focus events present  
**NOT:** User productive, focused, making progress, or intentional

### READING
**Signals:** Scroll events without concurrent input events  
**NOT:** User comprehending, paying attention, learning, or engaged

### TYPING
**Signals:** Continuous keyboard events ≥ 500ms  
**NOT:** User writing meaningful content, productive, or composing

### NAVIGATING
**Signals:** Route change events detected  
**NOT:** User exploring, searching, lost, or intentional navigation

### SEARCHING
**Signals:** Search input focus + query submission  
**NOT:** User finding something, successful search, or intentional search

### VIEWING
**Signals:** Content display or media playback start events  
**NOT:** User watching, consuming, learning, or paying attention

## State Rules

- **Complete Set:** Seven states only. No additions without specification change.
- **Mutual Exclusivity:** Exactly one state per observation window.
- **Ephemeral:** States exist only for observation window duration.
- **Signal-Only:** States equal signal representations. No semantic meaning.

## Minimum Signal Thresholds

| State | Threshold |
|-------|-----------|
| IDLE | Zero signals for full window |
| ACTIVE | ≥1 interaction signal |
| READING | Scroll events, no input |
| TYPING | Keyboard events ≥500ms |
| NAVIGATING | Route change detected |
| SEARCHING | Search focus + submission |
| VIEWING | Content/media display |

**Ambiguity:** Insufficient signals → Emit IDLE

## Guarantees

- **Determinism:** Same signals → Same state
- **Observational:** Telemetry only, no behavior changes
- **Non-Invasive:** No performance or UX impact
- **Ephemeral:** No persistent state
- **Failure-Tolerant:** Fail-open silently
