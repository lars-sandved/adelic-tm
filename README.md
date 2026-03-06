# Adelic-TM: Turing Machines as Möbius Transformations

Encoding Turing machine computation as products of GL(2,ℤ) matrices acting on continued fractions — the **Möbius-Shear framework**.

Based on [Emmett Shear's "Möbius Transformations on the Adeles as Computational Steps"](docs/emmett-mobius-adele-2026-03-05.pdf).

## The Core Idea

A Turing machine tape is a pair of continued fractions (left, right stacks). Each computational step is a Möbius transformation — a 2×2 integer matrix acting on ℚ via `x ↦ (ax+b)/(cx+d)`.

| TM Operation | Matrix | Name |
|---|---|---|
| Push symbol k onto stack | `P_k = [[k,1],[1,0]]` | Push matrix |
| Pop symbol k from stack | `Q_k = [[0,1],[1,-k]]` | Pop matrix (P_k⁻¹) |
| Right move (read a, write w) | Q_a on R, P_w on L | Pop-right, push-left |
| Left move | Q_a on R, P_w on R, P_b on R, Q_b on L | Compound move |

A full computation of n steps becomes a **Shear expansion**: a single matrix product Φ = M₁ · M₂ · ... · Mₙ that encodes the entire computation.

## Structure

```
src/
├── spec.py          # Machine/input validation, JSON loading
├── mobius.py         # MobiusMatrix (GL(2,ℤ)) + ShearFactor
├── cf.py            # CFStack — exact continued fraction arithmetic
├── shear.py         # ShearExpansion — per-stack matrix products
├── selectors.py     # CRT packing, Lagrange interpolation, Mem diagnostics
├── divergence.py    # ℵ-condition divergence monitoring
├── lean_export.py   # Lean 4 proof generation
└── core.py          # MobiusComputer — unified runner

tests/
└── test_mobius_computer.py   # 32 tests across 9 phases

examples/
├── bb3_machine.json          # Busy Beaver 3-state champion
├── bb3_input.json
├── library_machines/         # Corpus from Emmett's MobiusMachine
└── library_inputs/
```

## Quick Start

```python
from src.spec import load_machine, load_input
from src.core import MobiusComputer

machine = load_machine("examples/bb3_machine.json")
inp = load_input("examples/bb3_input.json")
mc = MobiusComputer(machine, inp, mode="direct", verify=True)
result = mc.run()

print(f"Status: {result.status}")           # HALT
print(f"Steps: {result.steps}")             # 13
print(f"Emet: {result.emet.is_emet}")       # False (Mem fails for BB3)
print(f"Φ_R = {mc.shear_expansion.phi_R}")  # [(-1,4),(0,1)]
print(f"Φ_L = {mc.shear_expansion.phi_L}")  # [(-5,22),(-2,9)]
```

## The Emet Conditions

A machine run satisfies **Emet** (אמת — "truth") when three conditions hold:

- **ℵ (Aleph)**: No crash or divergence — all partial quotients stay bounded
- **Mem (מ)**: The CRT selector is total — transition residues are distinct mod N
- **Tav (ת)**: The computation halts

BB(3) satisfies ℵ and Tav but fails Mem (gcd(d,q) = gcd(2,4) = 2).

## Running Tests

```bash
python3 -m pytest tests/ -v
```

## Lean 4 Export

```python
lean_code = mc.export_lean("BB3")
print(lean_code)  # Lean 4 proof that Φ = M₁ · M₂ · ... · M₁₃
```

## History

This repo evolved through several experimental phases:
1. **CF-architecture** — tape as continued fractions, state in p-adics
2. **Genuine adelic** — parity checker using 2-adic valuations
3. **Rational dynamics** — Collatz-style maps for TM steps
4. **Shape/magnitude transducer** — finite-state CF decomposition
5. **Möbius-Shear** → current framework (Emmett's formulation)

Earlier experiments are preserved in git history. The `archive/` directory contains the original monolithic implementation.
