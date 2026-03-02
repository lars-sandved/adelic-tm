# Adelic-TM: Continued Fraction Architecture

**Proof of principle** implementing Turing machines using adelic number theory with the continued fraction (CF) approach.

## The Architecture

This implementation follows the correct architecture identified by Emmett Shear:

| TM Component | Adelic Component |
|--------------|------------------|
| **Tape** (data) | **Real place** α∞ encoded as continued fraction |
| **State machine** (control) | **p-adic places** α₂, α₃, ... (state as residue mod prime) |
| **One step of computation** | **Gauss map** G(x) = 1/(x - ⌊x⌋) |

The tape is a rational number whose continued fraction expansion encodes the sequence of symbols. Each application of the Gauss map reads one CF digit (= one tape symbol) and advances the head.

## The Gauss Map

The Gauss map peels off CF digits one at a time:

```
G(x) = 1/(x - ⌊x⌋)
```

For x = [a₀; a₁, a₂, ...]:
1. Read digit: a₀ = ⌊x⌋
2. Advance: G(x) = [a₁; a₂, ...]

The inverse Gauss map pushes a digit onto the front:
```
G⁻¹(a, x) = a + 1/x = [a; a₁, a₂, ...]
```

## Parity Checker Example

Input [1, 0, 1, 1] encoded as CF [2; 1, 2, 2, 3] = 65/24:

```
Step 1: α∞ = 65/24
  READ: ⌊65/24⌋ = 2 → symbol 1
  STATE: EVEN + 1 → ODD
  GAUSS: G(65/24) = 24/17

Step 2: α∞ = 24/17
  READ: ⌊24/17⌋ = 1 → symbol 0
  STATE: ODD + 0 → ODD
  GAUSS: G(24/17) = 17/7

Step 3: α∞ = 17/7
  READ: ⌊17/7⌋ = 2 → symbol 1
  STATE: ODD + 1 → EVEN
  GAUSS: G(17/7) = 7/3

Step 4: α∞ = 7/3
  READ: ⌊7/3⌋ = 2 → symbol 1
  STATE: EVEN + 1 → ODD
  GAUSS: G(7/3) = 3

Step 5: α∞ = 3
  READ: 3 → end marker
  RESULT: ODD (three 1s) ✓
```

The Gauss map naturally unwinds the CF, and the state (tracked mod 2) gives the parity.

## The Product Formula

For any rational x ≠ 0:
```
|x|∞ × |x|₂ × |x|₃ × |x|₅ × ... = 1
```

At each step, this conservation law holds. When the Gauss map changes α∞, the p-adic norms adjust automatically.

## Running

```bash
# Run examples (parity checker + incrementer)
python examples.py

# Run unit tests
python test_cf.py

# Or with unittest
python -m unittest test_cf -v
```

## Files

```
cf_machine.py   — Core CF-based TM engine
  encode_tape()     Encode symbol list as CF (rational)
  gauss_map()       Apply G(x), return (digit, remainder)
  decode_tape()     Extract all CF digits
  AdelicTM class    Full TM implementation

examples.py     — Parity checker and incrementer demos
test_cf.py      — Unit tests with product formula verification
```

## Symbol Encoding

CF digits must be ≥ 1, so symbols are mapped:
- 0 → CF digit 1
- 1 → CF digit 2
- end marker → CF digit 3

Custom mappings can be provided.

## Key Features

- **Exact arithmetic**: Uses `fractions.Fraction` throughout (no floating point)
- **No external dependencies**: Pure Python standard library
- **Dual-tape model**: Supports read-write machines with left/right movement
- **Product formula verification**: Each step verifies ∏|x|ᵥ = 1

## Mathematical Context

This demonstrates that:

1. The Gauss map provides a natural "read head" operation
2. CF expansion is reversible (inverse Gauss = write)
3. Rational arithmetic encodes TM computation exactly
4. The product formula acts as a conservation law

The p-adic components track discrete state while the real component holds the (infinite) tape data. The adelic structure couples them through the product formula.

## Requirements

- Python 3.10+
- No external dependencies

## License

MIT
