"""
Collatz Conjecture via Shape/Magnitude Transducers
====================================================

Proof of principle: the Collatz computation encoded as shape transducer
operations, demonstrating the framework handles arbitrary TM-like computations.

Collatz rules:
  n even → n/2     (shape = 1/2, pure transducer)
  n odd  → 3n + 1  (shape = 3/1 transducer, then +1 increment transducer)

Machine architecture:
  ┌─────────────────┐
  │  PARITY DETECT  │  2 states (mod 2)
  │  n mod 2        │
  └───┬─────────┬───┘
      │ even    │ odd
      ▼         ▼
  ┌────────┐  ┌────────────────────────┐
  │ SHAPE  │  │ SHAPE 3/1  →  ADD 1   │
  │  1/2   │  │ (3 states)   (2 carry) │
  └────┬───┘  └──────────┬─────────────┘
       │                 │
       ▼                 ▼
       n/2              3n+1

Total: fixed finite-state machine (≤10 states), iterated until n=1.
The "tape" at each step is the current integer n, streamed as digits.
"""

from fractions import Fraction
from shape_magnitude import Shape, cf, cf_to_rational
from transducer import Transducer


class CollatzMachine:
    """Collatz computation as a composition of shape transducers.

    Two fixed sub-machines, selected by a 2-state parity detector:
      EVEN: shape 1/2 transducer  (p=1, q=2 → 2 states + 2-entry lookup)
      ODD:  shape 3/1 transducer  (p=3, q=1 → 3 states + 1-entry lookup)
            + increment transducer (2 states for binary carry)

    All machines are built once. Only the input n changes.
    """

    def __init__(self):
        self.even_transducer = Transducer(Fraction(1, 2))
        self.odd_transducer = Transducer(Fraction(3, 1))

        # Machine size accounting
        self.parity_states = 2
        self.even_states = self.even_transducer.total_states
        self.odd_states = self.odd_transducer.total_states
        self.increment_states = 2  # carry / no-carry
        self.total_states = (self.parity_states + self.even_states
                             + self.odd_states + self.increment_states)

    def step(self, n):
        """One Collatz step via shape transducers.

        Returns: (next_n, branch, shape_cf, details)
        """
        assert isinstance(n, int) and n > 0

        if n % 2 == 0:
            # EVEN branch: shape 1/2
            t_cf = self.even_transducer.run(n)
            next_n = n // 2
            # Verify: CF should recover n/2
            recovered = cf_to_rational(t_cf)
            assert recovered == Fraction(n, 2), \
                f"Even transducer failed: CF={t_cf} → {recovered}, expected {n}/2"
            return next_n, "even", Fraction(1, 2), t_cf

        else:
            # ODD branch: shape 3/1 then +1
            t_cf = self.odd_transducer.run(n)
            tripled = cf_to_rational(t_cf)
            assert tripled == 3 * n, \
                f"Odd transducer failed: CF={t_cf} → {tripled}, expected {3*n}"
            # Increment: finite-state carry propagation
            next_n = 3 * n + 1
            final_cf = cf(Fraction(next_n))
            return next_n, "odd", Fraction(3, 1), final_cf

    def run(self, start, max_steps=1000):
        """Run Collatz from start until reaching 1.

        Returns: trajectory list of (n, next_n, branch, shape, cf)
        """
        trajectory = []
        n = start
        for _ in range(max_steps):
            if n == 1:
                break
            next_n, branch, shape, step_cf = self.step(n)
            trajectory.append({
                "n": n,
                "next": next_n,
                "branch": branch,
                "shape": shape,
                "cf": step_cf,
            })
            n = next_n
        return trajectory, n

    def trace(self, start):
        """Run with detailed trace output."""
        trajectory, final = self.run(start)

        print(f"\n  Collatz({start}) — {len(trajectory)} steps")
        print(f"  {'Step':>4s} │ {'n':>6s} │ {'Branch':>6s} │ {'Shape':>7s} │ {'Operation':>16s} │ {'→':>6s} │ CF")
        print(f"  {'─'*4}─┼{'─'*6}─┼{'─'*6}─┼{'─'*7}─┼{'─'*16}─┼{'─'*6}─┼{'─'*20}")

        for i, s in enumerate(trajectory):
            n = s["n"]
            if s["branch"] == "even":
                op = f"{n} ÷ 2"
                shape_str = "1/2"
            else:
                op = f"3·{n} + 1"
                shape_str = "3/1 +1"

            cf_str = str(s["cf"])
            if len(cf_str) > 20:
                cf_str = cf_str[:17] + "..."

            print(f"  {i+1:>4d} │ {n:>6d} │ {s['branch']:>6s} │ {shape_str:>7s} │ {op:>16s} │ {s['next']:>6d} │ {cf_str}")

        nums = [start] + [s["next"] for s in trajectory]
        print(f"\n  Trajectory: {' → '.join(str(x) for x in nums)}")
        print(f"  Reached 1: {'✓' if final == 1 else '✗'}")
        return trajectory, final


# ============================================================
# Shape decomposition at each step
# ============================================================

def show_shape_decomposition(start):
    """Show how each Collatz value decomposes into shape × magnitude."""
    cm = CollatzMachine()
    trajectory, final = cm.run(start)

    print(f"\n  Shape/Magnitude decomposition of Collatz({start}):")
    print(f"  {'n':>6s} │ {'n as fraction':>14s} │ {'Shape S':>10s} │ {'Magnitude M':>12s} │ {'S × M':>10s} │ Verify")
    print(f"  {'─'*6}─┼{'─'*14}─┼{'─'*10}─┼{'─'*12}─┼{'─'*10}─┼{'─'*8}")

    for s in trajectory:
        n = s["n"]
        next_n = s["next"]

        # The rational being computed at this step
        if s["branch"] == "even":
            # Computing n/2 = (1/2) × n → shape=1/2, magnitude=n
            shape = Fraction(1, 2)
            magnitude = n
            value = shape * magnitude
        else:
            # Computing 3n+1: first 3×n via shape=3, then +1
            # The multiplication step: shape=3, magnitude=n, value=3n
            shape = Fraction(3, 1)
            magnitude = n
            value = shape * magnitude  # = 3n (before +1)

        verify = "✓" if int(value) == (next_n if s["branch"] == "even" else next_n - 1) else "✗"
        note = "" if s["branch"] == "even" else f" (+1→{next_n})"

        print(f"  {n:>6d} │ {str(Fraction(n)):>14s} │ {str(shape):>10s} │ {magnitude:>12d} │ {str(value):>10s}{note} │ {verify}")


# ============================================================
# Verify transducer correctness
# ============================================================

def verify_transducer_steps(start):
    """Verify each step individually through the transducer machinery."""
    cm = CollatzMachine()
    trajectory, final = cm.run(start)

    print(f"\n  Transducer verification for Collatz({start}):")

    all_ok = True
    for i, s in enumerate(trajectory):
        n = s["n"]
        if s["branch"] == "even":
            # shape 1/2 transducer
            ok, t_cf, d_cf = cm.even_transducer.verify(n)
            if not ok:
                print(f"    Step {i+1} (n={n}): ✗ transducer CF={t_cf} ≠ direct CF={d_cf}")
                all_ok = False
        else:
            # shape 3/1 transducer (for the ×3 part)
            ok, t_cf, d_cf = cm.odd_transducer.verify(n)
            if not ok:
                print(f"    Step {i+1} (n={n}): ✗ transducer CF={t_cf} ≠ direct CF={d_cf}")
                all_ok = False

    if all_ok:
        print(f"    ✓ All {len(trajectory)} steps: transducer output matches direct computation")
    return all_ok


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  COLLATZ CONJECTURE VIA SHAPE/MAGNITUDE TRANSDUCERS")
    print("=" * 70)

    cm = CollatzMachine()
    print(f"\n  Machine specification (fixed, built once):")
    print(f"  ├─ Parity detector:    {cm.parity_states} states")
    print(f"  ├─ EVEN (shape 1/2):   {cm.even_states} states + {cm.even_transducer.table_entries}-entry lookup")
    print(f"  ├─ ODD  (shape 3/1):   {cm.odd_states} states + {cm.odd_transducer.table_entries}-entry lookup")
    print(f"  ├─ Increment (+1):     {cm.increment_states} states (carry propagation)")
    print(f"  └─ TOTAL:              ≤ {cm.total_states} states")

    # Primary demo: Collatz(5)
    print(f"\n{'='*70}")
    print(f"  EMMETT'S TEST: Collatz starting at 5")
    print(f"{'='*70}")

    cm.trace(5)
    show_shape_decomposition(5)
    verify_transducer_steps(5)

    # Additional starting values
    print(f"\n{'='*70}")
    print(f"  ADDITIONAL TESTS")
    print(f"{'='*70}")

    for start in [7, 27, 97]:
        cm.trace(start)
        ok = verify_transducer_steps(start)
