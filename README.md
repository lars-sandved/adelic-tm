# Adelic-TM: Turing Machines ↔ Adelic Arithmetic

**Proof of principle** demonstrating a concrete correspondence between Turing machine operations and arithmetic in the adele ring 𝔸_ℚ.

## The Core Idea

A **p-adic integer** in ℤ₂ is a formal sum b₀ + b₁·2 + b₂·4 + ... where each bᵢ ∈ {0,1}. This is *exactly* a one-sided infinite binary tape. The 2-adic integers **are** binary tapes.

An **adele** α = (α_∞, α₂, α₃, α₅, ...) packages a real number with p-adic numbers at every prime. We use this to encode a complete TM configuration:

| Component | Encodes | Why this prime? |
|-----------|---------|-----------------|
| α₂ ∈ ℤ₂ | Tape right of head | Binary tape cells = 2-adic digits |
| α₃ ∈ ℤ₃ | Tape left of head | Separate prime = independent component |
| α₅ ∈ ℤ₅ | Machine state | Third prime for third data channel |
| α_∞ ∈ ℝ | Step counter | Archimedean place tracks "time" |

## Key Result: Binary Increment = +1 in ℤ₂

The binary incrementer TM adds 1 to a binary number via carry propagation. For input 23 = 10111₂, it flips bits one at a time:

```
Step 0: 10111  (23)
Step 1: 10110  (carry...)
Step 2: 10100  (carry...)
Step 3: 10000  (carry...)
Step 4: 11000  (24, done!)
```

The TM needs 4 steps. In ℤ₂, this is a **single operation**: 23 + 1 = 24. The carry propagation that the TM performs step-by-step is exactly what happens in 2-adic addition — but the adelic view does it "all at once."

This is verified by the code: both the step-by-step adelic simulation and the direct +1 operation produce identical results.

## Running

```bash
# Binary incrementer (default: 23 → 24)
python main.py increment

# Custom starting number
python main.py increment --start 255

# 3-state busy beaver (6 ones in 14 steps)
python main.py beaver

# Generate HTML report
python main.py increment --html report.html
```

## Example Output

```
========================================================================
  Direct Correspondence: Binary Increment = +1 in Z_2
========================================================================

  Start value:  23  (0b10111)
  End value:    24  (0b11000)
  TM steps needed: 4 (carry propagation)

  2-adic before:  23
  2-adic after:   24
  Difference:     1  (should be 1)

  VERIFIED: The TM's 4-step carry propagation
  is exactly +1 in Z_2. Adelic arithmetic captures the
  full computation in a single operation.
```

## Architecture

```
turing.py         — TM simulator with execution tracing
padic.py          — p-adic integer arithmetic
adelic.py         — Adele ring elements + TM config encoding
correspondence.py — Parallel execution + verification
visualize.py      — Terminal + HTML visualization
main.py           — CLI entry point
SPEC.md           — Full mathematical specification
```

## Mathematical Context

This is a proof-of-principle for a larger research question: **can the adelic structure naturally encode universal computation?**

The weak claim (any TM can be encoded arithmetically) is trivial. The strong claim is that the adelic decomposition into primes corresponds to something meaningful about the computation — that different primes track different aspects of the computation independently, and the product formula (∏ᵥ |α|ᵥ = 1) acts as a conservation law.

The binary incrementer demonstrates the cleanest case: the computation lives entirely in the 2-adic component, and arithmetic **is** the computation. The busy beaver demonstrates the general encoding where multiple primes collaborate.

### Next Steps

1. **Universality test**: Encode the (15,2) Neary-Woods strongly universal machine
2. **Adelic gradient descent**: Formalize Emmett's "step in the Archimedean place, primes adjust via tree pruning"
3. **Product formula as conservation law**: Investigate what ∏|α|ᵥ = 1 means for computation
4. **ProtoNum connection**: Can the F₁ → adeles path (from HoTT proto-numbers) be made precise?

## Requirements

- Python 3.10+
- No external dependencies (pure standard library)

## License

MIT
