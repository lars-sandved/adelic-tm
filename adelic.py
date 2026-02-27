"""
Adele ring elements and TM configuration encoding.

An adele a in A_Q is a tuple (a_inf, a_2, a_3, a_5, ...) where:
  - a_inf in R          (Archimedean place)
  - a_p in Q_p          (p-adic places, one per prime)
  - Almost all a_p in Z_p (integrality condition)

We encode a TM configuration as an adele:
  - a_2 in Z_2  -> tape to the RIGHT of the head (binary cells = 2-adic digits)
  - a_3 in Z_3  -> tape to the LEFT of the head (binary values encoded in base 3)
  - a_5 in Z_5  -> machine state (state number as a 5-adic integer)
  - a_inf in R  -> step counter

The key insight: for the binary incrementer, the ENTIRE computation
is just +1 in the 2-adic component. Carry propagation in the TM
corresponds exactly to carry propagation in Z_2 arithmetic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from padic import PAdic, tape_to_2adic, twoadicto_tape
from turing import TMConfig, L, R, S


PRECISION = 64


@dataclass
class Adele:
    """
    An element of the adele ring A_Q (finite approximation).
    
    real_part: the Archimedean component a_inf
    padic_parts: dict mapping prime p -> PAdic element a_p
    """
    real_part: float
    padic_parts: dict[int, PAdic] = field(default_factory=dict)

    def __repr__(self) -> str:
        parts = [f"inf={self.real_part:.1f}"]
        for p in sorted(self.padic_parts):
            parts.append(f"{p}={self.padic_parts[p]}")
        return f"Adele({', '.join(parts)})"

    def component(self, p: int) -> PAdic:
        return self.padic_parts[p]

    def norms(self) -> dict[str, float]:
        """Compute |a|_v at each place. Product formula: prod |a|_v = 1 for a in Q*."""
        result: dict[str, float] = {"inf": abs(self.real_part)}
        for p, x in self.padic_parts.items():
            result[str(p)] = x.norm()
        return result


def tm_config_to_adele(config: TMConfig, precision: int = PRECISION) -> Adele:
    """
    Encode a Turing machine configuration as an adele.
    
    a_2 = tape cells right of head (including head cell), as 2-adic integer
    a_3 = tape cells left of head, as 3-adic integer (binary vals in base 3)
    a_p = machine state as p-adic integer (p = STATE_PRIME, chosen >= max state + 1)
    a_inf = step count
    """
    right_cells = config.right_of_head(precision)
    alpha_2 = tape_to_2adic(right_cells, precision)

    left_cells = config.left_of_head(precision)
    alpha_3 = PAdic(3, left_cells, precision)

    alpha_5 = PAdic.from_int(23, config.state, precision)
    alpha_inf = float(config.step)

    return Adele(
        real_part=alpha_inf,
        padic_parts={2: alpha_2, 3: alpha_3, 23: alpha_5},
    )


def adele_to_tm_config(adele: Adele, precision: int = PRECISION) -> TMConfig:
    """Decode an adele back to a TM configuration. Inverse of tm_config_to_adele."""
    right_cells = twoadicto_tape(adele.padic_parts[2], precision)
    left_cells = adele.padic_parts[3].digits[:precision]
    state = adele.padic_parts[23].to_int() % 23
    step = int(adele.real_part)

    tape: dict[int, int] = {}
    for i, v in enumerate(right_cells):
        if v != 0:
            tape[i] = v
    for i, v in enumerate(left_cells):
        if v != 0:
            tape[-1 - i] = v

    return TMConfig(state=state, tape=tape, head=0, step=step)


def adelic_step(adele: Adele, transition_table: dict) -> Adele:
    """
    Advance one TM step using adelic operations.
    
    1. READ: current symbol = a_2 mod 2  (units digit of 2-adic component)
    2. LOOKUP: (state, symbol) -> (new_state, write, direction) from table
    3. WRITE + MOVE: modify a_2 and a_3 according to direction
    4. UPDATE STATE: modify a_5
    5. INCREMENT STEP: a_inf += 1
    
    For the binary incrementer, steps 1-4 collapse to: a_2 -> a_2 + 1 in Z_2.
    """
    alpha_2 = adele.padic_parts[2]
    alpha_3 = adele.padic_parts[3]
    alpha_5 = adele.padic_parts[23]

    current_symbol = alpha_2.mod_p()
    current_state = alpha_5.digits[0]
    key = (current_state, current_symbol)
    if key not in transition_table:
        return adele  # Halt

    new_state, write_symbol, direction = transition_table[key]

    # WRITE + MOVE via p-adic operations
    # Right tape a_2 = [cell_at_head, cell_right_1, ...]  (2-adic digits)
    # Left tape  a_3 = [cell_left_1, cell_left_2, ...]    (3-adic digits)

    if direction == R:
        # Write to current cell, move right
        # Left tape gets write_symbol prepended, right tape drops head cell
        new_alpha_3 = alpha_3.shift_left(write_symbol)
        new_alpha_2 = alpha_2.shift_right()

    elif direction == L:
        # Write to current cell, move left
        # Right tape gets [old_left_cell, write_symbol, old_right[1:]]
        # Left tape drops its nearest cell
        old_left_cell = alpha_3.digits[0]
        new_alpha_2 = PAdic(
            2,
            [old_left_cell, write_symbol] + alpha_2.digits[1:alpha_2.precision - 1],
            alpha_2.precision,
        )
        new_alpha_3 = alpha_3.shift_right()

    else:  # Stay
        new_alpha_2 = PAdic(
            2,
            [write_symbol] + alpha_2.digits[1:],
            alpha_2.precision,
        )
        new_alpha_3 = alpha_3

    new_alpha_5 = PAdic.from_int(23, new_state, alpha_5.precision)
    new_real = adele.real_part + 1.0

    return Adele(
        real_part=new_real,
        padic_parts={2: new_alpha_2, 3: new_alpha_3, 23: new_alpha_5},
    )


def adelic_increment(adele: Adele) -> Adele:
    """
    Special case: binary incrementer as pure 2-adic addition.
    
    Instead of step-by-step TM simulation, we add 1 to the 2-adic component.
    This is the KEY DEMONSTRATION: the entire carry-propagation computation
    is captured by a SINGLE arithmetic operation in Z_2.
    """
    one = PAdic.from_int(2, 1, adele.padic_parts[2].precision)
    new_alpha_2 = adele.padic_parts[2] + one

    new_parts = dict(adele.padic_parts)
    new_parts[2] = new_alpha_2
    new_parts[23] = PAdic.from_int(23, 1, adele.padic_parts[23].precision)

    return Adele(real_part=adele.real_part + 1.0, padic_parts=new_parts)
