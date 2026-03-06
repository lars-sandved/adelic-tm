# Test A: Shape Invariance Under Magnitude Variation

**Date:** 2026-03-04
**Context:** Verifying Emmett's shape/magnitude/CF decomposition from "Continued Fractions from Magnitude and Shape"

## Framework

Any idele x decomposes into:
- **Shape**: {v_p(x)} — prime exponent pattern at finite places
- **Magnitude**: M = ||x|| = ∏_v |x_v|_v (idele norm)
- **Relationship**: |x|_∞ = M / ∏_p |x_p|_p

For principal ideles (diagonal embedding of q ∈ ℚ×), M = 1 by the product formula.

## Shape 1: 36/25 = 2² · 3² · 5⁻²

∏_p |q|_p = (1/4)(1/9)(25) = 25/36. So |x|_∞ = 36M/25.

| M | |x|_∞ | Euclidean on | CF | Length |
|---|-------|-------------|-----|--------|
| 1 | 36/25 | (36, 25) | [1; 2, 3, 1, 2] | 5 |
| 2 | 72/25 | (72, 25) | [2; 1, 7, 3] | 4 |
| 3 | 108/25 | (108, 25) | [4; 3, 8] | 3 |
| 1/2 | 18/25 | (18, 25) | [0; 1, 2, 1, 1, 3] | 6 |
| 1/3 | 12/25 | (12, 25) | [0; 2, 12] | 3 |
| 5/2 | 18/5 | (18, 5) | [3; 1, 1, 2] | 4 |
| **25/36** | **1** | **(1, 1)** | **[1]** | **idle** |

All verified by hand.

## Shape 2: 8/3 = 2³ · 3⁻¹

∏_p |q|_p = 2⁻³ · 3¹ = 3/8. So |x|_∞ = 8M/3.

| M | |x|_∞ | CF | Length |
|---|-------|----|--------|
| 1 | 8/3 | [2; 1, 2] | 3 |
| 2 | 16/3 | [5; 3] | 2 |
| 3 | 8 | [8] | 1 |
| 1/2 | 4/3 | [1; 3] | 2 |
| 1/4 | 2/3 | [0; 1, 2] | 3 |
| **3/8** | **1** | **[1]** | **idle** |

## Shape 3: 1/1 (trivial shape)

∏_p |q|_p = 1. So |x|_∞ = M.

CF(M) = CF(M). The trivial shape is the **identity machine**: output = input.

## Shape 4: 7 = 7¹ (single prime)

∏_p |q|_p = 1/7. So |x|_∞ = 7M.

Integer M → single-digit CF [7M]. The machine just multiplies by 7.

## Observations

1. **Idle point always works:** M* = 1/S gives CF = [1] for every shape. ✓
2. **CF length varies unpredictably with M** — no monotone relationship.
3. **Different shapes, same M → different CFs.** Shape genuinely determines different machines. ✓
4. **Trivial shape = identity machine.** ✓
5. **Shape complexity correlates with CF length:** More prime factors → longer CFs for same M.
6. **Invertibility:** CF + shape → unique M. The computation is reversible.
7. **Shape is not consumed:** The function T_S(M) = CF(S·M) exists unchanged after evaluation. The prime exponent pattern is invariant.

## Conclusion

The decomposition works cleanly as algebra. All predicted properties hold. Shape is invariant, magnitude is consumed, idle point exists, rational M ↔ halting.
