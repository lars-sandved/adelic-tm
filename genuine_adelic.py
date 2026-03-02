"""
Genuine Adelic Parity Checker

The adele α = (α_∞, α_2) where:
  - α_∞ ∈ ℝ: the tape, encoded as a continued fraction
  - α_2 ∈ ℤ_2: the state, evolved via multiplication

Each step:
  1. READ from α_∞: extract CF digit via Gauss map
  2. WRITE to α_2: multiply by 2 if symbol=1, by 1 if symbol=0
  3. ADVANCE α_∞: apply Gauss map

State is NEVER tracked in a separate variable.
It is read from v_2(α_2) mod 2 whenever needed.

The transition function is p-adic arithmetic: α_2 → α_2 · 2^symbol
"""

from fractions import Fraction
from math import floor


def v_2(x):
    """2-adic valuation of an integer."""
    if x == 0:
        return float('inf')
    n = abs(x)
    v = 0
    while n % 2 == 0:
        n //= 2
        v += 1
    return v


def gauss_map(x):
    """Standard Gauss map G(x) = 1/(x - floor(x)). Returns (digit, remainder)."""
    a = floor(x)
    frac = x - a
    if frac == 0:
        return a, Fraction(0)
    return a, Fraction(1) / frac


def encode_tape(symbols):
    """Encode tape as CF. 0→1, 1→2, end→3."""
    sym_map = {0: 1, 1: 2}
    digits = [sym_map[s] for s in symbols] + [3]
    x = Fraction(digits[-1])
    for i in range(len(digits) - 2, -1, -1):
        x = Fraction(digits[i]) + Fraction(1) / x
    return x


def adelic_parity(tape, verbose=True):
    """Run parity checker as a genuine adelic computation.

    The adele α = (α_inf, α_2):
      α_inf: rational number encoding the tape (real place)
      α_2:   integer tracking state via 2-adic valuation

    No separate state variable. State = v_2(α_2) mod 2.
    """
    digit_to_symbol = {1: 0, 2: 1, 3: 'end'}

    # Initial adele
    alpha_inf = encode_tape(tape)
    alpha_2 = 1  # v_2(1) = 0, mod 2 = 0 → EVEN

    if verbose:
        print(f"\n{'='*60}")
        print(f"  ADELIC PARITY CHECKER")
        print(f"  α = (α_∞, α_2) — no separate state variable")
        print(f"{'='*60}")
        print(f"  Tape: {tape}")
        print(f"  α_∞ = {alpha_inf}  α_2 = {alpha_2}")
        print(f"  v_2(α_2) = {v_2(alpha_2)}, mod 2 = {v_2(alpha_2) % 2} → EVEN")
        print()

    step = 0
    while True:
        step += 1
        digit, remainder = gauss_map(alpha_inf)
        symbol = digit_to_symbol.get(digit, digit)

        if symbol == 'end':
            parity = v_2(alpha_2) % 2
            result = "ODD" if parity == 1 else "EVEN"
            if verbose:
                print(f"  Step {step}: READ ⌊{alpha_inf}⌋ = {digit} → end")
                print(f"  α_2 = {alpha_2}, v_2 = {v_2(alpha_2)}, mod 2 = {parity}")
                print(f"  RESULT: {result}")
            return result

        # The adelic transition: α_2 → α_2 · 2^symbol
        # This is p-adic arithmetic, not a Python state flip.
        multiplier = 2 ** symbol
        new_alpha_2 = alpha_2 * multiplier

        if verbose:
            v_before = v_2(alpha_2) % 2
            v_after = v_2(new_alpha_2) % 2
            before = "EVEN" if v_before == 0 else "ODD"
            after = "EVEN" if v_after == 0 else "ODD"
            print(f"  Step {step}: READ ⌊{alpha_inf}⌋ = {digit} → sym {symbol}")
            print(f"    α_∞: {alpha_inf} → {remainder}")
            print(f"    α_2: {alpha_2} × {multiplier} = {new_alpha_2}"
                  f"  [v_2: {v_2(alpha_2)}→{v_2(new_alpha_2)},"
                  f" {before}→{after}]")
            print()

        alpha_inf = remainder
        alpha_2 = new_alpha_2

        if step > 100:
            return "TIMEOUT"


def run_tests():
    print(f"\n{'='*60}")
    print(f"  TEST SUITE")
    print(f"{'='*60}\n")

    tests = [
        ([1, 0, 1, 1], "ODD"),
        ([1, 1], "EVEN"),
        ([0, 0, 0], "EVEN"),
        ([1], "ODD"),
        ([1, 0, 1, 0, 1], "ODD"),
        ([1, 1, 1, 1], "EVEN"),
        ([0], "EVEN"),
        ([1, 0], "ODD"),
        ([], "EVEN"),
    ]

    passed = 0
    for tape, expected in tests:
        result = adelic_parity(tape, verbose=False)
        ok = result == expected
        if ok:
            passed += 1
        print(f"  {'✓' if ok else '✗'} {str(tape):20s} → {result:4s} (expected {expected})")

    print(f"\n  {passed}/{len(tests)} passed")
    if passed == len(tests):
        print(f"\n  State tracked entirely via v_2(α_2) mod 2.")
        print(f"  Transition is p-adic arithmetic: α_2 → α_2 · 2^symbol")
    return passed == len(tests)


if __name__ == "__main__":
    adelic_parity([1, 0, 1, 1], verbose=True)
    print()
    run_tests()
