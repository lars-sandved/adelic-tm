"""Continued fraction stack — exact arithmetic via fractions.Fraction.

This is the verification layer. The fast path uses symbol lists directly;
CFStack provides independent confirmation that CF values are correct.
"""

from __future__ import annotations

from fractions import Fraction

from .mobius import MobiusMatrix


class CFStack:
    """A stack of positive integer symbols encoded as a continued fraction.

    The stack [a₀, a₁, a₂, ...] encodes as CF [a₀; a₁, a₂, ...].
    All symbols must be ≥ 1 (alphabet shifted so blank = 1).

    Uses exact Fraction arithmetic throughout.
    """

    def __init__(self, symbols: list[int]):
        """Create from explicit symbol list. All must be ≥ 1."""
        if any(s < 1 for s in symbols):
            raise ValueError(f"All symbols must be ≥ 1, got {symbols}")
        self._symbols = list(symbols)

    @staticmethod
    def from_internal_stack(stack: list[int], blank_internal: int) -> "CFStack":
        """Build CFStack from an internal symbol list (as used by the fast path).

        Appends blank_internal as the 'tail' to make the CF finite and well-defined.
        An empty stack becomes just [blank_internal].
        """
        symbols = list(stack) if stack else []
        symbols.append(blank_internal)
        return CFStack(symbols)

    @staticmethod
    def blank(length: int = 50) -> "CFStack":
        """Blank tape: all 1s. CF value → golden ratio φ as length → ∞."""
        return CFStack([1] * length)

    @property
    def symbols(self) -> list[int]:
        return list(self._symbols)

    def push(self, k: int) -> "CFStack":
        """Push symbol k onto top of stack."""
        if k < 1:
            raise ValueError(f"Symbol must be ≥ 1, got {k}")
        return CFStack([k] + self._symbols)

    def pop(self) -> tuple[int, "CFStack"]:
        """Pop top symbol. Returns (symbol, remaining_stack)."""
        if not self._symbols:
            raise ValueError("Cannot pop from empty stack")
        return self._symbols[0], CFStack(self._symbols[1:])

    def value(self) -> Fraction:
        """Evaluate as exact Fraction. Computes from bottom up."""
        if not self._symbols:
            raise ValueError("Empty CF has no value")
        result = Fraction(self._symbols[-1])
        for i in range(len(self._symbols) - 2, -1, -1):
            result = Fraction(self._symbols[i]) + Fraction(1, result)
        return result

    def convergent_matrix(self) -> MobiusMatrix:
        """Convergent matrix: product of P_{aᵢ} for all symbols."""
        result = MobiusMatrix.identity()
        for s in self._symbols:
            result = result @ MobiusMatrix.push(s)
        return result

    def __len__(self):
        return len(self._symbols)

    def __repr__(self):
        if len(self._symbols) <= 8:
            inner = ", ".join(str(s) for s in self._symbols)
        else:
            inner = ", ".join(str(s) for s in self._symbols[:6]) + ", ..."
        return f"CF[{inner}]"


def cf_value_from_stack(stack: list[int], blank_internal: int) -> Fraction:
    """Compute exact CF value from an internal symbol list.

    This is a convenience function for the verification layer.
    """
    return CFStack.from_internal_stack(stack, blank_internal).value()
