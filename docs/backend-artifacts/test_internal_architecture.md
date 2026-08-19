# Test Cases: Internal Architecture (Realignment)

## TC-ARCH-01: Engine Determinism
*   **Command**: `vibesec scan . --json >> out1.json` (repeated x2)
*   **Action**: Compare hashes of `out1.json` and `out2.json`.
*   **Expectation**: Zero difference. `findings` array order is identical.

## TC-ARCH-02: Discovery Engine Limits
*   **Command**: `vibesec scan .`
*   **Pre-Condition**: Create `node_modules/bad_file.js` (Syntax Error).
*   **Expectation**: Scanner ignores `node_modules` entirely (No parsing error logged).

## TC-ARCH-03: Crash Resilience
*   **Command**: `vibesec scan .`
*   **Pre-Condition**: Create `crash.js` (Stack Overflow code).
*   **Expectation**: Tool logs "Skipping file" but exits with code 0/1 (Not 4).
