# Divergence Formula Document

This document specifies the structural formula used by Vaani Sentinel to compute the Narrative Divergence Score.

## 1. Concept

Divergence measures how much the claims within a single topic vary structurally. It does not assess the "truth" of the content, only the diversity of the statements provided by different sources.

## 2. The Formula

The Divergence Score ($D$) is calculated as follows:

$$D = \frac{U - 1}{N - 1}$$

Where:
- $U$ = Number of **unique statements** (trimmed and case-sensitive).
- $N$ = Total number of **signals** in the cluster.

### Constraints:
- If $N \le 1$, $D = 0$.
- Range: $0$ to $1$.
- $D = 0$: Perfect alignment (all sources say exactly the same thing).
- $D = 1$: Maximum divergence (every signal provides a unique statement).

## 3. Implementation Logic

1.  **Normalization**: Trim whitespace from the `statement` field.
2.  **Uniqueness**: Convert the list of statements to a set to count unique occurrences.
3.  **Calculation**: Apply the formula and round to 4 decimal places to prevent floating-point variance during replay.

## 4. Contradiction Mapping

In addition to the score, a `contradiction_map` is generated to trace which `source_id` supports which `statement`. This preserves the original structure without collapsing disagreement into a mean or probabilistic average.
