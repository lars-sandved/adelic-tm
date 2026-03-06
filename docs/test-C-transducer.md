# Test C: The Transducer Proof of Principle

**Date:** 2026-03-04
**Context:** Testing whether shape determines a genuine finite-state machine (strong claim), not just a parametric family of Euclidean algorithms (weak claim).

## Key Insight: The Remainder Bound

For shape S = p/q (with numerator p, denominator q) and INTEGER magnitude M:
- Euclidean algorithm runs on (pM, q)
- Step 1: q₁ = ⌊pM/q⌋, r₁ = pM mod q
- Crucially: **r₁ < q always**, regardless of M
- Steps 2+ operate on numbers ALL less than q
- Therefore: steps 2+ are a FIXED finite computation (lookup table with q entries)

## The Lookup Table for Shape 36/25

After step 1, r₁ ∈ {0, 1, ..., 24}. The remaining CF is CF(25/r₁):

```
r₁ = 0:  halt
r₁ = 1:  [25]
r₁ = 2:  [12; 2]
r₁ = 3:  [8; 3]
r₁ = 4:  [6; 4]
r₁ = 5:  [5]
r₁ = 6:  [4; 6]
r₁ = 7:  [3; 1, 1, 3]
r₁ = 8:  [3; 8]
r₁ = 9:  [2; 1, 3, 2]
r₁ = 10: [2; 2]
r₁ = 11: [2; 3, 1, 2]    ← M=1 lands here (36 mod 25 = 11)
r₁ = 12: [2; 12]
r₁ = 13: [1; 1, 12]
r₁ = 14: [1; 1, 3, 1, 2]
r₁ = 15: [1; 1, 2]
r₁ = 16: [1; 1, 1, 3]
r₁ = 17: [1; 2, 8]
r₁ = 18: [1; 2, 1, 2]
r₁ = 19: [1; 3, 6]
r₁ = 20: [1; 4]
r₁ = 21: [1; 5, 4]
r₁ = 22: [1; 7, 3]        ← M=2 lands here (72 mod 25 = 22)
r₁ = 23: [1; 11, 2]
r₁ = 24: [1; 24]
```

This table is ENTIRELY determined by the shape's denominator (25).

## Verification

M = 1: 36·1 mod 25 = 11 → table[11] = [2; 3, 1, 2] → full CF: [1; 2, 3, 1, 2] ✓
M = 2: 36·2 mod 25 = 22 → table[22] = [1; 7, 3] → full CF: [2; 1, 7, 3] ✓
M = 3: 36·3 mod 25 = 8  → table[8]  = [3; 8] → full CF: [4; 3, 8] ✓

## The Full Machine Architecture

```
INPUT:  M's digit stream (magnitude)
                │
                ▼
┌──────────────────┐
│ MULTIPLY BY 36   │  (transducer, ≤36 states for carry)
│ M → 36M          │
└────────┬─────────┘
         │  36M digit stream
         ▼
┌──────────────────┐
│ LONG DIVISION     │  (transducer, 25 states for remainder)
│ BY 25             │──────▶ emit q₁ digits (first CF coefficient)
│                   │
│ accumulate r₁     │
└────────┬─────────┘
         │  r₁ ∈ {0,...,24}
         ▼
┌──────────────────┐
│ LOOKUP TABLE      │  (25 entries, fixed by shape)
│ r₁ → [q₂;q₃;...]│──────▶ emit remaining CF coefficients
└──────────────────┘

OUTPUT: CF = [q₁; q₂, q₃, ...]
```

Machine size: ≤ 36 × 25 = 900 states + 25-entry lookup. ALL determined by shape.

## What This Proves

1. The shape determines a FIXED finite-state machine.
2. The magnitude is the input tape (digit stream fed into the machine).
3. The CF is the output tape.
4. Different magnitudes through the same machine → different outputs.
5. Machine size = O(numerator × denominator) of the shape.

## Limitation: Rational Magnitudes

For rational M = a/b, Euclidean runs on (36a, 25b). After step 1:
- r₁ < 25b (depends on b, part of magnitude, not just shape)
- Lookup table would need 25b entries

So the clean decomposition works for INTEGER magnitudes. For rational M, the machine size depends on the input's denominator.

Possible resolution: magnitude naturally lives in ℤ (or ℤ_p), not ℚ, with rational structure captured by the shape.

## Open Question for Emmett

For rational magnitudes, is there a formulation where machine size depends ONLY on shape? Or does magnitude naturally live in ℤ/ℤ_p?
