# PRANA-G Signal Specification

## Overview
This document defines the behavioral signals captured by the PRANA-G cognitive telemetry engine and their meanings.

## Signal Definitions

### 1. dwell_time_ms
- **Meaning**: Duration spent on current content/page
- **Unit**: Milliseconds
- **Range**: 0 to ∞
- **Interpretation**: 
  - Higher values → Sustained reading/focus
  - Lower values → Skimming/distraction

### 2. hover_loops
- **Meaning**: Number of circular mouse movements indicating indecision
- **Unit**: Count
- **Range**: 0 to ∞
- **Interpretation**:
  - Higher values → Indecision/uncertainty
  - Lower values → Clear focus/direction

### 3. rapid_click_count
- **Meaning**: Number of rapid successive clicks in short timeframe
- **Unit**: Count
- **Range**: 0 to ∞
- **Interpretation**:
  - Higher values → Anxiety/frustration
  - Lower values → Calm interaction

### 4. scroll_depth
- **Meaning**: Percentage of page scrolled through
- **Unit**: Percentage (0-100)
- **Range**: 0 to 100
- **Interpretation**:
  - Higher values → Deeper engagement
  - Lower values → Surface browsing

### 5. mouse_velocity
- **Meaning**: Speed of mouse movement across screen
- **Unit**: Pixels per second
- **Range**: 0 to ∞
- **Interpretation**:
  - Higher values → Agitation/restlessness
  - Lower values → Calm/focused movement

### 6. inactivity_ms
- **Meaning**: Duration since last user interaction
- **Unit**: Milliseconds
- **Range**: 0 to ∞
- **Interpretation**:
  - Higher values → Idle/potential distraction
  - Lower values → Active engagement

### 7. tab_visible
- **Meaning**: Whether the browser tab is currently visible
- **Unit**: Boolean (true/false)
- **Range**: true/false
- **Interpretation**:
  - true → User present at device
  - false → User away from device

### 8. panel_focused
- **Meaning**: Whether the learning panel is in focus
- **Unit**: Boolean (true/false)
- **Range**: true/false
- **Interpretation**:
  - true → Mental focus on task
  - false → Potential distraction

## Signal Capture Frequency
- All signals are captured in real-time as user interacts
- Aggregate snapshots taken every 5 seconds for packet generation
- Continuous monitoring for state engine calculations

## Signal Quality Assurance
- No fake or guessed data - all signals derived from actual user behavior
- Resilient to browser limitations and privacy restrictions
- Minimal performance impact on user experience