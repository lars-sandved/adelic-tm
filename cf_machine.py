"""
CF-based Adelic Turing Machine

This module implements the continued fraction (CF) approach to encoding
Turing machine computation in adelic arithmetic:

- TAPE lives at the Archimedean (real) place: encoded as a continued fraction
- STATE MACHINE lives in p-adic components: state as residue mod prime
- STEPPING = applying the Gauss map G(x) = 1/(x - floor(x)) to read CF digits

Uses fractions.Fraction for exact rational arithmetic throughout.
"""

from fractions import Fraction
from typing import Optional


def encode_tape(
    symbols: list[int],
    symbol_map: Optional[dict[int, int]] = None,
    add_end_marker: bool = True
) -> Fraction:
    """
    Encode a list of symbols as a continued fraction (rational number).

    CF digits must be >= 1, so we map symbols:
    - 0 -> 1
    - 1 -> 2
    - blank/end marker -> 3

    Or accept a custom symbol_map.

    The CF is built bottom-up:
    [a0; a1, a2, ..., an] = a0 + 1/(a1 + 1/(a2 + ... + 1/an))

    Args:
        symbols: List of tape symbols (e.g., [1, 0, 1, 1])
        symbol_map: Optional mapping from symbol to CF digit (must be >= 1)
        add_end_marker: If True, append end marker to CF (default True)

    Returns:
        Fraction representing the tape as a continued fraction
    """
    if symbol_map is None:
        # Default: 0->1, 1->2, 2 (blank/end)->3
        symbol_map = {0: 1, 1: 2, 2: 3, 'end': 3, 'blank': 3}

    # Convert symbols to CF digits
    cf_digits = []
    for s in symbols:
        if s in symbol_map:
            cf_digits.append(symbol_map[s])
        else:
            raise ValueError(f"Symbol {s} not in symbol_map")

    # Optionally add end marker
    if add_end_marker:
        cf_digits.append(symbol_map.get('end', symbol_map.get(2, 3)))

    # Build CF bottom-up: start from the last digit
    if not cf_digits:
        if add_end_marker:
            return Fraction(3)  # Just end marker
        else:
            return Fraction(0)  # Empty tape, no encoding

    # Start with the last digit
    result = Fraction(cf_digits[-1])

    # Work backwards: x = a + 1/x
    for digit in reversed(cf_digits[:-1]):
        result = Fraction(digit) + Fraction(1, 1) / result

    return result


def gauss_map(x: Fraction) -> tuple[int, Fraction]:
    """
    Apply the Gauss map G(x) = 1/(x - floor(x)).

    This extracts one continued fraction digit:
    - cf_digit = floor(x)
    - remainder = 1/(x - floor(x))

    Args:
        x: A Fraction > 1 (or >= 1 for the last digit)

    Returns:
        (cf_digit, remainder) where cf_digit is the integer part
        and remainder is the next CF value.

    Raises:
        ValueError: if x <= 0 or x is exactly an integer (no remainder)
    """
    if x <= 0:
        raise ValueError(f"Gauss map requires x > 0, got {x}")

    # floor(x) for a Fraction
    cf_digit = int(x)  # This gives floor for positive Fractions

    fractional_part = x - cf_digit

    if fractional_part == 0:
        # x is an integer - this is the last CF digit
        return (cf_digit, Fraction(0))

    remainder = Fraction(1, 1) / fractional_part

    return (cf_digit, remainder)


def inverse_gauss(digit: int, remainder: Fraction) -> Fraction:
    """
    Inverse of the Gauss map: push a digit onto the front of a CF.

    Given CF [a1; a2, ...] (represented by remainder), construct [digit; a1, a2, ...]

    The inverse is: x = digit + 1/remainder

    Args:
        digit: The CF digit to push (must be >= 1)
        remainder: The rest of the CF as a Fraction

    Returns:
        The new CF with digit prepended
    """
    if digit < 1:
        raise ValueError(f"CF digit must be >= 1, got {digit}")

    if remainder == 0:
        # Pushing onto empty CF - the digit becomes a standalone integer
        return Fraction(digit)

    return Fraction(digit) + Fraction(1, 1) / remainder


def decode_tape(x: Fraction, max_steps: int = 100) -> list[int]:
    """
    Decode a CF-encoded tape back to CF digits by repeatedly applying Gauss map.

    Args:
        x: The CF-encoded tape as a Fraction
        max_steps: Maximum number of digits to extract

    Returns:
        List of CF digits (NOT the original symbols - caller must reverse the symbol_map)
    """
    digits = []
    current = x

    for _ in range(max_steps):
        if current == 0:
            break

        digit, remainder = gauss_map(current)
        digits.append(digit)

        if remainder == 0:
            break

        current = remainder

    return digits


def cf_digits_to_symbols(cf_digits: list[int], symbol_map: Optional[dict[int, int]] = None) -> list[int]:
    """
    Convert CF digits back to original tape symbols.

    Args:
        cf_digits: List of CF digits
        symbol_map: The original symbol -> CF digit mapping

    Returns:
        List of original symbols (without the end marker)
    """
    if symbol_map is None:
        symbol_map = {0: 1, 1: 2, 2: 3, 'end': 3, 'blank': 3}

    # Build reverse map (CF digit -> symbol)
    reverse_map = {}
    for sym, digit in symbol_map.items():
        if sym not in ('end', 'blank'):
            reverse_map[digit] = sym

    # The last digit is typically the end marker, exclude it
    symbols = []
    end_marker = symbol_map.get('end', symbol_map.get(2, 3))

    for d in cf_digits:
        if d == end_marker and d == cf_digits[-1]:
            # Skip end marker at the end
            continue
        if d in reverse_map:
            symbols.append(reverse_map[d])
        else:
            # Unknown digit - might be end marker in middle or something else
            symbols.append(d)

    return symbols


def p_adic_valuation(n: int, p: int) -> int:
    """
    Compute the p-adic valuation v_p(n) = max power of p dividing n.

    Args:
        n: Integer (if 0, returns infinity represented as -1)
        p: Prime number

    Returns:
        The exponent k such that p^k divides n but p^(k+1) doesn't.
        Returns -1 for n=0 (representing infinity).
    """
    if n == 0:
        return -1  # Convention for infinity

    n = abs(n)
    count = 0
    while n % p == 0:
        n //= p
        count += 1
    return count


def p_adic_norm(x: Fraction, p: int) -> Fraction:
    """
    Compute the p-adic absolute value |x|_p = p^(-v_p(x)).

    For x = a/b, v_p(x) = v_p(a) - v_p(b).

    Args:
        x: A Fraction
        p: A prime number

    Returns:
        |x|_p as a Fraction
    """
    if x == 0:
        return Fraction(0)

    v_num = p_adic_valuation(x.numerator, p)
    v_den = p_adic_valuation(x.denominator, p)
    v = v_num - v_den

    # |x|_p = p^(-v)
    if v >= 0:
        return Fraction(1, p ** v)
    else:
        return Fraction(p ** (-v), 1)


def real_norm(x: Fraction) -> Fraction:
    """
    Compute the real (Archimedean) absolute value |x|_∞.

    Args:
        x: A Fraction

    Returns:
        |x| as a Fraction (always non-negative)
    """
    if x < 0:
        return -x
    return x


def verify_product_formula(x: Fraction, primes: list[int] = None) -> dict:
    """
    Verify the product formula: |x|_∞ * ∏_p |x|_p = 1 for x ∈ ℚ*.

    We only need primes dividing the numerator or denominator.

    Args:
        x: A non-zero Fraction
        primes: Optional list of primes to check. If None, finds relevant primes.

    Returns:
        Dict with verification results
    """
    if x == 0:
        return {"valid": False, "error": "x = 0, product formula undefined"}

    # Find all primes dividing numerator or denominator
    if primes is None:
        primes = set()
        for n in [abs(x.numerator), x.denominator]:
            temp = n
            d = 2
            while d * d <= temp:
                while temp % d == 0:
                    primes.add(d)
                    temp //= d
                d += 1
            if temp > 1:
                primes.add(temp)
        primes = sorted(primes)

    real = real_norm(x)

    p_adic_norms = {}
    product = real
    for p in primes:
        norm_p = p_adic_norm(x, p)
        p_adic_norms[p] = norm_p
        product *= norm_p

    return {
        "valid": product == 1,
        "x": x,
        "real_norm": real,
        "p_adic_norms": p_adic_norms,
        "product": product,
        "primes_used": primes
    }


class AdelicTM:
    """
    Adelic Turing Machine using continued fraction tape encoding.

    The tape is encoded as a continued fraction (real number).
    The state machine lives in p-adic components (state as residue mod prime).

    Supports:
    - Read-only machines (like parity checker) using single right-tape
    - Read-write machines (like incrementer) using dual-tape (left + right)
    """

    def __init__(
        self,
        transitions: dict,
        initial_state: int,
        state_prime: int = 2,
        halt_states: set = None,
        symbol_map: dict = None
    ):
        """
        Initialize the Adelic TM.

        Args:
            transitions: Dict mapping (state, symbol) -> (new_state, write_symbol, direction)
                        direction is 'R' (right), 'L' (left), or 'H' (halt)
            initial_state: Starting state (integer)
            state_prime: Which prime encodes state (default 2)
            halt_states: Set of halt states (optional, can also use 'H' direction)
            symbol_map: Symbol to CF digit mapping (default: 0->1, 1->2, blank->3)
        """
        self.transitions = transitions
        self.initial_state = initial_state
        self.state_prime = state_prime
        self.halt_states = halt_states or set()

        if symbol_map is None:
            self.symbol_map = {0: 1, 1: 2, 2: 3, 'end': 3, 'blank': 3}
        else:
            self.symbol_map = symbol_map

        # Build reverse map for CF digit -> symbol
        self.reverse_symbol_map = {}
        for sym, digit in self.symbol_map.items():
            if sym not in ('end', 'blank'):
                self.reverse_symbol_map[digit] = sym

        # Runtime state
        self.state = initial_state
        self.right_tape: Fraction = Fraction(0)  # Tape to the right of head (includes current cell)
        self.left_tape: Fraction = Fraction(0)   # Tape to the left of head
        self.halted = False
        self.step_count = 0

    def encode_state(self, state: int) -> int:
        """
        Encode state as residue mod state_prime.

        Args:
            state: The state number

        Returns:
            state mod state_prime
        """
        return state % self.state_prime

    def _digit_to_symbol(self, cf_digit: int) -> int:
        """Convert a CF digit back to the original symbol."""
        return self.reverse_symbol_map.get(cf_digit, cf_digit)

    def _symbol_to_digit(self, symbol: int) -> int:
        """Convert a symbol to its CF digit."""
        return self.symbol_map.get(symbol, symbol)

    def step(self) -> dict:
        """
        Perform one computation step.

        1. Read CF digit from right_tape (Gauss map)
        2. Convert to symbol, lookup transition
        3. Write (possibly modified) symbol
        4. Move head (update left/right tapes)
        5. Update state

        Returns:
            Dict with step details: cf_digit_read, symbol_read, state_before, state_after,
            new_state, write_symbol, direction, right_tape_before, right_tape_after, etc.
        """
        if self.halted:
            return {"halted": True, "step": self.step_count}

        result = {
            "step": self.step_count,
            "state_before": self.state,
            "right_tape_before": self.right_tape,
            "left_tape_before": self.left_tape,
        }

        # Check if tape is empty (shouldn't happen with proper encoding)
        if self.right_tape == 0:
            # Treat as reading blank
            cf_digit = self.symbol_map.get('blank', 3)
            remainder = Fraction(0)
        else:
            # Apply Gauss map to read CF digit
            cf_digit, remainder = gauss_map(self.right_tape)

        symbol_read = self._digit_to_symbol(cf_digit)
        result["cf_digit_read"] = cf_digit
        result["symbol_read"] = symbol_read

        # Check for end marker
        end_digit = self.symbol_map.get('end', 3)
        if cf_digit == end_digit and remainder == 0:
            # Reached end of tape
            self.halted = True
            result["halted"] = True
            result["reason"] = "end_of_tape"
            result["state_after"] = self.state
            return result

        # Check for halt state
        if self.state in self.halt_states:
            self.halted = True
            result["halted"] = True
            result["reason"] = "halt_state"
            result["state_after"] = self.state
            return result

        # Lookup transition
        key = (self.state, symbol_read)
        if key not in self.transitions:
            # No transition defined - halt
            self.halted = True
            result["halted"] = True
            result["reason"] = "no_transition"
            result["state_after"] = self.state
            return result

        new_state, write_symbol, direction = self.transitions[key]
        result["new_state"] = new_state
        result["write_symbol"] = write_symbol
        result["direction"] = direction

        # Convert write_symbol to CF digit
        write_digit = self._symbol_to_digit(write_symbol)

        # Check for explicit halt - still perform the write, but don't move
        if direction == 'H':
            # Write the symbol at current position (replace the read digit)
            # right_tape was [current; rest...], becomes [write_digit; rest...]
            if remainder == 0:
                # Last cell - just the written digit
                self.right_tape = Fraction(write_digit)
            else:
                # Prepend written digit to remainder
                self.right_tape = inverse_gauss(write_digit, remainder)

            self.halted = True
            self.state = new_state
            result["halted"] = True
            result["reason"] = "halt_direction"
            result["state_after"] = self.state
            result["right_tape_after"] = self.right_tape
            result["left_tape_after"] = self.left_tape
            return result

        # Apply tape update based on direction
        if direction == 'R':
            # Move RIGHT: push write_digit onto left_tape, pop from right_tape
            # Left tape gets the written symbol
            if self.left_tape == 0:
                self.left_tape = Fraction(write_digit)
            else:
                self.left_tape = inverse_gauss(write_digit, self.left_tape)

            # Right tape advances (we already have remainder from Gauss map)
            self.right_tape = remainder

        elif direction == 'L':
            # Move LEFT: push write_digit onto right_tape, pop from left_tape
            # Right tape gets the written symbol prepended
            if remainder == 0:
                # We were at the last cell, write_digit becomes the only cell on right
                self.right_tape = Fraction(write_digit)
            else:
                self.right_tape = inverse_gauss(write_digit, remainder)

            # Pop from left tape
            if self.left_tape == 0:
                # No left tape - extend tape with a blank cell (symbol 0, CF digit 1)
                # This represents moving into a new blank cell to the left
                blank_digit = self.symbol_map.get('blank', self.symbol_map.get(0, 1))
                self.right_tape = inverse_gauss(blank_digit, self.right_tape)
                # left_tape remains 0 (still nothing further left)
            else:
                left_digit, left_remainder = gauss_map(self.left_tape)
                # The popped digit becomes the new current cell
                # We prepend it to right_tape (it's now our current position)
                self.right_tape = inverse_gauss(left_digit, self.right_tape)
                self.left_tape = left_remainder

        # Update state
        self.state = new_state

        result["state_after"] = self.state
        result["right_tape_after"] = self.right_tape
        result["left_tape_after"] = self.left_tape
        result["halted"] = False

        self.step_count += 1

        return result

    def run(
        self,
        tape_symbols: list[int],
        symbol_map: dict = None,
        max_steps: int = 1000,
        start_at: str = 'left'
    ) -> dict:
        """
        Run the TM on given input tape.

        Args:
            tape_symbols: List of tape symbols (e.g., [1, 0, 1, 1])
            symbol_map: Optional override for symbol mapping
            max_steps: Maximum number of steps before forced halt
            start_at: 'left' (head starts at leftmost cell) or 'right' (head starts at rightmost)

        Returns:
            Dict with execution trace and final state
        """
        # Reset state
        self.state = self.initial_state
        self.halted = False
        self.step_count = 0

        if symbol_map is not None:
            self.symbol_map = symbol_map
            self.reverse_symbol_map = {}
            for sym, digit in symbol_map.items():
                if sym not in ('end', 'blank'):
                    self.reverse_symbol_map[digit] = sym

        # Encode tape
        if start_at == 'left':
            # Head at left - entire tape is to the right
            self.right_tape = encode_tape(tape_symbols, self.symbol_map)
            self.left_tape = Fraction(0)
        elif start_at == 'right':
            # Head at right - entire tape is to the left (reversed)
            # Actually for right start, we reverse the symbols for left_tape
            # and right_tape starts with just the rightmost symbol
            if not tape_symbols:
                self.right_tape = encode_tape([], self.symbol_map)
                self.left_tape = Fraction(0)
            else:
                # Right tape has current (rightmost) cell + end marker
                self.right_tape = encode_tape([tape_symbols[-1]], self.symbol_map)
                # Left tape has the rest in reverse order
                if len(tape_symbols) > 1:
                    self.left_tape = encode_tape(list(reversed(tape_symbols[:-1])), self.symbol_map)
                else:
                    self.left_tape = Fraction(0)

        # Run
        trace = []
        trace.append({
            "step": "initial",
            "state": self.state,
            "right_tape": self.right_tape,
            "left_tape": self.left_tape,
            "tape_symbols": tape_symbols
        })

        steps_taken = 0
        while not self.halted and steps_taken < max_steps:
            step_result = self.step()
            trace.append(step_result)
            steps_taken += 1

        # Decode final tape state
        right_digits = decode_tape(self.right_tape) if self.right_tape else []
        left_digits = decode_tape(self.left_tape) if self.left_tape else []

        return {
            "final_state": self.state,
            "halted": self.halted,
            "steps_taken": steps_taken,
            "trace": trace,
            "right_tape_final": self.right_tape,
            "left_tape_final": self.left_tape,
            "right_digits_final": right_digits,
            "left_digits_final": left_digits,
        }

    def get_adelic_state(self) -> dict:
        """
        Get the current adelic representation.

        Returns:
            Dict with α∞ (right_tape), state residue mod prime, and product formula verification
        """
        return {
            "alpha_infinity": self.right_tape,
            "alpha_p": self.encode_state(self.state),
            "state_prime": self.state_prime,
            "state": self.state,
            "product_formula": verify_product_formula(self.right_tape) if self.right_tape else None
        }
