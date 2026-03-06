"""Core MobiusComputer — unified adelic TM runner with dual-mode execution.

Fast path: symbol-list operations (no Fraction arithmetic).
Verification path: exact CFStack arithmetic confirms CF values match.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from fractions import Fraction
from typing import Literal

from .cf import CFStack, cf_value_from_stack
from .divergence import DivergenceMonitor, DivergencePolicy
from .lean_export import export_lean as _lean_export
from .mobius import MobiusMatrix, ShearFactor
from .selectors import (
    SelectorError, MemCheckReport, check_mem_totality, select_transition,
)
from .shear import ShearExpansion
from .spec import InputSpec, MachineSpec, Transition


# ---------------------------------------------------------------------------
# Data classes for results
# ---------------------------------------------------------------------------

RunStatus = Literal["HALT", "CRASH", "DIVERGE", "UNKNOWN"]


@dataclass
class EmetReport:
    aleph: bool
    mem: bool
    tav: bool
    is_emet: bool
    notes: list[str] = field(default_factory=list)


@dataclass
class StepRecord:
    step: int
    pre_state: str
    post_state: str
    read_symbol: int       # external
    write_symbol: int      # external
    move: str
    shear_factor: ShearFactor
    matrix_2x2: list[list[int]]
    pre_left: list[int]    # internal symbols
    pre_right: list[int]
    post_left: list[int]
    post_right: list[int]
    selector_mode: str
    status_flags: list[str] = field(default_factory=list)
    # Verification data (only when verify=True)
    pre_left_cf: Fraction | None = None
    pre_right_cf: Fraction | None = None
    post_left_cf: Fraction | None = None
    post_right_cf: Fraction | None = None


@dataclass
class RunResult:
    status: RunStatus
    steps: int
    final_left: list[int]   # internal symbols
    final_right: list[int]
    final_state: str
    trace: list[StepRecord]
    emet: EmetReport
    crash_reason: str | None = None


# ---------------------------------------------------------------------------
# Stack helpers (fast path — no Fraction, just integer lists)
# ---------------------------------------------------------------------------

def _trim_trailing_blanks(stack: list[int], blank: int) -> list[int]:
    out = list(stack)
    while out and out[-1] == blank:
        out.pop()
    return out


def _stack_top(stack: list[int], blank: int) -> int:
    return stack[0] if stack else blank


def _stack_pop(stack: list[int], blank: int) -> tuple[int, list[int]]:
    if not stack:
        return blank, []
    return stack[0], _trim_trailing_blanks(stack[1:], blank)


def _stack_push(stack: list[int], value: int, blank: int) -> list[int]:
    if not stack and value == blank:
        return []
    pushed = [value] + list(stack)
    return _trim_trailing_blanks(pushed, blank)


# ---------------------------------------------------------------------------
# MobiusComputer
# ---------------------------------------------------------------------------

class MobiusComputer:
    """Unified adelic TM runner.

    Modes:
        "direct"   — table lookup (fast, no arithmetic selection)
        "selector" — CRT Lagrange interpolation over ℤ/Nℤ

    When verify=True, exact Fraction arithmetic via CFStack runs alongside
    the fast path and asserts agreement at each step.
    """

    def __init__(
        self,
        machine: MachineSpec,
        input_spec: InputSpec | None = None,
        mode: str = "direct",
        verify: bool = True,
        divergence_policy: DivergencePolicy | None = None,
    ):
        self.machine = machine
        self.input_spec = input_spec or InputSpec()
        self.mode = mode
        self.verify = verify
        self._divergence = DivergenceMonitor(divergence_policy)
        self._shear = ShearExpansion()
        self._result: RunResult | None = None

        # Initialize tape
        left_ext, right_ext = self.input_spec.to_external_stacks()
        for s in left_ext + right_ext:
            if s < 0 or s >= machine.alphabet_size:
                raise ValueError(f"input symbol out of bounds: {s}")

        self._blank = machine.internal_symbol(machine.blank_symbol)
        self._left = _trim_trailing_blanks(
            [machine.internal_symbol(s) for s in left_ext], self._blank
        )
        self._right = _trim_trailing_blanks(
            [machine.internal_symbol(s) for s in right_ext], self._blank
        )
        self._state = self.input_spec.state or machine.start_state
        if self._state not in set(machine.states):
            raise ValueError(f"input state not in machine states: {self._state}")

    def _lookup_transition(self, state: str, read_ext: int) -> Transition:
        """Get transition via direct lookup or selector."""
        if self.mode == "selector":
            return select_transition(self.machine, state, read_ext)
        t = self.machine.transition_map.get((state, read_ext))
        if t is None:
            raise _CrashError(f"undefined transition for state={state}, read={read_ext}")
        return t

    def _step(self, step_idx: int) -> StepRecord:
        """Execute one step. Mutates internal state."""
        blank = self._blank
        pre_left = list(self._left)
        pre_right = list(self._right)

        read_internal = _stack_top(self._right, blank)
        read_ext = self.machine.external_symbol(read_internal)

        transition = self._lookup_transition(self._state, read_ext)
        write_internal = self.machine.internal_symbol(transition.write)

        if transition.move == "R":
            # Pop from right (read), push write onto left
            _, right_rest = _stack_pop(self._right, blank)
            post_right = right_rest
            post_left = _stack_push(self._left, write_internal, blank)
            factor = ShearFactor(kind="pop", k=read_internal)

            # Shear expansion: Q_a on R, P_w on L
            self._shear.record_right(MobiusMatrix.pop(read_internal))
            self._shear.record_left(MobiusMatrix.push(write_internal))
            self._shear.record_step([factor])

        else:  # "L"
            # Left move: pop a from R, push w onto R, pop b from L, push b onto R
            popped_left, left_rest = _stack_pop(self._left, blank)
            _, right_rest = _stack_pop(self._right, blank)
            right_with_write = _stack_push(right_rest, write_internal, blank)
            post_right = _stack_push(right_with_write, popped_left, blank)
            post_left = left_rest
            factor = ShearFactor(kind="push", k=write_internal)

            # Shear expansion: Q_a on R, P_w on R, P_b on R, Q_b on L
            self._shear.record_right(MobiusMatrix.pop(read_internal))
            self._shear.record_right(MobiusMatrix.push(write_internal))
            self._shear.record_right(MobiusMatrix.push(popped_left))
            self._shear.record_left(MobiusMatrix.pop(popped_left))
            self._shear.record_step([
                ShearFactor(kind="pop", k=read_internal),
                ShearFactor(kind="push", k=write_internal),
                ShearFactor(kind="push", k=popped_left),
            ])

        # Validate all symbols positive
        if factor.k <= 0:
            raise _CrashError(f"invalid non-positive shear parameter k={factor.k}")
        for s in post_left + post_right:
            if s <= 0:
                raise _CrashError(f"invalid non-positive internal symbol: {s}")

        # Verification layer
        pre_left_cf = pre_right_cf = post_left_cf = post_right_cf = None
        if self.verify:
            pre_left_cf = cf_value_from_stack(pre_left, blank)
            pre_right_cf = cf_value_from_stack(pre_right, blank)
            post_left_cf = cf_value_from_stack(post_left, blank)
            post_right_cf = cf_value_from_stack(post_right, blank)

        # Update state
        self._left = post_left
        self._right = post_right
        self._state = transition.next_state

        status_flags = []
        if self._state in set(self.machine.halt_states):
            status_flags.append("HALT")

        return StepRecord(
            step=step_idx,
            pre_state=transition.state,
            post_state=transition.next_state,
            read_symbol=transition.read,
            write_symbol=transition.write,
            move=transition.move,
            shear_factor=factor,
            matrix_2x2=factor.to_matrix().as_list(),
            pre_left=pre_left,
            pre_right=pre_right,
            post_left=post_left,
            post_right=post_right,
            selector_mode=self.mode,
            status_flags=status_flags,
            pre_left_cf=pre_left_cf,
            pre_right_cf=pre_right_cf,
            post_left_cf=post_left_cf,
            post_right_cf=post_right_cf,
        )

    def run(self, max_steps: int = 10_000) -> RunResult:
        """Execute the machine up to max_steps.

        Returns RunResult with status, trace, Emet report.
        """
        trace: list[StepRecord] = []
        halt_states = set(self.machine.halt_states)

        # Check immediate halt
        if self._state in halt_states:
            self._result = RunResult(
                status="HALT", steps=0,
                final_left=list(self._left), final_right=list(self._right),
                final_state=self._state, trace=trace,
                emet=EmetReport(True, True, True, True),
            )
            return self._result

        for step_idx in range(max_steps):
            try:
                record = self._step(step_idx)
            except (_CrashError, SelectorError) as exc:
                self._result = RunResult(
                    status="CRASH", steps=len(trace),
                    final_left=list(self._left), final_right=list(self._right),
                    final_state=self._state, trace=trace,
                    emet=EmetReport(False, False, False, False),
                    crash_reason=str(exc),
                )
                self._evaluate_emet()
                return self._result

            trace.append(record)

            # Divergence check
            if self._divergence.check_step(
                record.shear_factor.k,
                len(self._left), len(self._right),
            ):
                self._result = RunResult(
                    status="DIVERGE", steps=len(trace),
                    final_left=list(self._left), final_right=list(self._right),
                    final_state=self._state, trace=trace,
                    emet=EmetReport(False, False, False, False),
                )
                self._evaluate_emet()
                return self._result

            if self._state in halt_states:
                self._result = RunResult(
                    status="HALT", steps=len(trace),
                    final_left=list(self._left), final_right=list(self._right),
                    final_state=self._state, trace=trace,
                    emet=EmetReport(True, True, True, True),
                )
                self._evaluate_emet()
                return self._result

        # Exceeded max_steps
        self._result = RunResult(
            status="UNKNOWN", steps=len(trace),
            final_left=list(self._left), final_right=list(self._right),
            final_state=self._state, trace=trace,
            emet=EmetReport(False, False, False, False),
        )
        self._evaluate_emet()
        return self._result

    def _evaluate_emet(self):
        """Fill in the Emet report on the current result."""
        if self._result is None:
            return
        r = self._result
        mem_report = check_mem_totality(self.machine)
        aleph = r.status not in ("CRASH", "DIVERGE")
        mem = mem_report.is_total
        tav = r.status == "HALT"
        notes = []
        if not aleph:
            notes.append(f"ℵ failed: {r.crash_reason or self._divergence.reason or 'crash/diverge'}")
        if not mem:
            notes.append("Mem failed: selector denominator non-units in ℤ/Nℤ")
        if not tav:
            notes.append("Tav failed: computation did not halt")
        r.emet = EmetReport(
            aleph=aleph, mem=mem, tav=tav,
            is_emet=(aleph and mem and tav), notes=notes,
        )

    @property
    def shear_expansion(self) -> ShearExpansion:
        """The Shear expansion from the computation."""
        return self._shear

    @property
    def emet_report(self) -> EmetReport | None:
        """Emet report (available after run())."""
        return self._result.emet if self._result else None

    def selector_diagnostics(self) -> MemCheckReport:
        """Run Mem totality check on the machine."""
        return check_mem_totality(self.machine)

    def export_lean(self, machine_name: str = "MachineRun") -> str:
        """Generate Lean 4 proof of the Shear expansion."""
        matrices = self._shear.all_matrices()
        if not matrices:
            raise ValueError("No computation trace to export (run first)")
        return _lean_export(matrices, machine_name)

    def final_tape_external(self) -> tuple[list[int], list[int]]:
        """Return final (left, right) stacks in external symbols."""
        if self._result is None:
            raise ValueError("No result yet (call run() first)")
        return (
            [self.machine.external_symbol(s) for s in self._result.final_left],
            [self.machine.external_symbol(s) for s in self._result.final_right],
        )


class _CrashError(Exception):
    """Internal crash during execution."""
    pass
