"""
Explicit Finite-State Transducer for Shape/Magnitude/CF
=========================================================

Proof of principle: the shape of a rational number determines a FIXED
finite-state machine. The magnitude is the input tape. The CF is the output.

Architecture (for shape p/q, integer magnitude M):

    INPUT: M's digit stream
           │
           ▼
    ┌──────────────────┐
    │ MULTIPLY BY p    │  (transducer, ≤p states for carry)
    │ M → pM           │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ LONG DIVISION    │  (transducer, q states for remainder)
    │ BY q             │──────▶ emit q₁ digits (first CF coefficient)
    │                  │
    │ accumulate r₁    │
    └────────┬─────────┘
             │  r₁ ∈ {0,...,q-1}
             ▼
    ┌──────────────────┐
    │ LOOKUP TABLE     │  (q entries, fixed by shape)
    │ r₁ → [q₂;q₃;...]│──────▶ emit remaining CF coefficients
    └──────────────────┘

    OUTPUT: CF = [q₁; q₂, q₃, ...]

Machine size: ≤ p × q states + q-entry lookup. ALL determined by shape.

Key insight: after the first Euclidean step, remainder r₁ < q ALWAYS,
regardless of M. So steps 2+ are a fixed finite computation.

References:
- Anashin's theorem: 1-Lipschitz maps on ℤ_p ↔ finite-state transducers
- Emmett Shear, "Continued Fractions from Magnitude and Shape" (2026)
"""

from fractions import Fraction
from math import floor
from shape_magnitude import cf, cf_to_rational, Shape


def build_lookup_table(denominator):
    """Build the complete lookup table for a shape with given denominator.

    For each possible remainder r₁ ∈ {0, 1, ..., denominator-1},
    compute CF(denominator / r₁) — the CF tail after the first step.

    This table is ENTIRELY determined by the denominator (= shape's denominator).
    It IS the program — the finite set of behaviors the machine can exhibit.

    Returns: dict mapping r₁ → list of CF coefficients (the tail)
    """
    table = {}
    for r in range(denominator):
        if r == 0:
            table[r] = []  # No remainder → computation halts
        else:
            # CF of denominator/r gives the tail [q₂; q₃, ...]
            table[r] = cf(Fraction(denominator, r))
    return table


class Transducer:
    """A finite-state transducer determined by a shape.

    For a shape S = p/q, the transducer:
    1. Multiplies input M by p (streaming, ≤p states)
    2. Divides by q via long division (q states for remainder)
    3. Looks up remaining CF from a q-entry table

    The machine is FIXED once the shape is chosen. Only M varies.
    """

    def __init__(self, shape_rational):
        """Build the transducer for a given shape.

        Args:
            shape_rational: A Fraction representing the shape (e.g., 36/25)
        """
        if not isinstance(shape_rational, Fraction):
            shape_rational = Fraction(shape_rational)

        self.shape = Shape(shape_rational)
        self.p = abs(shape_rational.numerator)    # multiply factor
        self.q = abs(shape_rational.denominator)   # divide factor

        # Build the lookup table (the "ROM" of the machine)
        self.lookup_table = build_lookup_table(self.q)

        # Machine metrics
        self.multiply_states = self.p  # carry register for multiplication
        self.division_states = self.q  # remainder register for long division
        self.total_states = self.p * self.q
        self.table_entries = self.q

    def run(self, M):
        """Run integer magnitude M through the transducer.

        Phase 1: Compute q₁ = ⌊pM/q⌋ and r₁ = pM mod q
        Phase 2: Look up CF tail from table[r₁]

        Returns: full CF [q₁; tail...]
        """
        if not isinstance(M, int):
            raise TypeError(f"Transducer.run() requires integer M, got {type(M)}")

        # Phase 1: multiply and divide
        pM = self.p * M
        q1 = pM // self.q        # first CF coefficient (streamed output)
        r1 = pM % self.q          # remainder (selects lookup table row)

        # Phase 2: lookup
        tail = self.lookup_table[r1]

        # Assemble full CF
        if r1 == 0:
            return [q1]  # exact division, no tail
        else:
            return [q1] + tail

    def verify(self, M):
        """Verify transducer output matches direct CF computation.

        Returns: (matches: bool, transducer_cf, direct_cf)
        """
        transducer_cf = self.run(M)
        direct_cf = cf(self.shape.rational * Fraction(M))
        return transducer_cf == direct_cf, transducer_cf, direct_cf

    def trace(self, M):
        """Run with full trace output showing machine internals."""
        pM = self.p * M
        q1 = pM // self.q
        r1 = pM % self.q
        tail = self.lookup_table[r1]
        full_cf = [q1] + tail if r1 != 0 else [q1]

        print(f"    Input:  M = {M}")
        print(f"    Phase 1: {self.p} × {M} = {pM}")
        print(f"             {pM} ÷ {self.q} = {q1} remainder {r1}")
        print(f"    Phase 2: table[{r1}] = {tail if r1 != 0 else '(halt)'}")
        print(f"    Output: CF = {full_cf}")
        return full_cf

    def print_lookup_table(self):
        """Display the full lookup table (the machine's program)."""
        print(f"\n  Lookup table for denominator {self.q}:")
        print(f"  {'r₁':>4s} │ CF tail")
        print(f"  {'─'*4}─┼{'─'*40}")
        for r in range(self.q):
            tail = self.lookup_table[r]
            marker = ""
            # Check which M values (1-10) land on this row
            hits = [m for m in range(1, 11) if (self.p * m) % self.q == r]
            if hits:
                marker = f"  ← M={','.join(str(m) for m in hits)}"
            print(f"  {r:>4d} │ {str(tail) if tail else '(halt)'}{marker}")


def analyze_machine_sizes():
    """Show how machine size scales with different shapes."""
    shapes = [
        Fraction(2, 1),
        Fraction(7, 1),
        Fraction(3, 2),
        Fraction(8, 3),
        Fraction(36, 25),
        Fraction(100, 7),
        Fraction(355, 113),
        Fraction(1000, 999),
    ]

    print(f"\n{'='*70}")
    print(f"  MACHINE SIZE ANALYSIS")
    print(f"{'='*70}")
    print(f"  {'Shape':>12s} │ {'Num(p)':>7s} │ {'Den(q)':>7s} │ {'States':>10s} │ {'Table':>6s} │ {'Primes':>10s}")
    print(f"  {'─'*12}─┼{'─'*7}─┼{'─'*7}─┼{'─'*10}─┼{'─'*6}─┼{'─'*10}")

    for s in shapes:
        shape = Shape(s)
        t = Transducer(s)
        primes = ",".join(str(p) for p in sorted(shape.valuations.keys()))
        print(f"  {str(s):>12s} │ {t.p:>7d} │ {t.q:>7d} │ {t.total_states:>10d} │ {t.table_entries:>6d} │ {primes:>10s}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  FINITE-STATE TRANSDUCER: SHAPE → MACHINE, MAGNITUDE → INPUT")
    print("=" * 70)

    # Build transducer for shape 36/25
    T = Transducer(Fraction(36, 25))

    print(f"\n  Shape: {T.shape.rational}")
    print(f"  Multiply by: {T.p}")
    print(f"  Divide by:   {T.q}")
    print(f"  Machine size: {T.total_states} states + {T.table_entries}-entry lookup")

    # Print the lookup table
    T.print_lookup_table()

    # Trace a few examples
    print(f"\n{'='*70}")
    print(f"  TRACED EXECUTIONS")
    print(f"{'='*70}")

    for M in [1, 2, 3, 5, 10, 25]:
        print(f"\n  M = {M}:")
        T.trace(M)

    # Verify M = 1 through 100
    print(f"\n{'='*70}")
    print(f"  VERIFICATION: M = 1 through 100")
    print(f"{'='*70}")

    failures = []
    for M in range(1, 101):
        ok, t_cf, d_cf = T.verify(M)
        if not ok:
            failures.append((M, t_cf, d_cf))

    if not failures:
        print(f"\n  ✓ All 100 magnitudes verified: transducer output = direct CF")
    else:
        print(f"\n  ✗ {len(failures)} failures:")
        for M, t_cf, d_cf in failures:
            print(f"    M={M}: transducer={t_cf}, direct={d_cf}")

    # Show which table rows are hit by M=1..25
    print(f"\n{'='*70}")
    print(f"  ROW ACTIVATION PATTERN (M=1..25)")
    print(f"{'='*70}")
    row_hits = {}
    for M in range(1, 26):
        r1 = (T.p * M) % T.q
        if r1 not in row_hits:
            row_hits[r1] = []
        row_hits[r1].append(M)

    for r in sorted(row_hits.keys()):
        ms = row_hits[r]
        tail = T.lookup_table[r]
        print(f"  r₁={r:>2d} │ M={','.join(str(m) for m in ms):>20s} │ tail={tail}")

    # Row coverage analysis
    rows_hit = len(row_hits)
    print(f"\n  {rows_hit}/{T.q} rows activated by M=1..25")
    if rows_hit == T.q:
        print(f"  All rows activated — full program coverage.")
    else:
        missing = set(range(T.q)) - set(row_hits.keys())
        print(f"  Missing rows: {sorted(missing)}")

    # Machine size analysis across shapes
    analyze_machine_sizes()

    # Verify other shapes too
    print(f"\n{'='*70}")
    print(f"  CROSS-SHAPE VERIFICATION")
    print(f"{'='*70}")

    for shape_q in [Fraction(8, 3), Fraction(7), Fraction(100, 7), Fraction(355, 113)]:
        T2 = Transducer(shape_q)
        fails = 0
        for M in range(1, 51):
            ok, _, _ = T2.verify(M)
            if not ok:
                fails += 1
        status = "✓" if fails == 0 else f"✗ ({fails} failures)"
        print(f"  Shape {str(shape_q):>10s}: {status}  (machine: {T2.total_states} states, {T2.table_entries}-entry table)")

    print(f"\n  Done.")
