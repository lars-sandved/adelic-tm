"""
Turing Machine simulator with execution tracing.

A Turing machine is defined by a transition table mapping (state, symbol) -> (new_state, write_symbol, direction).
The tape is infinite in both directions, represented as a defaultdict with 0 (blank) as default.
"""

from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# Directions
L, R, S = 'L', 'R', 'S'  # Left, Right, Stay


@dataclass
class TMConfig:
    """A snapshot of a Turing machine configuration."""
    state: int
    tape: dict[int, int]
    head: int
    step: int

    def tape_contents(self, margin: int = 4) -> tuple[list[int], int]:
        """Return tape cells around the head as a list + offset."""
        if not self.tape:
            cells = [0] * (2 * margin + 1)
            return cells, margin
        lo = min(min(self.tape.keys()), self.head) - margin
        hi = max(max(self.tape.keys()), self.head) + margin
        cells = [self.tape.get(i, 0) for i in range(lo, hi + 1)]
        return cells, self.head - lo

    def tape_as_binary(self) -> str:
        """Read tape as a binary number (head at LSB, reading rightward)."""
        if not self.tape:
            return "0"
        lo = min(self.tape.keys())
        hi = max(self.tape.keys())
        bits = [self.tape.get(i, 0) for i in range(lo, hi + 1)]
        # Remove trailing zeros
        while bits and bits[-1] == 0:
            bits.pop()
        if not bits:
            return "0"
        return ''.join(str(b) for b in reversed(bits))

    def right_of_head(self, length: int = 32) -> list[int]:
        """Tape cells to the right of (and including) head position."""
        return [self.tape.get(self.head + i, 0) for i in range(length)]

    def left_of_head(self, length: int = 32) -> list[int]:
        """Tape cells to the left of head position (nearest first)."""
        return [self.tape.get(self.head - 1 - i, 0) for i in range(length)]

    def copy(self) -> TMConfig:
        return TMConfig(
            state=self.state,
            tape=dict(self.tape),
            head=self.head,
            step=self.step,
        )


class TuringMachine:
    """
    A deterministic Turing machine.

    transition_table: dict mapping (state, symbol) -> (new_state, write_symbol, direction)
    initial_state: starting state (default 0)
    halt_states: set of halting states
    """

    def __init__(
        self,
        transition_table: dict[tuple[int, int], tuple[int, int, str]],
        initial_state: int = 0,
        halt_states: Optional[set[int]] = None,
    ):
        self.table = transition_table
        self.initial_state = initial_state
        self.halt_states = halt_states or set()
        self.tape: dict[int, int] = {}
        self.state = initial_state
        self.head = 0
        self.step_count = 0
        self.halted = False
        self.trace: list[TMConfig] = []

    def load_tape(self, data: dict[int, int] | list[int], offset: int = 0):
        """Load data onto the tape. List is written starting at offset."""
        if isinstance(data, list):
            for i, v in enumerate(data):
                if v != 0:
                    self.tape[offset + i] = v
        else:
            self.tape.update(data)

    def load_binary(self, n: int, pos: int = 0):
        """Load a non-negative integer in binary onto the tape (LSB at pos)."""
        i = pos
        while n > 0:
            self.tape[i] = n & 1
            n >>= 1
            i += 1

    def current_symbol(self) -> int:
        return self.tape.get(self.head, 0)

    def snapshot(self) -> TMConfig:
        return TMConfig(
            state=self.state,
            tape=dict(self.tape),
            head=self.head,
            step=self.step_count,
        )

    def step(self) -> bool:
        """Execute one step. Returns False if halted."""
        if self.halted:
            return False

        self.trace.append(self.snapshot())
        sym = self.current_symbol()
        key = (self.state, sym)

        if key not in self.table or self.state in self.halt_states:
            self.halted = True
            return False

        new_state, write_sym, direction = self.table[key]
        self.tape[self.head] = write_sym
        self.state = new_state

        if direction == L:
            self.head -= 1
        elif direction == R:
            self.head += 1
        # S = stay

        self.step_count += 1
        return True

    def run(self, max_steps: int = 1000) -> list[TMConfig]:
        """Run until halt or max_steps. Returns trace including final config."""
        while self.step_count < max_steps:
            if not self.step():
                break
        self.trace.append(self.snapshot())
        return self.trace


# ─── Built-in Machines ────────────────────────────────────────────────


def binary_incrementer() -> TuringMachine:
    """
    2-state, 2-symbol binary incrementer.
    
    Tape holds a binary number (LSB at position 0, growing rightward).
    Head starts at position 0 (LSB).
    
    States: 0 = carry, 1 = halt
    Symbols: 0, 1
    
    Transition table:
        (0, 0) → (1, 1, S)   — write 1, halt (no carry)
        (0, 1) → (0, 0, R)   — write 0, carry right (move to next bit)
    
    This is binary addition of 1. The carry propagation is EXACTLY
    what happens in 2-adic addition: n → n + 1 in ℤ₂.
    """
    table = {
        (0, 0): (1, 1, S),  # 0 bit: flip to 1, done
        (0, 1): (0, 0, R),  # 1 bit: flip to 0, carry to next
    }
    return TuringMachine(table, initial_state=0, halt_states={1})


def busy_beaver_3state() -> TuringMachine:
    """
    3-state, 2-symbol busy beaver (BB-3).
    
    The classic BB(3) champion: writes 6 ones and halts in 14 steps.
    
    States: 0=A, 1=B, 2=C, 3=HALT
    Symbols: 0, 1
    
    Transition table (Marxen & Buntrock):
        (A, 0) → (B, 1, R)
        (A, 1) → (C, 1, L)
        (B, 0) → (A, 1, L)
        (B, 1) → (B, 1, R)
        (C, 0) → (B, 1, L)
        (C, 1) → (HALT, 1, S)
    """
    A, B, C, HALT = 0, 1, 2, 3
    table = {
        (A, 0): (B, 1, R),
        (A, 1): (C, 1, L),
        (B, 0): (A, 1, L),
        (B, 1): (B, 1, R),
        (C, 0): (B, 1, L),
        (C, 1): (HALT, 1, S),
    }
    return TuringMachine(table, initial_state=A, halt_states={HALT})
