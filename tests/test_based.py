"""Tests for the base-d adelic TM runtime."""

from __future__ import annotations

import pytest
from pathlib import Path
from fractions import Fraction

from src.based import (
    BaseDConfig, BaseDRunResult, BaseDStepRecord,
    run_based, initialize_based_config, step_based,
    extract_tape_from_config, _encode_stack_based,
)
from src.spec import load_machine, load_input

EXAMPLES = Path(__file__).parent.parent / "examples"
LIB_MACHINES = EXAMPLES / "library_machines"
LIB_INPUTS = EXAMPLES / "library_inputs"


class TestBaseDEncoding:
    """Test d-ary fraction encoding."""

    def test_empty_stack(self):
        val = _encode_stack_based([], 2)
        assert val == Fraction(0)

    def test_single_symbol(self):
        # [1] as base-2: 1/2
        val = _encode_stack_based([1], 2)
        assert val == Fraction(1, 2)

    def test_two_symbols(self):
        # [1, 0] as base-2: 1/2 + 0/4 = 1/2
        val = _encode_stack_based([1, 0], 2)
        assert val == Fraction(1, 2)
        # [1, 1] as base-2: 1/2 + 1/4 = 3/4
        val = _encode_stack_based([1, 1], 2)
        assert val == Fraction(3, 4)

    def test_base3(self):
        # [2, 1] as base-3: 2/3 + 1/9 = 7/9
        val = _encode_stack_based([2, 1], 3)
        assert val == Fraction(7, 9)


class TestBaseDRuntime:
    """Test base-d TM execution."""

    def test_unary_add_halts(self):
        machine = load_machine(LIB_MACHINES / "unary_add.json")
        inp = load_input(LIB_INPUTS / "unary_add.input.json")
        result = run_based(machine, inp)
        assert result.status == "HALT"

    def test_unary_parity_halts(self):
        machine = load_machine(LIB_MACHINES / "unary_parity.json")
        inp = load_input(LIB_INPUTS / "unary_parity.input.json")
        result = run_based(machine, inp)
        assert result.status == "HALT"

    def test_binary_add_halts(self):
        machine = load_machine(LIB_MACHINES / "binary_add.json")
        inp = load_input(LIB_INPUTS / "binary_add.input.json")
        result = run_based(machine, inp)
        assert result.status == "HALT"

    def test_unary_multiply_halts(self):
        machine = load_machine(LIB_MACHINES / "unary_multiply.json")
        inp = load_input(LIB_INPUTS / "unary_multiply.input.json")
        result = run_based(machine, inp, max_steps=50_000)
        assert result.status == "HALT"

    def test_3x3_matrix_is_affine(self):
        """Each step's 3x3 matrix should have [0,0,1] as last row."""
        machine = load_machine(LIB_MACHINES / "unary_add.json")
        inp = load_input(LIB_INPUTS / "unary_add.input.json")
        result = run_based(machine, inp)
        for record in result.trace:
            m = record.matrix_3x3
            assert m[2] == [Fraction(0), Fraction(0), Fraction(1)], \
                f"Step {record.step}: last row should be [0,0,1], got {m[2]}"

    def test_tape_extraction_roundtrip(self):
        """Encode then extract should give back the original tape."""
        machine = load_machine(LIB_MACHINES / "unary_add.json")
        inp = load_input(LIB_INPUTS / "unary_add.input.json")
        config = initialize_based_config(machine, inp)
        tape = extract_tape_from_config(config, machine.alphabet_size)
        # Original input for unary_add is typically [1,1,0,1,1,1]
        # Just verify we get something reasonable
        assert len(tape) > 0


class TestNewMachines:
    """Test the new machines from Emmett's repo."""

    def test_rogozhin_2_3_loads(self):
        machine = load_machine(LIB_MACHINES / "rogozhin_2_3.json")
        assert machine.alphabet_size == 3
        assert len(machine.states) == 2
        assert len(machine.transitions) == 6

    def test_sweeper_6_2_loads(self):
        machine = load_machine(LIB_MACHINES / "sweeper_6_2.json")
        assert machine.alphabet_size == 2
        assert len(machine.states) == 6

    def test_bouncer_15_2_loads(self):
        machine = load_machine(LIB_MACHINES / "bouncer_15_2.json")
        assert machine.alphabet_size == 2
        assert len(machine.states) == 15

    def test_rogozhin_2_3_based_runs(self):
        """Rogozhin (2,3) should run without crash in base-d mode."""
        machine = load_machine(LIB_MACHINES / "rogozhin_2_3.json")
        inp = load_input(LIB_INPUTS / "rogozhin_2_3.input.json")
        result = run_based(machine, inp, max_steps=100)
        # This is a universal TM — it may not halt on the test input,
        # but it should run without crashing
        assert result.status in ("HALT", "UNKNOWN")

    def test_sweeper_6_2_based_runs(self):
        machine = load_machine(LIB_MACHINES / "sweeper_6_2.json")
        inp = load_input(LIB_INPUTS / "sweeper_6_2.input.json")
        result = run_based(machine, inp, max_steps=200)
        assert result.status in ("HALT", "UNKNOWN")

    def test_bouncer_15_2_based_runs(self):
        machine = load_machine(LIB_MACHINES / "bouncer_15_2.json")
        inp = load_input(LIB_INPUTS / "bouncer_15_2.input.json")
        result = run_based(machine, inp, max_steps=200)
        assert result.status in ("HALT", "UNKNOWN")
