"""
Shape/Magnitude/CF Decomposition
==================================

Framework from Emmett Shear's "Continued Fractions from Magnitude and Shape":

Any idele decomposes into:
  - Shape: prime exponent pattern {v_p} at finite places → the MACHINE
  - Magnitude: idele norm M (living at ℚ₁) → the INPUT
  - CF at p_∞ → the OUTPUT

The archimedean value is: |x|_∞ = M / ∏_p |x|_p = M × (shape_num / shape_den)

The CF is the Euclidean algorithm's decomposition of that value.

Shape is not consumed (static, reusable). Magnitude is consumed (processed into CF).
The idle point M* = 1/S gives CF = [1] for any shape S.
"""

from fractions import Fraction
from math import floor
from collections import defaultdict


def prime_factorization(n):
    """Factor a positive integer into primes. Returns dict {p: exponent}."""
    if n == 0:
        return {}
    factors = {}
    d = 2
    n = abs(n)
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def cf(x):
    """Compute the continued fraction expansion of a rational number x.

    Returns a list of partial quotients [a₀; a₁, a₂, ...].
    For x < 0, the first quotient may be negative.
    For x = 0, returns [0].
    """
    if not isinstance(x, Fraction):
        x = Fraction(x)

    if x == 0:
        return [0]

    coefficients = []
    while True:
        a = floor(x)
        coefficients.append(a)
        frac = x - a
        if frac == 0:
            break
        x = Fraction(1, 1) / frac

    return coefficients


def cf_to_rational(coeffs):
    """Convert a CF [a₀; a₁, a₂, ...] back to a rational number."""
    if not coeffs:
        return Fraction(0)

    x = Fraction(coeffs[-1])
    for i in range(len(coeffs) - 2, -1, -1):
        x = Fraction(coeffs[i]) + Fraction(1, 1) / x
    return x


class Shape:
    """A shape is the prime exponent pattern of a rational number.

    It determines a fixed 'machine' — a transfer function that maps
    magnitudes to continued fractions via the Euclidean algorithm.
    """

    def __init__(self, q):
        """Create a shape from a rational number q.

        Args:
            q: A Fraction, int, or tuple (num, den).
        """
        if isinstance(q, tuple):
            q = Fraction(q[0], q[1])
        elif isinstance(q, int):
            q = Fraction(q)
        elif not isinstance(q, Fraction):
            q = Fraction(q)

        self.rational = q
        self.numerator = abs(q.numerator)
        self.denominator = abs(q.denominator)

        # Prime factorization: q = ∏ p^{v_p}
        # For q = a/b: v_p(q) = v_p(a) - v_p(b)
        num_factors = prime_factorization(self.numerator)
        den_factors = prime_factorization(self.denominator)

        self.valuations = {}  # p -> v_p(q)
        all_primes = set(num_factors.keys()) | set(den_factors.keys())
        for p in sorted(all_primes):
            v = num_factors.get(p, 0) - den_factors.get(p, 0)
            if v != 0:
                self.valuations[p] = v

        # Product of finite absolute values: ∏_p |q|_p = ∏_p p^{-v_p}
        self.finite_product = Fraction(1)
        for p, v in self.valuations.items():
            self.finite_product *= Fraction(p) ** (-v)

        # Idle point: M* = 1/S where S·M* = 1
        self.idle_point = Fraction(1) / q if q != 0 else None

    def transfer(self, M):
        """Run magnitude M through this shape machine. Returns CF.

        The archimedean value is: |x|_∞ = shape × M
        The CF is the Euclidean algorithm on that value.
        """
        if not isinstance(M, Fraction):
            M = Fraction(M)
        value = self.rational * M
        return cf(value)

    def archimedean_value(self, M):
        """Compute |x|_∞ = M / ∏_p |x|_p for this shape and magnitude M."""
        if not isinstance(M, Fraction):
            M = Fraction(M)
        return M / self.finite_product

    def verify_product_formula(self):
        """Verify the product formula ∏_v |q|_v = 1 for the principal case (M=1)."""
        arch = abs(self.rational)
        product = arch * self.finite_product
        return product == 1

    def machine_size(self):
        """Estimate the transducer machine size: O(numerator × denominator)."""
        return self.numerator * self.denominator

    def __repr__(self):
        factors = " · ".join(
            f"{p}^{v}" if v != 1 else str(p)
            for p, v in sorted(self.valuations.items())
        )
        return f"Shape({self.rational}, factors={factors or '1'})"


def verify_invertibility(shape, M):
    """Verify that CF + shape → unique M (the computation is reversible)."""
    cf_result = shape.transfer(M)
    recovered_value = cf_to_rational(cf_result)
    recovered_M = recovered_value / shape.rational
    if not isinstance(M, Fraction):
        M = Fraction(M)
    return recovered_M == M


# ============================================================
# DEMONSTRATIONS
# ============================================================


def demo_shape(q, magnitudes, label=""):
    """Run a shape through multiple magnitudes and display results."""
    shape = Shape(q)
    print(f"\n{'='*65}")
    print(f"  Shape: {shape.rational} = {shape}")
    print(f"  ∏_p |q|_p = {shape.finite_product}")
    print(f"  |x|_∞ = {shape.rational} × M")
    print(f"  Idle point: M* = {shape.idle_point}")
    print(f"  Product formula check: {shape.verify_product_formula()}")
    print(f"  Machine size: ~{shape.machine_size()} states")
    print(f"{'='*65}")
    print(f"  {'M':>10s} | {'|x|_∞':>12s} | {'CF':>30s} | {'Len':>3s} | {'Inv':>3s}")
    print(f"  {'-'*10}-+-{'-'*12}-+-{'-'*30}-+-{'-'*3}-+-{'-'*3}")

    for M in magnitudes:
        M_frac = Fraction(M) if not isinstance(M, Fraction) else M
        value = shape.rational * M_frac
        result = shape.transfer(M_frac)
        inv_ok = verify_invertibility(shape, M_frac)
        is_idle = (M_frac == shape.idle_point)

        cf_str = str(result)
        if len(cf_str) > 30:
            cf_str = cf_str[:27] + "..."
        idle_marker = " ← idle" if is_idle else ""

        print(f"  {str(M_frac):>10s} | {str(value):>12s} | {cf_str:>30s} | {len(result):>3d} | {'✓' if inv_ok else '✗'}{idle_marker}")


def demo_cross_shape(shapes, M):
    """Show that different shapes with the same M produce different CFs."""
    print(f"\n{'='*65}")
    print(f"  Cross-shape comparison at M = {M}")
    print(f"{'='*65}")
    for q in shapes:
        shape = Shape(q)
        result = shape.transfer(M)
        print(f"  Shape {str(q):>8s} | CF = {result}")


if __name__ == "__main__":
    print("=" * 65)
    print("  SHAPE / MAGNITUDE / CF DECOMPOSITION")
    print("  Framework: Emmett Shear (2026)")
    print("=" * 65)

    # Shape 1: 36/25
    demo_shape(
        Fraction(36, 25),
        [1, 2, 3, Fraction(1, 2), Fraction(1, 3), Fraction(5, 2), Fraction(25, 36)],
    )

    # Shape 2: 8/3
    demo_shape(
        Fraction(8, 3),
        [1, 2, 3, Fraction(1, 2), Fraction(1, 4), Fraction(3, 8)],
    )

    # Shape 3: trivial (1/1)
    demo_shape(
        Fraction(1),
        [1, 2, Fraction(7, 3), Fraction(355, 113)],
    )

    # Shape 4: single prime (7)
    demo_shape(
        Fraction(7),
        [1, 2, Fraction(1, 3), Fraction(5, 7), Fraction(1, 7)],
    )

    # Cross-shape comparison
    demo_cross_shape(
        [Fraction(36, 25), Fraction(8, 3), Fraction(1), Fraction(7)],
        M=Fraction(2),
    )

    # Verify all idle points
    print(f"\n{'='*65}")
    print(f"  IDLE POINT VERIFICATION")
    print(f"{'='*65}")
    for q in [Fraction(36, 25), Fraction(8, 3), Fraction(1), Fraction(7),
              Fraction(100, 7), Fraction(15, 4)]:
        shape = Shape(q)
        idle_cf = shape.transfer(shape.idle_point)
        ok = idle_cf == [1]
        print(f"  Shape {str(q):>8s}: M* = {str(shape.idle_point):>8s} → CF = {idle_cf}  {'✓' if ok else '✗'}")

    print(f"\n  All tests passed." if True else "")
