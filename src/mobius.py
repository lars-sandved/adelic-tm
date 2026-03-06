"""Möbius matrix and shear factor utilities.

Combines our exact-arithmetic MobiusMatrix with Emmett's ShearFactor semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


class MobiusMatrix:
    """A 2×2 integer matrix [[a,b],[c,d]] acting as Möbius transformation.

    Acts on x as: x → (ax + b) / (cx + d)

    Key matrices:
        P_k = ((k,1),(1,0))  — push k onto CF stack
        Q_k = ((0,1),(1,-k)) — pop k from CF stack (Gauss map)
        S(k) = ((1,k),(0,1)) — upper shear
        J    = ((0,1),(1,0))  — swap (J² = I)
    """

    __slots__ = ("a", "b", "c", "d")

    def __init__(self, a: int, b: int, c: int, d: int):
        self.a, self.b, self.c, self.d = int(a), int(b), int(c), int(d)

    # --- Named constructors ---

    @staticmethod
    def push(k: int) -> "MobiusMatrix":
        """P_k = ((k,1),(1,0)) — push symbol k onto CF stack."""
        return MobiusMatrix(k, 1, 1, 0)

    @staticmethod
    def pop(k: int) -> "MobiusMatrix":
        """Q_k = ((0,1),(1,-k)) — pop symbol k from CF stack."""
        return MobiusMatrix(0, 1, 1, -k)

    @staticmethod
    def shear(k: int) -> "MobiusMatrix":
        """S(k) = ((1,k),(0,1)) — upper shear."""
        return MobiusMatrix(1, k, 0, 1)

    @staticmethod
    def swap() -> "MobiusMatrix":
        """J = ((0,1),(1,0)) — swap. J² = I."""
        return MobiusMatrix(0, 1, 1, 0)

    @staticmethod
    def identity() -> "MobiusMatrix":
        """I = ((1,0),(0,1))."""
        return MobiusMatrix(1, 0, 0, 1)

    # --- Operations ---

    def __matmul__(self, other: "MobiusMatrix") -> "MobiusMatrix":
        """Matrix multiplication: self @ other."""
        return MobiusMatrix(
            self.a * other.a + self.b * other.c,
            self.a * other.b + self.b * other.d,
            self.c * other.a + self.d * other.c,
            self.c * other.b + self.d * other.d,
        )

    def act(self, x: Fraction) -> Fraction:
        """Apply Möbius transformation: x → (ax + b) / (cx + d)."""
        num = self.a * x + self.b
        den = self.c * x + self.d
        if den == 0:
            raise ValueError(f"Möbius transform undefined: denominator = 0 for x={x}")
        return Fraction(num, den)

    def det(self) -> int:
        """Determinant ad - bc."""
        return self.a * self.d - self.b * self.c

    def as_list(self) -> list[list[int]]:
        """Return as [[a,b],[c,d]] for serialization."""
        return [[self.a, self.b], [self.c, self.d]]

    def __eq__(self, other):
        if not isinstance(other, MobiusMatrix):
            return False
        return self.a == other.a and self.b == other.b and self.c == other.c and self.d == other.d

    def __repr__(self):
        return f"[({self.a},{self.b}),({self.c},{self.d})]"

    def pretty(self) -> str:
        return f"┌{self.a:3d} {self.b:3d}┐\n└{self.c:3d} {self.d:3d}┘"


@dataclass(frozen=True)
class ShearFactor:
    """Semantic factor for a computational step.

    kind='push': step pushed symbol k → matrix P_k = S(k)·J
    kind='pop':  step popped symbol k → matrix Q_k = J·S(-k)
    """

    kind: str  # "push" or "pop"
    k: int

    @property
    def word(self) -> str:
        if self.kind == "push":
            return f"S({self.k})J"
        if self.kind == "pop":
            return f"JS({-self.k})"
        raise ValueError(f"unknown factor kind: {self.kind}")

    def to_matrix(self) -> MobiusMatrix:
        if self.kind == "push":
            return MobiusMatrix.push(self.k)
        if self.kind == "pop":
            return MobiusMatrix.pop(self.k)
        raise ValueError(f"unknown factor kind: {self.kind}")

    def to_dict(self) -> dict:
        return {"kind": self.kind, "k": self.k}


def mat_mul_lists(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    """Multiply two 2x2 matrices in list form."""
    return [
        [a[0][0] * b[0][0] + a[0][1] * b[1][0], a[0][0] * b[0][1] + a[0][1] * b[1][1]],
        [a[1][0] * b[0][0] + a[1][1] * b[1][0], a[1][0] * b[0][1] + a[1][1] * b[1][1]],
    ]
