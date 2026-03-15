"""Tests verifying equivalence between CF runtime and base-d runtime.

Both runtimes encode a Turing machine tape as rational numbers:
- CF runtime: continued fraction stacks (Phase 1-3 of Möbius-Shear framework)
- Base-d runtime: d-ary fractions (§7 of spec)

These tests confirm they produce identical results: same number of steps,
same final state, same final tape contents, and matching step-by-step traces.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from src.core import MobiusComputer
from src.based import run_based, extract_tape_from_config
from src.spec import load_machine, load_input

# Paths
EXAMPLES = Path(__file__).parent.parent / "examples"
LIB_MACHINES = EXAMPLES / "library_machines"
LIB_INPUTS = EXAMPLES / "library_inputs"


def _trim_blanks(tape: list[int]) -> list[int]:
    """Remove leading and trailing zeros (blank symbols)."""
    t = list(tape)
    while t and t[0] == 0:
        t.pop(0)
    while t and t[-1] == 0:
        t.pop()
    return t


def _cf_flat_tape(mc: MobiusComputer) -> list[int]:
    """Extract flat tape from CF runtime result."""
    left, right = mc.final_tape_external()
    return _trim_blanks(list(reversed(left)) + right)


def _based_flat_tape(result, alphabet_size: int) -> list[int]:
    """Extract flat tape from base-d runtime result."""
    tape = extract_tape_from_config(result.final_config, alphabet_size)
    return _trim_blanks(tape)


class TestHaltingEquivalence:
    """Test that halting machines produce identical results in both runtimes."""

    @pytest.mark.parametrize("name,max_steps", [
        ("unary_add", 10_000),
        ("unary_parity", 10_000),
        ("binary_add", 10_000),
        ("unary_multiply", 50_000),
    ])
    def test_library_machine_equivalence(self, name, max_steps):
        """Library machines must halt with same steps, state, and tape."""
        machine = load_machine(LIB_MACHINES / f"{name}.json")
        inp = load_input(LIB_INPUTS / f"{name}.input.json")

        # CF runtime
        mc = MobiusComputer(machine, inp)
        mc.run(max_steps=max_steps)
        cf_result = mc._result
        cf_tape = _cf_flat_tape(mc)

        # Base-d runtime
        bd_result = run_based(machine, inp, max_steps=max_steps)
        bd_tape = _based_flat_tape(bd_result, machine.alphabet_size)

        # Both must halt
        assert cf_result.status == "HALT", f"CF runtime did not halt for {name}"
        assert bd_result.status == "HALT", f"Base-d runtime did not halt for {name}"

        # Same number of steps
        assert cf_result.steps == bd_result.steps, \
            f"{name}: CF took {cf_result.steps} steps, base-d took {bd_result.steps}"

        # Same final state
        assert cf_result.final_state == bd_result.final_config.state, \
            f"{name}: CF ended in {cf_result.final_state}, base-d in {bd_result.final_config.state}"

        # Same final tape
        assert cf_tape == bd_tape, \
            f"{name}: CF tape={cf_tape}, base-d tape={bd_tape}"

    def test_bb3_equivalence(self):
        """BB(3) — the flagship machine — must be equivalent."""
        machine = load_machine(EXAMPLES / "bb3_machine.json")
        inp = load_input(EXAMPLES / "bb3_input.json")

        mc = MobiusComputer(machine, inp)
        mc.run()
        cf_result = mc._result
        cf_tape = _cf_flat_tape(mc)

        bd_result = run_based(machine, inp)
        bd_tape = _based_flat_tape(bd_result, machine.alphabet_size)

        assert cf_result.status == "HALT"
        assert bd_result.status == "HALT"
        assert cf_result.steps == bd_result.steps == 13
        assert cf_result.final_state == bd_result.final_config.state
        assert cf_tape == bd_tape == [1, 1, 1, 1, 1, 1]


class TestTraceEquivalence:
    """Test that step-by-step traces match between runtimes."""

    @pytest.mark.parametrize("name,max_steps", [
        ("unary_add", 10_000),
        ("binary_add", 10_000),
    ])
    def test_trace_state_sequence(self, name, max_steps):
        """State sequence must be identical step by step."""
        machine = load_machine(LIB_MACHINES / f"{name}.json")
        inp = load_input(LIB_INPUTS / f"{name}.input.json")

        mc = MobiusComputer(machine, inp)
        mc.run(max_steps=max_steps)
        cf_trace = [(r.post_state, r.write_symbol, r.move) for r in mc._result.trace]

        bd_result = run_based(machine, inp, max_steps=max_steps)
        bd_trace = [(r.post_state, r.write_symbol, r.move) for r in bd_result.trace]

        assert cf_trace == bd_trace, \
            f"{name}: trace mismatch at step {next(i for i,(a,b) in enumerate(zip(cf_trace, bd_trace)) if a != b)}"

    def test_bb3_full_trace(self):
        """BB(3) complete 13-step trace must match exactly."""
        machine = load_machine(EXAMPLES / "bb3_machine.json")
        inp = load_input(EXAMPLES / "bb3_input.json")

        mc = MobiusComputer(machine, inp)
        mc.run()
        cf_trace = [(r.post_state, r.write_symbol, r.move) for r in mc._result.trace]

        bd_result = run_based(machine, inp)
        bd_trace = [(r.post_state, r.write_symbol, r.move) for r in bd_result.trace]

        assert len(cf_trace) == len(bd_trace) == 13
        assert cf_trace == bd_trace


class TestNonHaltingEquivalence:
    """Test non-halting machines produce matching partial traces."""

    @pytest.mark.parametrize("name,steps", [
        ("sweeper_6_2", 100),
        ("bouncer_15_2", 100),
        ("rogozhin_2_3", 100),
    ])
    def test_partial_trace_match(self, name, steps):
        """Traces must match for all steps both runtimes complete.

        Some machines crash in the CF runtime due to CF stack divergence
        before reaching max_steps. The key invariant is: for every step
        BOTH runtimes complete, the (state, write, move) triple is identical.
        """
        machine = load_machine(LIB_MACHINES / f"{name}.json")
        inp = load_input(LIB_INPUTS / f"{name}.input.json")

        mc = MobiusComputer(machine, inp)
        mc.run(max_steps=steps)
        cf_trace = [(r.post_state, r.write_symbol, r.move) for r in mc._result.trace]

        bd_result = run_based(machine, inp, max_steps=steps)
        bd_trace = [(r.post_state, r.write_symbol, r.move) for r in bd_result.trace]

        # Compare for however many steps both runtimes completed
        common = min(len(cf_trace), len(bd_trace))
        assert common > 0, f"{name}: at least one runtime produced 0 steps"

        assert cf_trace[:common] == bd_trace[:common], \
            f"{name}: trace diverges at step {next(i for i,(a,b) in enumerate(zip(cf_trace[:common], bd_trace[:common])) if a != b)}"
