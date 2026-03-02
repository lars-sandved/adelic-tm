# Adelic-TM: Turing Machines via Adelic Number Theory

Proof of principle: encoding Turing machine computation in the adele ring, where the **tape lives at the real place** and the **state machine lives at the p-adic places**.

## The Core Idea

A Turing machine has two parts: **data** (tape) and **control** (state machine).
An adele has two parts: the **real place** (∞) and the **p-adic places** (2, 3, 5, ...).

These match up:

| TM Component | Adelic Component | Operation |
|---|---|---|
| **Tape** | α_∞ ∈ ℝ (continued fraction) | Gauss map reads/advances |
| **State machine** | α_2 ∈ ℤ_2 (p-adic integer) | Multiplication updates state |
| **One computation step** | Coupled evolution of (α_∞, α_2) | Read from ℝ, write to ℤ_2 |

The adele α = (α_∞, α_2) evolves at each step:
1. **Read** from α_∞ via the Gauss map G(x) = 1/(x − ⌊x⌋)
2. **Transition** α_2 via p-adic arithmetic: α_2 → α_2 · 2^symbol
3. **State** = v_2(α_2) mod 2 — read directly from the 2-adic valuation

No separate state variable. The state IS the p-adic structure.

## Genuine Adelic Parity Checker

The flagship example: determine if a binary string has an even or odd number of 1s.

**Input** [1, 0, 1, 1] → CF digits [2, 1, 2, 2, 3] → α_∞ = 65/24

```
Start:  α = (65/24, 1)     v_2(1) = 0  → EVEN

Step 1: READ ⌊65/24⌋ = 2 → symbol 1
        α_∞: 65/24 → 24/17          (Gauss map)
        α_2:  1 × 2 = 2              (p-adic transition)
        v_2(2) = 1, mod 2 = 1       → ODD

Step 2: READ ⌊24/17⌋ = 1 → symbol 0
        α_∞: 24/17 → 17/7
        α_2:  2 × 1 = 2
        v_2(2) = 1, mod 2 = 1       → ODD

Step 3: READ ⌊17/7⌋ = 2 → symbol 1
        α_∞: 17/7 → 7/3
        α_2:  2 × 2 = 4
        v_2(4) = 2, mod 2 = 0       → EVEN

Step 4: READ ⌊7/3⌋ = 2 → symbol 1
        α_∞: 7/3 → 3
        α_2:  4 × 2 = 8
        v_2(8) = 3, mod 2 = 1       → ODD

Step 5: READ ⌊3⌋ = 3 → end marker
        v_2(8) = 3, mod 2 = 1       → ODD ✓  (three 1s)
```

The Gauss map unwinds the CF digit by digit at the real place. The 2-adic component accumulates parity via multiplication. The answer lives in v_2(α_2) mod 2.

## Why This Matters

The transition `α_2 → α_2 · 2^symbol` is **p-adic arithmetic**, not an arbitrary lookup table. The state lives in the algebraic structure of the number — specifically, in how many times 2 divides it.

This raises deep questions:
- Can every finite state machine be expressed as p-adic arithmetic? (Likely yes, via CRT)
- What conservation laws govern the coupled (α_∞, α_2) evolution?
- What does α^n mean — can exponentiation encode multi-step computation?

## Running

```bash
# Genuine adelic parity checker (the main result)
python3 genuine_adelic.py

# Also includes CF-based TM engine with more examples
python3 examples.py

# Unit tests
python3 -m unittest test_cf -v
```

## Files

```
genuine_adelic.py  — Genuine adelic parity checker (state via v_2)
cf_machine.py      — CF-based TM engine (Gauss map, encode/decode, AdelicTM class)
examples.py        — Parity checker and incrementer demos (cf_machine version)
test_cf.py         — Unit tests (26 tests, product formula verification)
docs/              — Theory writeup (adelic-tm-from-scratch.md)
```

### Legacy files (from initial p-adic-tape approach, kept for reference)
```
adelic.py, padic.py, turing.py, correspondence.py, universal.py
```

## Symbol Encoding

CF digits must be ≥ 1:
- Symbol 0 → CF digit 1
- Symbol 1 → CF digit 2
- End marker → CF digit 3

## Requirements

- Python 3.10+
- No external dependencies (pure standard library, `fractions.Fraction` for exact arithmetic)

## Architecture History

1. **v1** (initial): Tape in p-adics, state in reals. Worked but adelic structure was decorative — branching logic lived in Python, not number theory.

2. **v2** (CF architecture): Tape at real place as CF, state tracked separately. Gauss map does genuine computational work. But state was still a "Python variable."

3. **v3** (genuine adelic): Adele α = (α_∞, α_2) with independent components. State IS the 2-adic valuation. Transition IS p-adic multiplication. No separate state variable.

## License

MIT
