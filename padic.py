"""
p-adic integer arithmetic.

A p-adic integer is represented as a sequence of digits in base p,
stored least-significant-first: digits[0] is the units digit.

Key insight for this project: a 2-adic integer with digits [b₀, b₁, b₂, ...]
represents the formal sum b₀ + b₁·2 + b₂·4 + ... which is EXACTLY how a
binary Turing machine tape is laid out (LSB at the head, extending rightward).

So: ℤ₂ ≅ {one-sided infinite binary tapes}
"""

from __future__ import annotations
from typing import Optional
import math


class PAdic:
    """
    A p-adic integer to finite precision.
    
    Stored as a list of digits [d₀, d₁, d₂, ...] where
    the number = d₀ + d₁·p + d₂·p² + ...
    
    Each dᵢ ∈ {0, 1, ..., p-1}.
    """

    def __init__(self, p: int, digits: Optional[list[int]] = None, precision: int = 64):
        assert p >= 2, f"p must be >= 2, got {p}"
        self.p = p
        self.precision = precision
        if digits is None:
            self.digits = [0] * precision
        else:
            # Normalize: ensure all digits are in [0, p-1]
            d = list(digits) + [0] * max(0, precision - len(digits))
            d = d[:precision]
            self._normalize(d)
            self.digits = d

    def _normalize(self, d: list[int]):
        """Carry-propagate so all digits are in [0, p-1]."""
        for i in range(len(d) - 1):
            if d[i] < 0:
                borrow = (-d[i] + self.p - 1) // self.p
                d[i] += borrow * self.p
                d[i + 1] -= borrow
            if d[i] >= self.p:
                carry = d[i] // self.p
                d[i] %= self.p
                d[i + 1] += carry
        d[-1] %= self.p  # Truncate at precision

    @classmethod
    def from_int(cls, p: int, n: int, precision: int = 64) -> PAdic:
        """
        Create a p-adic integer from a Python int.
        
        For non-negative n, this gives the standard base-p expansion.
        For negative n, this gives the p-adic representation (all digits eventually p-1).
        """
        digits = []
        if n >= 0:
            val = n
            for _ in range(precision):
                digits.append(val % p)
                val //= p
        else:
            # p-adic representation of negative number:
            # -1 = (p-1) + (p-1)·p + (p-1)·p² + ... (all digits p-1)
            # In general, compute in mod p^precision
            mod = p ** precision
            val = n % mod  # This gives the correct p-adic digits
            for _ in range(precision):
                digits.append(val % p)
                val //= p
        return cls(p, digits, precision)

    def to_int(self) -> int:
        """
        Convert to Python int (only meaningful for 'small' p-adic integers).
        
        Returns the value mod p^precision.
        """
        result = 0
        for i in range(len(self.digits) - 1, -1, -1):
            result = result * self.p + self.digits[i]
        return result

    def to_signed_int(self) -> int:
        """
        Convert to signed Python int.
        
        If the leading digit is >= p/2, treat as negative.
        """
        val = self.to_int()
        mod = self.p ** self.precision
        if val > mod // 2:
            return val - mod
        return val

    def __add__(self, other: PAdic) -> PAdic:
        assert self.p == other.p, "Cannot add p-adic numbers with different p"
        prec = max(self.precision, other.precision)
        d = [0] * prec
        for i in range(prec):
            a = self.digits[i] if i < len(self.digits) else 0
            b = other.digits[i] if i < len(other.digits) else 0
            d[i] = a + b
        return PAdic(self.p, d, prec)

    def __sub__(self, other: PAdic) -> PAdic:
        assert self.p == other.p
        prec = max(self.precision, other.precision)
        d = [0] * prec
        for i in range(prec):
            a = self.digits[i] if i < len(self.digits) else 0
            b = other.digits[i] if i < len(other.digits) else 0
            d[i] = a - b
        return PAdic(self.p, d, prec)

    def __mul__(self, other: PAdic) -> PAdic:
        assert self.p == other.p
        prec = min(self.precision, other.precision)
        d = [0] * prec
        for i in range(prec):
            for j in range(prec - i):
                d[i + j] += self.digits[i] * other.digits[j]
        return PAdic(self.p, d, prec)

    def mod_p(self) -> int:
        """Return the units digit (value mod p). For ℤ₂, this reads one bit."""
        return self.digits[0]

    def shift_right(self) -> PAdic:
        """
        Divide by p (shift digits right, dropping the least significant).
        
        For a 2-adic tape, this is equivalent to moving the TM head one cell right:
        the cell at the head is dropped, and all remaining cells shift down.
        """
        return PAdic(self.p, self.digits[1:] + [0], self.precision)

    def shift_left(self, new_digit: int = 0) -> PAdic:
        """
        Multiply by p and add a new least-significant digit.
        
        For a 2-adic tape, this is prepending a cell at the head position.
        """
        return PAdic(self.p, [new_digit] + self.digits[:self.precision - 1], self.precision)

    def valuation(self) -> int:
        """
        p-adic valuation: the exponent of the highest power of p dividing this number.
        
        v_p(0) = precision (infinity, capped).
        For the tape: counts how many leading zeros.
        """
        for i, d in enumerate(self.digits):
            if d != 0:
                return i
        return self.precision  # "infinity"

    def norm(self) -> float:
        """
        p-adic absolute value: |x|_p = p^(-v_p(x)).
        
        |0|_p = 0 by convention.
        """
        v = self.valuation()
        if v >= self.precision:
            return 0.0
        return self.p ** (-v)

    def digit_string(self, n: Optional[int] = None) -> str:
        """Show first n digits as ...d₃d₂d₁d₀ (most significant on left)."""
        if n is None:
            # Show up to last nonzero digit + 1
            last = 0
            for i, d in enumerate(self.digits):
                if d != 0:
                    last = i
            n = max(last + 1, 1)
        n = min(n, self.precision)
        return ''.join(str(self.digits[i]) for i in range(n - 1, -1, -1))

    def __repr__(self) -> str:
        return f"PAdic({self.p}, ...{self.digit_string(8)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PAdic):
            return NotImplemented
        if self.p != other.p:
            return False
        n = min(self.precision, other.precision)
        return self.digits[:n] == other.digits[:n]


# ─── Utility Functions ────────────────────────────────────────────────


def tape_to_2adic(tape_cells: list[int], precision: int = 64) -> PAdic:
    """
    Convert a list of binary tape cells to a 2-adic integer.
    
    tape_cells[0] is the cell at the head, tape_cells[1] is one step right, etc.
    This IS the 2-adic expansion: cell[i] is the coefficient of 2^i.
    
    The identification is:
        tape = [b₀, b₁, b₂, ...] ↔ b₀ + b₁·2 + b₂·4 + ... ∈ ℤ₂
    """
    return PAdic(2, tape_cells, precision)


def twoadicto_tape(x: PAdic, length: int = 32) -> list[int]:
    """Convert a 2-adic integer back to tape cells."""
    assert x.p == 2
    return x.digits[:length]
