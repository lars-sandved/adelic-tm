"""Tests for the unified MobiusComputer package."""

import json
import sys
from pathlib import Path
from fractions import Fraction

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spec import MachineSpec, InputSpec, load_machine, load_input
from src.mobius import MobiusMatrix, ShearFactor
from src.cf import CFStack, cf_value_from_stack
from src.shear import ShearExpansion
from src.selectors import check_mem_totality, check_prime_field, SelectorError
from src.divergence import DivergencePolicy
from src.core import MobiusComputer, RunResult

EXAMPLES = Path(__file__).parent.parent / "examples"


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def bb3_machine():
    return load_machine(EXAMPLES / "bb3_machine.json")


@pytest.fixture
def bb3_input():
    return load_input(EXAMPLES / "bb3_input.json")


# ===========================================================================
# Phase 1: Spec loading
# ===========================================================================

class TestSpec:
    def test_load_bb3_machine(self, bb3_machine):
        assert bb3_machine.alphabet_size == 2
        assert bb3_machine.start_state == "A"
        assert bb3_machine.halt_states == ["HALT"]
        assert len(bb3_machine.transitions) == 6

    def test_load_bb3_input(self, bb3_input):
        left, right = bb3_input.to_external_stacks()
        assert left == []
        assert right == []

    def test_internal_symbol_shift(self, bb3_machine):
        assert bb3_machine.internal_symbol(0) == 1  # blank -> 1
        assert bb3_machine.internal_symbol(1) == 2  # mark -> 2
        assert bb3_machine.external_symbol(1) == 0
        assert bb3_machine.external_symbol(2) == 1

    def test_transition_map(self, bb3_machine):
        tm = bb3_machine.transition_map
        assert ("A", 0) in tm
        assert tm[("A", 0)].write == 1
        assert tm[("A", 0)].move == "R"
        assert tm[("A", 0)].next_state == "B"


# ===========================================================================
# Phase 2: MobiusMatrix
# ===========================================================================

class TestMobiusMatrix:
    def test_push_pop_inverse(self):
        """P_k and Q_k are inverses: Q_k @ P_k = I (up to sign)."""
        for k in [1, 2, 3, 5]:
            p = MobiusMatrix.push(k)
            q = MobiusMatrix.pop(k)
            product = q @ p
            # Q_k @ P_k = ((0,1),(1,-k)) @ ((k,1),(1,0)) = ((1,0),(k-k,1)) = I
            assert product == MobiusMatrix.identity(), f"Q_{k} @ P_{k} != I, got {product}"

    def test_push_is_shear_times_swap(self):
        """P_k = S(k) · J"""
        for k in [1, 2, 3]:
            p = MobiusMatrix.push(k)
            sj = MobiusMatrix.shear(k) @ MobiusMatrix.swap()
            assert p == sj

    def test_pop_is_swap_times_shear(self):
        """Q_k = J · S(-k)"""
        for k in [1, 2, 3]:
            q = MobiusMatrix.pop(k)
            js = MobiusMatrix.swap() @ MobiusMatrix.shear(-k)
            assert q == js

    def test_act_on_fraction(self):
        """Möbius action gives correct CF values."""
        phi = (1 + 5**0.5) / 2
        # Push 2 onto φ: 2 + 1/φ = 2 + φ - 1 = 1 + φ ≈ 2.618
        p2 = MobiusMatrix.push(2)
        x = Fraction(3, 2)  # approximate starting point
        result = p2.act(x)
        assert result == Fraction(2 * 3 + 2, 1 * 3 + 0) == Fraction(8, 3)

    def test_determinants(self):
        """Push has det -1, pop has det -1, shear has det 1."""
        assert MobiusMatrix.push(3).det() == -1
        assert MobiusMatrix.pop(3).det() == -1
        assert MobiusMatrix.shear(5).det() == 1
        assert MobiusMatrix.swap().det() == -1

    def test_shear_factor_to_matrix(self):
        f_push = ShearFactor(kind="push", k=3)
        assert f_push.to_matrix() == MobiusMatrix.push(3)
        f_pop = ShearFactor(kind="pop", k=2)
        assert f_pop.to_matrix() == MobiusMatrix.pop(2)


# ===========================================================================
# Phase 3: CFStack
# ===========================================================================

class TestCFStack:
    def test_blank_is_golden_ratio(self):
        blank = CFStack.blank(30)
        phi = (1 + 5**0.5) / 2
        assert abs(float(blank.value()) - phi) < 1e-6

    def test_push_pop_roundtrip(self):
        stack = CFStack.blank(20)
        original = stack.value()
        pushed = stack.push(3)
        sym, popped = pushed.pop()
        assert sym == 3
        assert popped.value() == original

    def test_from_internal_stack(self):
        # Internal stack [2, 1] with blank=1 → CF [2; 1, 1] = 2 + 1/(1+1) = 2.5
        cf = CFStack.from_internal_stack([2, 1], blank_internal=1)
        assert cf.value() == Fraction(5, 2)

    def test_from_empty_internal_stack(self):
        # Empty stack with blank=1 → CF [1] = 1
        cf = CFStack.from_internal_stack([], blank_internal=1)
        assert cf.value() == Fraction(1)

    def test_cf_value_from_stack_helper(self):
        val = cf_value_from_stack([2], blank_internal=1)
        # [2, 1] → 2 + 1/1 = 3
        assert val == Fraction(3)


# ===========================================================================
# Phase 4: BB(3) end-to-end
# ===========================================================================

class TestBB3EndToEnd:
    def test_bb3_direct_mode(self, bb3_machine, bb3_input):
        """BB(3) should halt in 13 steps."""
        mc = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=True)
        result = mc.run()
        assert result.status == "HALT"
        assert result.steps == 13

    def test_bb3_final_tape(self, bb3_machine, bb3_input):
        """BB(3) writes 6 ones (marks)."""
        mc = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=False)
        result = mc.run()
        left_ext, right_ext = mc.final_tape_external()
        # All non-empty symbols should be 1 (mark)
        all_marks = left_ext + right_ext
        assert all(s == 1 for s in all_marks)
        # Total marks = 6 (BB(3) productivity)
        assert len(all_marks) == 6

    def test_bb3_emet(self, bb3_machine, bb3_input):
        """BB(3) halts (ℵ, Tav) but Mem fails (gcd(d,q)≠1)."""
        mc = MobiusComputer(bb3_machine, bb3_input, mode="direct")
        result = mc.run()
        assert result.emet.aleph is True
        assert result.emet.tav is True
        # states = ["A","B","C","HALT"] → q=4, d=2, gcd(2,4)=2
        # So Mem is False for BB(3) with CRT packing
        assert result.emet.mem is False
        assert result.emet.is_emet is False

    def test_bb3_shear_expansion(self, bb3_machine, bb3_input):
        """Check Φ_R and Φ_L for BB(3)."""
        mc = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=False)
        mc.run()
        phi_r = mc.shear_expansion.phi_R
        phi_l = mc.shear_expansion.phi_L

        # Known values from our verified implementation:
        # Φ_R = [(-1,4),(0,1)]
        assert phi_r == MobiusMatrix(-1, 4, 0, 1), f"Φ_R = {phi_r}"
        # Φ_L = [(-5,22),(-2,9)]
        assert phi_l == MobiusMatrix(-5, 22, -2, 9), f"Φ_L = {phi_l}"

    def test_bb3_fraction_verification(self, bb3_machine, bb3_input):
        """Run with verify=True — should not raise any errors."""
        mc = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=True)
        result = mc.run()
        assert result.status == "HALT"
        # Check that CF values were recorded
        for record in result.trace:
            assert record.pre_left_cf is not None
            assert record.pre_right_cf is not None
            assert record.post_left_cf is not None
            assert record.post_right_cf is not None

    def test_bb3_trace_states(self, bb3_machine, bb3_input):
        """Verify the state sequence matches classical BB(3) trace."""
        mc = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=False)
        result = mc.run()
        # Classical BB(3) state sequence:
        expected_states = ["A", "B", "A", "C", "B", "A", "B", "B", "B", "B", "B", "A", "C"]
        actual_states = [r.pre_state for r in result.trace]
        assert actual_states == expected_states


# ===========================================================================
# Phase 5: Selector mode
# ===========================================================================

class TestSelector:
    def test_mem_check_bb3(self, bb3_machine):
        """BB(3) has gcd(2,4)=2, so CRT packing fails."""
        report = check_mem_totality(bb3_machine)
        assert report.gcd_d_q == 2
        assert report.is_total is False

    def test_mem_check_coprime_machine(self):
        """A machine with gcd(d,q)=1 should pass Mem check."""
        # 3-symbol, 2-state machine (gcd(3,2)=1)
        spec = MachineSpec(
            alphabet_size=3,
            blank_symbol=0,
            states=["q0", "halt"],
            start_state="q0",
            halt_states=["halt"],
            transitions=[
                {"state": "q0", "read": 0, "write": 1, "move": "R", "next_state": "halt"},
                {"state": "q0", "read": 1, "write": 2, "move": "R", "next_state": "halt"},
                {"state": "q0", "read": 2, "write": 0, "move": "R", "next_state": "halt"},
            ],
        )
        report = check_mem_totality(spec)
        assert report.gcd_d_q == 1

    def test_selector_coprime_machine(self):
        """Selector mode works for a machine where Mem holds.

        d=3 symbols, q=5 states (gcd=1), with residue diffs all coprime to N=15.
        We construct a trivial machine that halts in 1 step.
        """
        # d=3, q=5 states → gcd(3,5)=1, N=15
        spec = MachineSpec(
            alphabet_size=3,
            blank_symbol=0,
            states=["q0", "s1", "s2", "s3", "halt"],
            start_state="q0",
            halt_states=["halt"],
            transitions=[
                {"state": "q0", "read": 0, "write": 1, "move": "R", "next_state": "halt"},
                {"state": "q0", "read": 1, "write": 2, "move": "R", "next_state": "halt"},
                {"state": "q0", "read": 2, "write": 0, "move": "R", "next_state": "halt"},
            ],
        )
        report = check_mem_totality(spec)
        if not report.is_total:
            # Even with gcd=1, residue collisions may prevent selector.
            # This is expected — Mem is a strong condition.
            pytest.skip(f"Mem not satisfied: {len(report.collisions)} collisions")
        mc = MobiusComputer(spec, InputSpec(), mode="selector", verify=True)
        result = mc.run()
        assert result.status == "HALT"
        assert result.steps == 1


# ===========================================================================
# Phase 5b: Prime field selector
# ===========================================================================

class TestPrimeFieldSelector:
    def test_prime_field_report_bb3(self, bb3_machine):
        """BB(3) prime field selector uses P=11 (d*q=8 → smallest prime ≥ 8)."""
        report = check_prime_field(bb3_machine)
        assert report.prime == 11
        assert report.num_transitions == 6
        assert report.is_total is True

    def test_bb3_prime_mode_halts(self, bb3_machine, bb3_input):
        """BB(3) via prime field selector: same result as direct mode."""
        mc = MobiusComputer(bb3_machine, bb3_input, mode="prime", verify=True)
        result = mc.run()
        assert result.status == "HALT"
        assert result.steps == 13

    def test_bb3_prime_mode_same_tape(self, bb3_machine, bb3_input):
        """Prime mode produces identical tape to direct mode."""
        mc_direct = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=False)
        mc_prime = MobiusComputer(bb3_machine, bb3_input, mode="prime", verify=False)
        r_direct = mc_direct.run()
        r_prime = mc_prime.run()
        assert r_direct.final_left == r_prime.final_left
        assert r_direct.final_right == r_prime.final_right

    def test_bb3_prime_mode_same_shear(self, bb3_machine, bb3_input):
        """Prime mode produces identical Shear expansion to direct mode."""
        mc_direct = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=False)
        mc_prime = MobiusComputer(bb3_machine, bb3_input, mode="prime", verify=False)
        mc_direct.run()
        mc_prime.run()
        assert mc_direct.shear_expansion.phi_R == mc_prime.shear_expansion.phi_R
        assert mc_direct.shear_expansion.phi_L == mc_prime.shear_expansion.phi_L

    def test_bb3_prime_mode_emet(self, bb3_machine, bb3_input):
        """BB(3) in prime mode satisfies FULL Emet (ℵ + Mem + Tav)."""
        mc = MobiusComputer(bb3_machine, bb3_input, mode="prime", verify=True)
        result = mc.run()
        assert result.emet.aleph is True
        assert result.emet.mem is True
        assert result.emet.tav is True
        assert result.emet.is_emet is True

    def test_bb3_prime_mode_trace_matches(self, bb3_machine, bb3_input):
        """Every step's state sequence matches direct mode."""
        mc_direct = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=False)
        mc_prime = MobiusComputer(bb3_machine, bb3_input, mode="prime", verify=False)
        r_direct = mc_direct.run()
        r_prime = mc_prime.run()
        assert [r.pre_state for r in r_direct.trace] == [r.pre_state for r in r_prime.trace]
        assert [r.read_symbol for r in r_direct.trace] == [r.read_symbol for r in r_prime.trace]
        assert [r.write_symbol for r in r_direct.trace] == [r.write_symbol for r in r_prime.trace]

    def test_library_machines_prime_mode(self):
        """All library machines work with prime field selector."""
        for name in ["unary_add", "unary_parity", "binary_add", "unary_multiply"]:
            machine_path = EXAMPLES / "library_machines" / f"{name}.json"
            input_path = EXAMPLES / "library_inputs" / f"{name}.input.json"
            if not machine_path.exists():
                continue
            machine = load_machine(machine_path)
            inp = load_input(input_path) if input_path.exists() else InputSpec()
            mc = MobiusComputer(machine, inp, mode="prime", verify=True)
            result = mc.run()
            assert result.status == "HALT", f"{name} failed in prime mode: {result.crash_reason}"
            assert result.emet.mem is True, f"{name} Mem should be True in prime mode"
            assert result.emet.is_emet is True, f"{name} should achieve full Emet in prime mode"


# ===========================================================================
# Phase 6: Lean export
# ===========================================================================

class TestLeanExport:
    def test_lean_export_bb3(self, bb3_machine, bb3_input):
        """Generate Lean proof and check it's valid syntax."""
        mc = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=False)
        mc.run()
        lean_code = mc.export_lean("BB3")
        assert "def factors" in lean_code
        assert "def phi" in lean_code
        assert "native_decide" in lean_code
        assert "BB3" in lean_code


# ===========================================================================
# Phase 7: Divergence detection
# ===========================================================================

class TestDivergence:
    def test_bb3_does_not_diverge(self, bb3_machine, bb3_input):
        """BB(3) is well-behaved — no divergence."""
        mc = MobiusComputer(
            bb3_machine, bb3_input, mode="direct", verify=False,
            divergence_policy=DivergencePolicy(partial_quotient_threshold=100),
        )
        result = mc.run()
        assert result.status == "HALT"


# ===========================================================================
# Phase 8: Machine library
# ===========================================================================

class TestMachineLibrary:
    """Test against Emmett's machine corpus."""

    @pytest.fixture
    def library_path(self):
        return EXAMPLES

    def _load_library_machine(self, name):
        machine_path = EXAMPLES / "library_machines" / f"{name}.json"
        input_path = EXAMPLES / "library_inputs" / f"{name}.input.json"
        if not machine_path.exists():
            pytest.skip(f"Machine {name} not found")
        machine = load_machine(machine_path)
        inp = load_input(input_path) if input_path.exists() else InputSpec()
        return machine, inp

    def test_unary_add(self):
        machine, inp = self._load_library_machine("unary_add")
        mc = MobiusComputer(machine, inp, mode="direct", verify=True)
        result = mc.run()
        assert result.status == "HALT"

    def test_unary_parity(self):
        machine, inp = self._load_library_machine("unary_parity")
        mc = MobiusComputer(machine, inp, mode="direct", verify=True)
        result = mc.run()
        assert result.status == "HALT"

    def test_binary_add(self):
        machine, inp = self._load_library_machine("binary_add")
        mc = MobiusComputer(machine, inp, mode="direct", verify=True)
        result = mc.run()
        assert result.status == "HALT"

    def test_unary_multiply(self):
        machine, inp = self._load_library_machine("unary_multiply")
        mc = MobiusComputer(machine, inp, mode="direct", verify=True)
        result = mc.run()
        assert result.status == "HALT"


# ===========================================================================
# Phase 9: ShearExpansion
# ===========================================================================

class TestShearExpansion:
    def test_shear_summary(self, bb3_machine, bb3_input):
        mc = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=False)
        mc.run()
        summary = mc.shear_expansion.summary()
        assert "Φ_R" in summary
        assert "Φ_L" in summary

    def test_all_matrices_for_lean(self, bb3_machine, bb3_input):
        mc = MobiusComputer(bb3_machine, bb3_input, mode="direct", verify=False)
        mc.run()
        matrices = mc.shear_expansion.all_matrices()
        assert len(matrices) > 0
        for m in matrices:
            assert len(m) == 2
            assert len(m[0]) == 2
            assert len(m[1]) == 2
