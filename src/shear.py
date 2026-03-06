"""Shear expansion — full computation as matrix products over GL(2,ℤ).

Tracks separate products for right and left stacks, giving Φ_R and Φ_L
such that:
    final_R = Φ_R · act(initial_R)
    final_L = Φ_L · act(initial_L)
"""

from __future__ import annotations

from .mobius import MobiusMatrix, ShearFactor


class ShearExpansion:
    """Collects matrices from a computation into the Shear expansion Φ(γ).

    Tracks separate products for the right and left stacks.
    Each step records one or more ShearFactors.
    """

    def __init__(self):
        self.right_matrices: list[MobiusMatrix] = []
        self.left_matrices: list[MobiusMatrix] = []
        self.right_product = MobiusMatrix.identity()
        self.left_product = MobiusMatrix.identity()
        self.step_factors: list[list[ShearFactor]] = []  # factors per step

    def record_right(self, m: MobiusMatrix):
        """Record a matrix applied to the right stack."""
        self.right_matrices.append(m)
        self.right_product = m @ self.right_product  # Left-multiply (newest first)

    def record_left(self, m: MobiusMatrix):
        """Record a matrix applied to the left stack."""
        self.left_matrices.append(m)
        self.left_product = m @ self.left_product

    def record_step(self, factors: list[ShearFactor]):
        """Record the semantic factors for one computational step."""
        self.step_factors.append(factors)

    @property
    def phi_R(self) -> MobiusMatrix:
        """Total Möbius transformation on the right stack."""
        return self.right_product

    @property
    def phi_L(self) -> MobiusMatrix:
        """Total Möbius transformation on the left stack."""
        return self.left_product

    def all_matrices(self) -> list[list[list[int]]]:
        """All step matrices in list form (for Lean export)."""
        result = []
        for factors in self.step_factors:
            for f in factors:
                result.append(f.to_matrix().as_list())
        return result

    def factor_into_shears(self) -> list[tuple[str, int]]:
        """Factor all matrices into S(k) and J components.

        P_k = S(k) · J → [('S', k), ('J', 0)]
        Q_k = J · S(-k) → [('J', 0), ('S', -k)]
        """
        factors = []
        for m in self.right_matrices + self.left_matrices:
            if m.c == 1 and m.d == 0 and m.b == 1:
                k = m.a
                factors.append(("S", k))
                factors.append(("J", 0))
            elif m.a == 0 and m.b == 1 and m.c == 1:
                k = -m.d
                factors.append(("J", 0))
                factors.append(("S", -k))
            else:
                factors.append(("?", 0))
        return factors

    def summary(self) -> str:
        lines = [
            "Shear Expansion Summary:",
            f"  Right stack: {len(self.right_matrices)} matrices",
            f"  Left stack:  {len(self.left_matrices)} matrices",
            f"  Φ_R = {self.right_product}  (det = {self.right_product.det()})",
            f"  Φ_L = {self.left_product}  (det = {self.left_product.det()})",
            f"  Steps: {len(self.step_factors)}",
        ]
        return "\n".join(lines)
