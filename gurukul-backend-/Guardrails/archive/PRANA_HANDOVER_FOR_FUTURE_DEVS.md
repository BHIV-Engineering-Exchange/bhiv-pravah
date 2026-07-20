# PRANA_HANDOVER_FOR_FUTURE_DEVS.md

## A. What PRANA Is (Plain Language)
PRANA is the system's "peripheral nervous system." It senses that a keyboard was pressed or a mouse was moved, and it translates those raw signals into basic cognitive states (like "Working" or "Browsing"). It does not know *what* you are typing or *where* you are clicking. It is a recording device for system-level context, designed to be as simple and reliable as a wall clock.

## B. What PRANA Is Not
- It is NOT an AI.
- It is NOT a user tracking tool.
- It is NOT a performance monitor.
- It is NOT a judge of your work.
- It is NOT a source of "insights."
- It is NOT a part of the product's feature set.

## C. How to Reason About PRANA Safely
1. **Think Constitution, Not Feature**: PRANA is a set of rules that must be followed. It is not an asset to be improved for "engagement."
2. **Think Boundary, Not Insight**: PRANA's value is in what it *refuses* to do. The boundaries are the most important part of the code.
3. **Think Invariant, Not Optimization**: Stability is the only metric that matters. If you make it "faster" but break the determinism, you have failed.

## D. Common Mistakes (Forbidden Actions)
1. **"Improving" the Output**: Do not add more specific states. "Reading" is enough; do not try to detect "Deep Reading vs. Skimming."
2. **Adding Helpful Logic**: Do not add logic that helps the user. PRANA is not a coach or a guide.
3. **Adding Analytics**: Do not call home with aggregated PRANA data.
4. **Coupling to Product Flow**: Do not make a button enable/disable based on a PRANA state.
5. **Optimizing Latency**: PRANA operates in 2-second windows. Trying to make it sub-millisecond is unnecessary and introduces jitter.
6. **"Just One Small Feature"**: Every feature added to PRANA is a hole poked in the boundary. Resistance is the primary duty of the maintainer.

## E. Why Optimization is Dangerous
In a boundary system, optimization often requires more data. More data increases the surface area for a privacy breach. Optimization also introduces complexity, making the system harder to audit. A simple, slow, but perfectly transparent system is better than a complex, fast, but opaque one.
