## EMS Signal Specification (PRANA-E)

Source: `ems_signals.js`  
API: `window.EMSSignals.getState()`

All signals are **per-browser-tab**, reset/updated on a ~1s cadence, and contain **no text content** (counts and flags only).

### Core fields

- **timestamp** (`string`, ISO)
  - Wall-clock time when the snapshot was computed.

- **window_focus** (`boolean`)
  - `true` if the EMS window has OS focus (`window.onfocus`), else `false`.

- **browser_visibility** (`"visible" | "hidden" | string`)
  - Page visibility from `document.visibilityState`.

- **browser_hidden** (`boolean`)
  - `true` when `browser_visibility === "hidden"`.

- **task_tab_active** (`boolean`)
  - `true` only when `window_focus === true` **and** `browser_visibility === "visible"`.
  - Represents “real EMS task in the foreground”.

- **idle_seconds** (`number`)
  - Whole seconds since last human activity (key, mouse, scroll, or content click).

- **keystroke_count** (`number`)
  - Count of `keydown` events in the current 1s window (no key names or text captured).

- **mouse_events** (`number`)
  - Count of `mousemove` events in the current 1s window.

- **mouse_distance** (`number`)
  - Approximate pixel distance the mouse has moved in the current 1s window.

- **scroll_events** (`number`)
  - Count of `scroll` events in the current 1s window.

- **content_clicks** (`number`)
  - Count of clicks on EMS task-related elements:
  - Elements matching `[data-ems-task]`, `[data-ems-interaction]`, or `[data-task-id]`.

- **app_switches** (`number`)
  - Monotonic counter incremented on:
  - `window.blur` and whenever `browser_visibility` becomes `"hidden"`.


