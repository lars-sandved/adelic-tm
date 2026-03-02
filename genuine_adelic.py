"""
Experiment: Can the state live IN the rational number's p-adic structure?

RESULT: Not with a single rational number and the Gauss map. Here's why:

APPROACH 1: Standard Gauss map, read state from v_2
  The standard CF uniquely determines the rational number.
  Tape [1,0,1,1] -> 65/24 -> Gauss orbit: 65/24, 24/17, 17/7, 7/3, 3
  Their v_2 values: -3, 3, 0, 0, 0
  v_2 mod 2:         1, 1, 0, 0, 0
  States needed:     0, 1, 1, 0, 1  (EVEN, ODD, ODD, EVEN, ODD)
  -> NO MATCH. The tape content fixes the factorization; no freedom for state.

APPROACH 2: Generalized Gauss map G_b(x) = b/(x-a), b encodes transition
  b=2 for symbol 1 (flip v_2), b=1 for symbol 0 (keep v_2).
  v_2 tracking works for one step! But b != 1 CORRUPTS the tape:
  G_2(65/24) = 48/17, floor(48/17) = 2 -> reads symbol 1
  But original tape[1] = 0 (should read symbol 0)
  The modified numerator changes ALL subsequent CF digits.

APPROACH 3: Encode b-values into initial number as generalized CF
  x = 2 + 2/(1 + 1/(2 + 2/(2 + 2/3))) = 52/15
  But floor(52/15) = 3, not 2. The b>1 makes the tail > 1,
  breaking the floor-based digit extraction.

FUNDAMENTAL TENSION: In a single rational number, the real structure
(CF digits = tape) and p-adic structure (valuations = state) are NOT
independent. The product formula COUPLES them: changing one changes the other.
This is precisely what makes adeles interesting, but it means you can't
separately encode tape and state in the same rational.

For genuinely adelic computation, we likely need:
  (a) Actual adeles (independent real + p-adic components), not just rationals
  (b) A non-diagonal embedding where real and p-adic parts have separate DoF
  (c) Something more subtle about how Emmett's architecture works

This is a KEY QUESTION for Emmett.
"""

from fractions import Fraction
from math import floor


def v_p(x, p):
    """p-adic valuation of rational x."""
    if x == 0:
        return float('inf')
    num, den = abs(x.numerator), abs(x.denominator)
    val = 0
    while num % p == 0: num //= p; val += 1
    while den % p == 0: den //= p; val -= 1
    return val


def demonstrate_the_problem():
    """Show concretely why state can't live in v_2 of a single rational."""
    
    print("="*70)
    print("  CAN THE STATE LIVE IN v_2(x) mod 2?")
    print("="*70)
    
    # Standard Gauss map trace
    print("\n--- Approach 1: Standard Gauss map, read v_2 ---\n")
    x = Fraction(65, 24)
    xs = [x]
    digits = []
    for _ in range(4):
        a = floor(x)
        digits.append(a)
        frac = x - a
        if frac == 0: break
        x = Fraction(1) / frac
        xs.append(x)
    
    states_needed = [0, 1, 1, 0, 1]
    state_names = {0: "EVEN", 1: "ODD"}
    
    print(f"  Tape: [1, 0, 1, 1]")
    print(f"  {'x':>12s}  {'v_2':>4s}  {'v2%2':>4s}  {'need':>4s}  {'match':>5s}")
    for i, xi in enumerate(xs):
        v2 = v_p(xi, 2)
        need = states_needed[i]
        got = v2 % 2
        match = "✓" if got == need else "✗"
        print(f"  {str(xi):>12s}  {v2:>4d}  {got:>4d}  {need:>4d}  {match:>5s}")
    
    print(f"\n  RESULT: v_2 mod 2 does NOT track parity state.")
    print(f"  The CF digits fix the rational, which fixes all valuations.")
    print(f"  Zero degrees of freedom for state encoding.\n")
    
    # Modified Gauss map
    print("--- Approach 2: Generalized Gauss map G_b(x) = b/(x-a) ---\n")
    
    x = Fraction(65, 24)
    tape = [1, 0, 1, 1]
    inv_map = {1: 0, 2: 1, 3: 'end'}
    
    print(f"  Step 1: x = {x}, v_2 = {v_p(x, 2)}")
    a = floor(x)
    symbol = inv_map[a]
    print(f"  Read digit {a} -> symbol {symbol} ✓ (correct)")
    
    b = 2  # flip for symbol 1
    new_x = Fraction(b) / (x - a)
    print(f"  G_2(x) = 2/({x}-{a}) = {new_x}")
    print(f"  v_2({new_x}) = {v_p(new_x, 2)}, mod 2 = {v_p(new_x, 2) % 2}")
    print(f"  v_2 flipped: {v_p(x,2)%2} -> {v_p(new_x,2)%2} ✓ (parity tracking works!)")
    print()
    
    a2 = floor(new_x)
    symbol2 = inv_map.get(a2, f"?({a2})")
    print(f"  Step 2: x = {new_x}, floor = {a2} -> symbol {symbol2}")
    print(f"  But tape[1] = {tape[1]} (symbol 0, should read digit 1)")
    print(f"  TAPE CORRUPTED: b=2 changed the CF structure ✗")
    print()
    
    # Fundamental tension
    print("--- The Fundamental Tension ---\n")
    print("  In a rational number, the CF (real structure) and the")
    print("  prime factorization (p-adic structure) are the SAME data")
    print("  viewed differently. You cannot change one independently.")
    print()
    print("  The product formula couples them: |x|_∞ × ∏|x|_p = 1")
    print("  This IS the computation — but it means tape ↔ state")
    print("  coupling is total, not partial.")
    print()
    print("  For Emmett's architecture to work, we likely need:")
    print("  (a) Genuine adeles with independent components, OR")
    print("  (b) The computation fundamentally WRITES the tape")
    print("      (modified CF = modified tape = the computation), OR")  
    print("  (c) A more subtle encoding we haven't seen yet")
    print()
    print("  This is the key question for Emmett: how does the state")
    print("  machine live in the p-adics INDEPENDENTLY of the tape?")


if __name__ == "__main__":
    demonstrate_the_problem()
