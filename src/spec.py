"""Schema definitions and validation for machines and inputs.

Adapted from Emmett Shear's mobiusmachine package.
Uses Pydantic for validation, JSON for serialization.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class Transition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: str
    read: int = Field(ge=0)
    write: int = Field(ge=0)
    move: Literal["L", "R"]
    next_state: str

    @property
    def case_id(self) -> str:
        return f"{self.state}:{self.read}"


class MachineSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alphabet_size: int = Field(ge=2)
    blank_symbol: int = Field(default=0, ge=0)
    states: list[str] = Field(min_length=1)
    start_state: str
    halt_states: list[str] = Field(default_factory=list)
    transitions: list[Transition] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_machine(self) -> "MachineSpec":
        if self.blank_symbol >= self.alphabet_size:
            raise ValueError("blank_symbol must be < alphabet_size")

        if len(set(self.states)) != len(self.states):
            raise ValueError("states must be unique")

        state_set = set(self.states)
        if self.start_state not in state_set:
            raise ValueError("start_state must be listed in states")

        unknown_halts = [s for s in self.halt_states if s not in state_set]
        if unknown_halts:
            raise ValueError(f"halt_states not in states: {unknown_halts}")

        seen: set[tuple[str, int]] = set()
        for transition in self.transitions:
            if transition.state not in state_set:
                raise ValueError(f"transition state not in states: {transition.state}")
            if transition.next_state not in state_set:
                raise ValueError(f"transition next_state not in states: {transition.next_state}")
            if transition.read >= self.alphabet_size:
                raise ValueError(f"read symbol out of range for {transition.case_id}")
            if transition.write >= self.alphabet_size:
                raise ValueError(f"write symbol out of range for {transition.case_id}")
            key = (transition.state, transition.read)
            if key in seen:
                raise ValueError(f"duplicate transition case: {key}")
            seen.add(key)

        return self

    def internal_symbol(self, external_symbol: int) -> int:
        """Convert external symbol (0-based) to internal (1-based for CF)."""
        return external_symbol + 1

    def external_symbol(self, internal_symbol: int) -> int:
        """Convert internal symbol (1-based) back to external (0-based)."""
        return internal_symbol - 1

    @property
    def transition_map(self) -> dict[tuple[str, int], Transition]:
        return {(t.state, t.read): t for t in self.transitions}


class InputSpec(BaseModel):
    """Input with either two-stack form or flat tape/head form."""

    model_config = ConfigDict(extra="forbid")

    tape: list[int] | None = None
    head: int = Field(default=0, ge=0)
    left: list[int] | None = None
    right: list[int] | None = None
    state: str | None = None

    @model_validator(mode="after")
    def _validate_input(self) -> "InputSpec":
        has_two_stack = self.left is not None or self.right is not None
        has_flat = self.tape is not None

        if has_two_stack and has_flat:
            raise ValueError("provide either tape/head or left/right, not both")

        if not has_two_stack and not has_flat:
            self.tape = []

        return self

    def to_external_stacks(self) -> tuple[list[int], list[int]]:
        if self.left is not None or self.right is not None:
            return list(self.left or []), list(self.right or [])

        tape = list(self.tape or [])
        head = self.head
        if head < 0:
            raise ValueError("head must be >= 0")

        if head > len(tape):
            tape = tape + [0] * (head - len(tape))

        right = tape[head:] if head < len(tape) else []
        left = list(reversed(tape[:head]))
        return left, right


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_machine(path: str | Path) -> MachineSpec:
    data = _load_json(path)
    try:
        return MachineSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


def load_input(path: str | Path) -> InputSpec:
    data = _load_json(path)
    try:
        return InputSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
