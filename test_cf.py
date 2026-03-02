"""
Unit tests for the CF-based Adelic Turing Machine.
"""

import unittest
from fractions import Fraction
from cf_machine import (
    encode_tape, decode_tape, gauss_map, inverse_gauss,
    cf_digits_to_symbols, verify_product_formula,
    p_adic_valuation, p_adic_norm, real_norm,
    AdelicTM
)


class TestGaussMap(unittest.TestCase):
    """Tests for the Gauss map and its inverse."""

    def test_gauss_map_65_24(self):
        """Test Gauss map on 65/24 (from the docs example)."""
        x = Fraction(65, 24)
        digit, remainder = gauss_map(x)

        # floor(65/24) = 2
        self.assertEqual(digit, 2)
        # remainder = 1/(65/24 - 2) = 1/(17/24) = 24/17
        self.assertEqual(remainder, Fraction(24, 17))

    def test_gauss_map_chain(self):
        """Test applying Gauss map repeatedly on 65/24."""
        x = Fraction(65, 24)

        # Step 1: 65/24 -> digit 2, remainder 24/17
        d1, r1 = gauss_map(x)
        self.assertEqual(d1, 2)
        self.assertEqual(r1, Fraction(24, 17))

        # Step 2: 24/17 -> digit 1, remainder 17/7
        d2, r2 = gauss_map(r1)
        self.assertEqual(d2, 1)
        self.assertEqual(r2, Fraction(17, 7))

        # Step 3: 17/7 -> digit 2, remainder 7/3
        d3, r3 = gauss_map(r2)
        self.assertEqual(d3, 2)
        self.assertEqual(r3, Fraction(7, 3))

        # Step 4: 7/3 -> digit 2, remainder 3
        d4, r4 = gauss_map(r3)
        self.assertEqual(d4, 2)
        self.assertEqual(r4, Fraction(3, 1))

        # Step 5: 3 -> digit 3, remainder 0 (integer, terminates)
        d5, r5 = gauss_map(r4)
        self.assertEqual(d5, 3)
        self.assertEqual(r5, Fraction(0))

    def test_inverse_gauss(self):
        """Test that inverse_gauss reverses gauss_map."""
        x = Fraction(65, 24)
        digit, remainder = gauss_map(x)

        # Inverse should reconstruct x
        reconstructed = inverse_gauss(digit, remainder)
        self.assertEqual(reconstructed, x)

    def test_gauss_inverse_roundtrip(self):
        """Test multiple roundtrips."""
        test_values = [
            Fraction(7, 3),
            Fraction(22, 7),
            Fraction(355, 113),  # Famous pi approximation
        ]

        for x in test_values:
            digit, remainder = gauss_map(x)
            reconstructed = inverse_gauss(digit, remainder)
            self.assertEqual(reconstructed, x, f"Roundtrip failed for {x}")


class TestTapeEncoding(unittest.TestCase):
    """Tests for tape encoding/decoding."""

    def test_encode_1011(self):
        """Test encoding [1, 0, 1, 1] as CF."""
        tape = [1, 0, 1, 1]
        symbol_map = {0: 1, 1: 2, 2: 3, 'end': 3, 'blank': 3}

        encoded = encode_tape(tape, symbol_map)

        # Expected: [2, 1, 2, 2, 3] -> 65/24
        self.assertEqual(encoded, Fraction(65, 24))

    def test_decode_65_24(self):
        """Test decoding 65/24 back to CF digits."""
        x = Fraction(65, 24)
        digits = decode_tape(x)

        # Should get [2, 1, 2, 2, 3]
        self.assertEqual(digits, [2, 1, 2, 2, 3])

    def test_encode_decode_roundtrip(self):
        """Test that encode -> decode gives back CF digits."""
        test_tapes = [
            [0, 0, 0],
            [1, 1, 1],
            [1, 0, 1, 0],
            [0],
            [1],
            [],  # Empty tape (just end marker)
        ]

        symbol_map = {0: 1, 1: 2, 2: 3, 'end': 3, 'blank': 3}

        for tape in test_tapes:
            encoded = encode_tape(tape, symbol_map)
            decoded_digits = decode_tape(encoded)

            # The decoded digits should be [mapped symbols..., 3 (end marker)]
            expected_digits = [symbol_map[s] for s in tape] + [3]
            self.assertEqual(decoded_digits, expected_digits,
                             f"Roundtrip failed for tape {tape}")

    def test_cf_digits_to_symbols(self):
        """Test converting CF digits back to symbols."""
        cf_digits = [2, 1, 2, 2, 3]
        symbols = cf_digits_to_symbols(cf_digits)

        # Should get [1, 0, 1, 1] (excluding end marker)
        self.assertEqual(symbols, [1, 0, 1, 1])


class TestProductFormula(unittest.TestCase):
    """Tests for the product formula verification."""

    def test_product_formula_12(self):
        """Test product formula for x = 12."""
        x = Fraction(12)
        result = verify_product_formula(x)

        self.assertTrue(result["valid"])
        self.assertEqual(result["real_norm"], Fraction(12))
        # |12|_2 = 1/4 (2^2 divides 12)
        self.assertEqual(result["p_adic_norms"][2], Fraction(1, 4))
        # |12|_3 = 1/3 (3 divides 12 once)
        self.assertEqual(result["p_adic_norms"][3], Fraction(1, 3))
        # 12 * (1/4) * (1/3) = 1
        self.assertEqual(result["product"], Fraction(1))

    def test_product_formula_65_24(self):
        """Test product formula for x = 65/24."""
        x = Fraction(65, 24)
        result = verify_product_formula(x)

        self.assertTrue(result["valid"])
        # |65/24|_∞ = 65/24
        self.assertEqual(result["real_norm"], Fraction(65, 24))

    def test_product_formula_various(self):
        """Test product formula for various rationals."""
        test_values = [
            Fraction(1, 2),
            Fraction(7, 3),
            Fraction(24, 17),
            Fraction(100),
            Fraction(1, 100),
        ]

        for x in test_values:
            result = verify_product_formula(x)
            self.assertTrue(result["valid"], f"Product formula failed for {x}")


class TestPadicFunctions(unittest.TestCase):
    """Tests for p-adic utility functions."""

    def test_p_adic_valuation(self):
        """Test p-adic valuation computation."""
        # v_2(8) = 3 (8 = 2^3)
        self.assertEqual(p_adic_valuation(8, 2), 3)

        # v_2(12) = 2 (12 = 4 * 3 = 2^2 * 3)
        self.assertEqual(p_adic_valuation(12, 2), 2)

        # v_3(12) = 1
        self.assertEqual(p_adic_valuation(12, 3), 1)

        # v_5(12) = 0 (5 doesn't divide 12)
        self.assertEqual(p_adic_valuation(12, 5), 0)

        # v_2(7) = 0 (7 is odd)
        self.assertEqual(p_adic_valuation(7, 2), 0)

    def test_p_adic_norm(self):
        """Test p-adic norm computation."""
        # |12|_2 = 2^(-2) = 1/4
        self.assertEqual(p_adic_norm(Fraction(12), 2), Fraction(1, 4))

        # |12|_3 = 3^(-1) = 1/3
        self.assertEqual(p_adic_norm(Fraction(12), 3), Fraction(1, 3))

        # |1/4|_2 = 2^2 = 4 (v_2(1/4) = v_2(1) - v_2(4) = 0 - 2 = -2)
        self.assertEqual(p_adic_norm(Fraction(1, 4), 2), Fraction(4))


class TestParityChecker(unittest.TestCase):
    """Tests for the parity checker TM."""

    def setUp(self):
        """Set up parity checker transitions."""
        self.transitions = {
            (0, 0): (0, 0, 'R'),  # EVEN + 0 -> EVEN
            (0, 1): (1, 1, 'R'),  # EVEN + 1 -> ODD
            (1, 0): (1, 0, 'R'),  # ODD + 0 -> ODD
            (1, 1): (0, 1, 'R'),  # ODD + 1 -> EVEN
        }

    def test_parity_1011(self):
        """Test [1, 0, 1, 1] -> ODD (3 ones)."""
        tm = AdelicTM(self.transitions, initial_state=0, state_prime=2)
        result = tm.run([1, 0, 1, 1])

        # Final state should be 1 (ODD)
        self.assertEqual(result["final_state"], 1)
        self.assertTrue(result["halted"])

    def test_parity_11(self):
        """Test [1, 1] -> EVEN (2 ones)."""
        tm = AdelicTM(self.transitions, initial_state=0, state_prime=2)
        result = tm.run([1, 1])

        self.assertEqual(result["final_state"], 0)

    def test_parity_000(self):
        """Test [0, 0, 0] -> EVEN (0 ones)."""
        tm = AdelicTM(self.transitions, initial_state=0, state_prime=2)
        result = tm.run([0, 0, 0])

        self.assertEqual(result["final_state"], 0)

    def test_parity_1(self):
        """Test [1] -> ODD (1 one)."""
        tm = AdelicTM(self.transitions, initial_state=0, state_prime=2)
        result = tm.run([1])

        self.assertEqual(result["final_state"], 1)

    def test_parity_empty(self):
        """Test [] -> EVEN (0 ones)."""
        tm = AdelicTM(self.transitions, initial_state=0, state_prime=2)
        result = tm.run([])

        self.assertEqual(result["final_state"], 0)

    def test_parity_alternating(self):
        """Test [1, 0, 1, 0, 1, 0] -> ODD (3 ones)."""
        tm = AdelicTM(self.transitions, initial_state=0, state_prime=2)
        result = tm.run([1, 0, 1, 0, 1, 0])

        self.assertEqual(result["final_state"], 1)


class TestProductFormulaInExecution(unittest.TestCase):
    """Test that product formula holds at each step of TM execution."""

    def test_product_formula_during_parity(self):
        """Verify product formula at each step of parity checker."""
        transitions = {
            (0, 0): (0, 0, 'R'),
            (0, 1): (1, 1, 'R'),
            (1, 0): (1, 0, 'R'),
            (1, 1): (0, 1, 'R'),
        }

        tm = AdelicTM(transitions, initial_state=0, state_prime=2)
        result = tm.run([1, 0, 1, 1])

        for step in result["trace"]:
            if step.get("step") == "initial":
                x = step["right_tape"]
            elif "right_tape_after" in step:
                x = step["right_tape_after"]
            else:
                continue

            if x and x != 0:
                pf = verify_product_formula(x)
                self.assertTrue(pf["valid"],
                                f"Product formula failed at step {step.get('step')} for x={x}")


class TestAdelicTMBasics(unittest.TestCase):
    """Basic tests for AdelicTM class."""

    def test_encode_state(self):
        """Test state encoding as residue mod prime."""
        tm = AdelicTM({}, initial_state=0, state_prime=2)

        self.assertEqual(tm.encode_state(0), 0)
        self.assertEqual(tm.encode_state(1), 1)
        self.assertEqual(tm.encode_state(2), 0)
        self.assertEqual(tm.encode_state(3), 1)

    def test_state_prime_3(self):
        """Test with state_prime=3."""
        tm = AdelicTM({}, initial_state=0, state_prime=3)

        self.assertEqual(tm.encode_state(0), 0)
        self.assertEqual(tm.encode_state(1), 1)
        self.assertEqual(tm.encode_state(2), 2)
        self.assertEqual(tm.encode_state(3), 0)
        self.assertEqual(tm.encode_state(4), 1)

    def test_get_adelic_state(self):
        """Test adelic state representation."""
        transitions = {(0, 1): (1, 1, 'R')}
        tm = AdelicTM(transitions, initial_state=0, state_prime=2)
        tm.right_tape = Fraction(65, 24)
        tm.state = 1

        adelic = tm.get_adelic_state()

        self.assertEqual(adelic["alpha_infinity"], Fraction(65, 24))
        self.assertEqual(adelic["alpha_p"], 1)  # 1 mod 2
        self.assertEqual(adelic["state_prime"], 2)
        self.assertEqual(adelic["state"], 1)


class TestIncrementer(unittest.TestCase):
    """Tests for the binary incrementer TM."""

    def setUp(self):
        """Set up incrementer transitions."""
        self.transitions = {
            (0, 0): (1, 1, 'H'),  # CARRY + 0 -> write 1, DONE, halt
            (0, 1): (0, 0, 'L'),  # CARRY + 1 -> write 0, keep carrying, move left
            (1, 0): (1, 0, 'H'),  # DONE (shouldn't happen in normal flow)
            (1, 1): (1, 1, 'H'),  # DONE
        }

    def _run_incrementer(self, tape: list[int]) -> list[int]:
        """Run incrementer and return output tape."""
        tm = AdelicTM(self.transitions, initial_state=0, state_prime=2)
        result = tm.run(tape, start_at='right')

        # Reconstruct output tape
        end_marker = tm.symbol_map.get('end', 3)

        left_symbols = []
        for d in result['left_digits_final']:
            if d == end_marker:
                continue
            left_symbols.append(tm._digit_to_symbol(d))

        right_symbols = []
        for d in result['right_digits_final']:
            if d == end_marker:
                continue
            right_symbols.append(tm._digit_to_symbol(d))

        # Left tape is reversed
        return list(reversed(left_symbols)) + right_symbols

    def _tape_to_int(self, tape: list[int]) -> int:
        """Convert binary tape (MSB first) to integer."""
        if not tape:
            return 0
        return sum(b * (2 ** (len(tape) - 1 - i)) for i, b in enumerate(tape))

    def test_increment_011_to_100(self):
        """Test 011 (3) -> 100 (4)."""
        tape = [0, 1, 1]  # 3
        output = self._run_incrementer(tape)
        output_val = self._tape_to_int(output)

        self.assertEqual(output_val, 4)

    def test_increment_001_to_010(self):
        """Test 001 (1) -> 010 (2)."""
        tape = [0, 0, 1]
        output = self._run_incrementer(tape)
        output_val = self._tape_to_int(output)

        self.assertEqual(output_val, 2)

    def test_increment_000_to_001(self):
        """Test 000 (0) -> 001 (1)."""
        tape = [0, 0, 0]
        output = self._run_incrementer(tape)
        output_val = self._tape_to_int(output)

        self.assertEqual(output_val, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
