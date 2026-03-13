"""Base-d adelic Turing machine runtime (§7 of the spec).

The tape is encoded as two d-ary fractions L, R ∈ ℚ≥0:
  R = t₀/d + t₁/d² + t₂/d³ + ...   (right half, including head)
  L = t₋₁/d + t₋₂/d² + ...          (left half)

Reading: a = floor(d·R), b = floor(d·L)
Each step applies a 3×3 rational matrix to the state vector (L, R, 1)ᵀ:

  Right move (read a, write w):
    L' = (L + w) / d           push w onto L
    R' = d·R - a               pop a from R

  Left move (read a, write w, left-read b):
    L' = d·L - b               pop b from L
    R' = (b·d + d·R - a + w) / d²   replace a with w, push b on top
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

from .errors import CrashError
from .spec import InputSpec, MachineSpec, Transition


RunStatus = Literal["HALT", "CRASH", "DIVERGE", "UNKNOWN"]


@dataclass
class BaseDConfig:
    """State of a base-d adelic TM: two d-ary fractions and a state label."""
    L: Fraction
    R: Fraction
    state: str
    step_index: int = 0


@dataclass
class BaseDStepRecord:
    step: int
    pre_state: str
    post_state: str
    read_symbol: int
    write_symbol: int
    move: str
    pre_L: Fraction
    pre_R: Fraction
    post_L: Fraction
    post_R: Fraction
    matrix_3x3: list[list[Fraction]]


@dataclass
class BaseDRunResult:
    status: RunStatus
    steps: int
    final_config: BaseDConfig
    trace: list[BaseDStepRecord]
    crash_reason: str | None = None


def _encode_stack_based(symbols: list[int], d: int) -> Fraction:
    """Encode a symbol list [s₀, s₁, ...] as s₀/d + s₁/d² + s₂/d³ + ..."""
    value = Fraction(0)
    for i, s in enumerate(symbols):
        value += Fraction(s, d ** (i + 1))
    return value


def initialize_based_config(machine: MachineSpec, input_spec: InputSpec) -> BaseDConfig:
    """Initialize a base-d config from a machine and input spec."""
    d = machine.alphabet_size
    left_external, right_external = input_spec.to_external_stacks()

    for symbol in left_external + right_external:
        if symbol < 0 or symbol >= d:
            raise ValueError(f"input symbol out of bounds: {symbol}")

    L = _encode_stack_based(left_external, d)
    R = _encode_stack_based(right_external, d)

    state = input_spec.state or machine.start_state
    if state not in set(machine.states):
        raise ValueError(f"input state is not in machine states: {state}")

    return BaseDConfig(L=L, R=R, state=state, step_index=0)


def _read_top_digit(value: Fraction, d: int) -> int:
    """Read the top d-ary digit: floor(d * value).

    For a well-formed encoding, this is in [0, d-1].
    For the empty stack (value=0), returns 0 (blank).
    """
    scaled = d * value
    digit = int(scaled)
    # Handle negative fractions from rounding
    if scaled < 0:
        digit = int(scaled) - (1 if scaled != int(scaled) else 0)
    return digit


def _extract_tape_based(value: Fraction, d: int, max_symbols: int = 100) -> list[int]:
    """Extract up to max_symbols d-ary digits from a fraction."""
    symbols = []
    remaining = value
    for _ in range(max_symbols):
        digit = _read_top_digit(remaining, d)
        symbols.append(digit)
        remaining = d * remaining - digit
        if remaining == 0:
            break
    # Trim trailing zeros (blanks)
    while symbols and symbols[-1] == 0:
        symbols.pop()
    return symbols


def step_based(machine: MachineSpec, config: BaseDConfig) -> BaseDStepRecord:
    """Execute one step of the base-d adelic TM."""
    d = machine.alphabet_size
    d_frac = Fraction(d)
    pre_L = config.L
    pre_R = config.R

    # Read current symbol (top of right stack)
    a = _read_top_digit(config.R, d)
    if a < 0 or a >= d:
        raise CrashError(f"read symbol out of range: {a}")

    # Look up transition
    transition = machine.transition_map.get((config.state, a))
    if transition is None:
        raise CrashError(f"undefined transition for state={config.state}, read={a}")

    w = transition.write

    if transition.move == "R":
        # Right move: push w onto L, pop a from R
        # L' = (L + w) / d
        # R' = d·R - a
        new_L = (config.L + Fraction(w)) / d_frac
        new_R = d_frac * config.R - Fraction(a)

        # Build the 3x3 matrix: [[1/d, 0, w/d], [0, d, -a], [0, 0, 1]]
        matrix = [
            [Fraction(1, d), Fraction(0), Fraction(w, d)],
            [Fraction(0), Fraction(d), Fraction(-a)],
            [Fraction(0), Fraction(0), Fraction(1)],
        ]
    else:
        # Left move:
        # Read b from top of left stack
        b = _read_top_digit(config.L, d)

        # L' = d·L - b
        # R' = (b·d + d·R - a + w) / d²
        new_L = d_frac * config.L - Fraction(b)
        new_R = (Fraction(b * d) + d_frac * config.R - Fraction(a) + Fraction(w)) / (d_frac * d_frac)

        # The 3x3 matrix for left move:
        # [[d, 0, -b], [0, 1/d, (b·d - a + w)/d²], [0, 0, 1]]
        # Wait, let me verify: M·(L, R, 1)ᵀ should give (new_L, new_R, 1)
        # new_L = d·L + 0·R + (-b)·1  ✓
        # new_R = 0·L + (1/d)·R + ? where ? = (b·d - a + w)/d²
        #       = R/d + (b·d - a + w)/d²
        # But we want: (b·d + d·R - a + w) / d² = b/d + R/d + (w - a)/d²
        #            = R/d + b/d + (w-a)/d²
        # So the constant term is b/d + (w-a)/d² = (b·d + w - a) / d²  ✓
        matrix = [
            [Fraction(d), Fraction(0), Fraction(-b)],
            [Fraction(0), Fraction(1, d), Fraction(b * d + w - a, d * d)],
            [Fraction(0), Fraction(0), Fraction(1)],
        ]

    config.L = new_L
    config.R = new_R
    config.state = transition.next_state
    config.step_index += 1

    return BaseDStepRecord(
        step=config.step_index - 1,
        pre_state=transition.state,
        post_state=transition.next_state,
        read_symbol=a,
        write_symbol=w,
        move=transition.move,
        pre_L=pre_L,
        pre_R=pre_R,
        post_L=new_L,
        post_R=new_R,
        matrix_3x3=matrix,
    )


def run_based(
    machine: MachineSpec,
    input_spec: InputSpec,
    max_steps: int = 10_000,
) -> BaseDRunResult:
    """Run a base-d adelic TM to completion or step limit."""
    config = initialize_based_config(machine, input_spec)
    trace: list[BaseDStepRecord] = []
    halt_states = set(machine.halt_states)

    if config.state in halt_states:
        return BaseDRunResult(status="HALT", steps=0, final_config=config, trace=trace)

    for _ in range(max_steps):
        try:
            record = step_based(machine, config)
        except CrashError as exc:
            return BaseDRunResult(
                status="CRASH",
                steps=len(trace),
                final_config=config,
                trace=trace,
                crash_reason=str(exc),
            )
        trace.append(record)

        if config.state in halt_states:
            return BaseDRunResult(
                status="HALT", steps=len(trace), final_config=config, trace=trace
            )

    return BaseDRunResult(
        status="UNKNOWN", steps=len(trace), final_config=config, trace=trace
    )


def extract_tape_from_config(config: BaseDConfig, d: int) -> list[int]:
    """Reconstruct the flat tape from a base-d config."""
    left_symbols = _extract_tape_based(config.L, d)
    right_symbols = _extract_tape_based(config.R, d)
    return list(reversed(left_symbols)) + right_symbols
