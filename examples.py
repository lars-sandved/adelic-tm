"""
Examples demonstrating the CF-based Adelic Turing Machine.

1. Parity Checker - Read-only machine that determines odd/even count of 1s
2. Binary Incrementer - Read-write machine that adds 1 to a binary number
"""

from fractions import Fraction
from cf_machine import (
    AdelicTM, encode_tape, decode_tape, gauss_map, inverse_gauss,
    verify_product_formula, p_adic_norm, real_norm
)


def parity_checker():
    """
    Parity Checker: Determines if input has odd or even number of 1s.

    States:
        0 = EVEN (even number of 1s seen so far)
        1 = ODD (odd number of 1s seen so far)

    Transitions (read-only, always move right):
        (EVEN, 0) -> (EVEN, 0, R)  - read 0, stay EVEN
        (EVEN, 1) -> (ODD, 1, R)   - read 1, flip to ODD
        (ODD, 0)  -> (ODD, 0, R)   - read 0, stay ODD
        (ODD, 1)  -> (EVEN, 1, R)  - read 1, flip to EVEN

    The machine halts when it reaches the end marker.
    Final state = parity (0=EVEN, 1=ODD)
    """
    print("=" * 70)
    print("  PARITY CHECKER - CF-based Adelic Turing Machine")
    print("=" * 70)
    print()
    print("States: 0 = EVEN, 1 = ODD")
    print("Symbols: 0 -> CF digit 1, 1 -> CF digit 2, end -> CF digit 3")
    print()

    # Define transitions: (state, symbol) -> (new_state, write_symbol, direction)
    # For parity checker, write_symbol = read symbol (no modification)
    transitions = {
        (0, 0): (0, 0, 'R'),  # EVEN + 0 -> EVEN
        (0, 1): (1, 1, 'R'),  # EVEN + 1 -> ODD
        (1, 0): (1, 0, 'R'),  # ODD + 0 -> ODD
        (1, 1): (0, 1, 'R'),  # ODD + 1 -> EVEN
    }

    # Test cases: (input, expected_parity)
    test_cases = [
        ([1, 0, 1, 1], "ODD"),   # 3 ones -> ODD
        ([1, 1], "EVEN"),        # 2 ones -> EVEN
        ([0, 0, 0], "EVEN"),     # 0 ones -> EVEN
        ([1], "ODD"),            # 1 one -> ODD
        ([], "EVEN"),            # 0 ones -> EVEN
    ]

    # First, detailed walkthrough of [1, 0, 1, 1]
    print("-" * 70)
    print("  Detailed walkthrough: input [1, 0, 1, 1]")
    print("-" * 70)
    print()

    tape = [1, 0, 1, 1]
    tm = AdelicTM(transitions, initial_state=0, state_prime=2)
    encoded = encode_tape(tape, tm.symbol_map)

    print(f"Input tape: {tape}")
    print(f"CF digits:  [2, 1, 2, 2, 3]  (1->2, 0->1, end->3)")
    print(f"Encoded as: {encoded} = {float(encoded):.6f}")
    print()
    print("Verify CF encoding:")
    print("  [2; 1, 2, 2, 3] = 2 + 1/(1 + 1/(2 + 1/(2 + 1/3)))")
    print(f"                 = 2 + 1/(1 + 1/(2 + 1/(7/3)))")
    print(f"                 = 2 + 1/(1 + 1/(2 + 3/7))")
    print(f"                 = 2 + 1/(1 + 1/(17/7))")
    print(f"                 = 2 + 1/(1 + 7/17)")
    print(f"                 = 2 + 1/(24/17)")
    print(f"                 = 2 + 17/24 = 65/24 ✓")
    print()

    # Run step by step
    result = tm.run(tape)

    print("Execution trace:")
    print()

    for i, step in enumerate(result["trace"]):
        if step.get("step") == "initial":
            print(f"  Initial: state={step['state']} ({'EVEN' if step['state']==0 else 'ODD'}), "
                  f"α∞={step['right_tape']}")
            print()
            continue

        if step.get("halted"):
            reason = step.get("reason", "unknown")
            if reason == "end_of_tape":
                state_name = "EVEN" if step['state_after'] == 0 else "ODD"
                print(f"  Step {step['step']}: READ end marker (digit 3)")
                print(f"           HALT - Final state: {step['state_after']} ({state_name})")
            break

        state_before = "EVEN" if step['state_before'] == 0 else "ODD"
        state_after = "EVEN" if step['state_after'] == 0 else "ODD"
        symbol_read = step['symbol_read']
        cf_digit = step['cf_digit_read']

        print(f"  Step {step['step']}:")
        print(f"    α∞ = {step['right_tape_before']}")
        print(f"    READ: floor({step['right_tape_before']}) = {cf_digit} -> symbol {symbol_read}")
        print(f"    STATE: {state_before} + symbol {symbol_read} -> {state_after}")
        print(f"    GAUSS: G({step['right_tape_before']}) = {step['right_tape_after']}")

        # Verify product formula
        if step['right_tape_after']:
            pf = verify_product_formula(step['right_tape_after'])
            if pf['valid']:
                norms = [f"|x|_∞={pf['real_norm']}"]
                for p, norm in pf['p_adic_norms'].items():
                    norms.append(f"|x|_{p}={norm}")
                print(f"    Product formula: {' × '.join(norms)} = 1 ✓")

        print()

    final_parity = "ODD" if result["final_state"] == 1 else "EVEN"
    print(f"  RESULT: {final_parity} parity")
    print()

    # Run all test cases
    print("-" * 70)
    print("  Test cases")
    print("-" * 70)
    print()

    all_passed = True
    for tape, expected in test_cases:
        tm = AdelicTM(transitions, initial_state=0, state_prime=2)
        result = tm.run(tape)
        actual = "ODD" if result["final_state"] == 1 else "EVEN"
        passed = actual == expected
        all_passed = all_passed and passed

        status = "✓" if passed else "✗"
        encoded_val = encode_tape(tape, tm.symbol_map) if tape else Fraction(3)
        print(f"  {status} Input {str(tape):15} -> α∞ = {str(encoded_val):12} -> {actual:4} (expected {expected})")

    print()
    if all_passed:
        print("  All tests passed!")
    else:
        print("  Some tests FAILED!")
    print()

    return all_passed


def incrementer():
    """
    Binary Incrementer: Adds 1 to a binary number.

    The tape represents a binary number with LSB on the right.
    Head starts at the rightmost (LSB) position and moves LEFT.

    States:
        0 = CARRY (we have a carry to propagate)
        1 = DONE (carry absorbed, just copying)

    Transitions:
        (CARRY, 1) -> (CARRY, 0, L)  - flip 1 to 0, keep carrying
        (CARRY, 0) -> (DONE, 1, H)   - flip 0 to 1, stop
        (DONE, *)  -> halt           - done

    Example: 011 (=3) -> 100 (=4)
    """
    print("=" * 70)
    print("  BINARY INCREMENTER - CF-based Adelic Turing Machine")
    print("=" * 70)
    print()
    print("Adds 1 to a binary number. Head starts at LSB (rightmost), moves LEFT.")
    print("States: 0 = CARRY, 1 = DONE")
    print()

    # Define transitions
    # Note: When we hit the left boundary, we need special handling
    transitions = {
        (0, 0): (1, 1, 'H'),  # CARRY + 0 -> write 1, DONE, halt
        (0, 1): (0, 0, 'L'),  # CARRY + 1 -> write 0, keep carrying, move left
        (1, 0): (1, 0, 'H'),  # DONE + 0 -> halt (shouldn't happen in normal flow)
        (1, 1): (1, 1, 'H'),  # DONE + 1 -> halt
    }

    print("-" * 70)
    print("  Example: 011 (=3) -> 100 (=4)")
    print("-" * 70)
    print()

    # For incrementer, we need to handle the two-tape model carefully
    # Input: [0, 1, 1] represents binary 011 = 3 (MSB first)
    # We start at the rightmost position (LSB)

    tape = [0, 1, 1]  # Binary 011 = 3 (MSB first in list)
    print(f"Input tape: {tape}  (binary {tape[0]}{tape[1]}{tape[2]} = {tape[0]*4 + tape[1]*2 + tape[2]})")
    print()

    # Create TM with start_at='right'
    tm = AdelicTM(transitions, initial_state=0, state_prime=2)
    result = tm.run(tape, start_at='right')

    print("Execution trace:")
    print()

    for i, step in enumerate(result["trace"]):
        if step.get("step") == "initial":
            print(f"  Initial: state={step['state']} (CARRY)")
            print(f"           right_tape={step['right_tape']} (current cell + right)")
            print(f"           left_tape={step['left_tape']} (cells to the left)")
            print()
            continue

        if step.get("halted"):
            state_name = "CARRY" if step.get('state_after', 0) == 0 else "DONE"
            reason = step.get('reason', '')
            if reason == 'halt_direction':
                print(f"  Step {step['step']}: HALT in state {state_name}")
                print(f"           Final right_tape: {step.get('right_tape_after', result['right_tape_final'])}")
                print(f"           Final left_tape: {step.get('left_tape_after', result['left_tape_final'])}")
            break

        state_before = "CARRY" if step['state_before'] == 0 else "DONE"
        state_after = "CARRY" if step['state_after'] == 0 else "DONE"
        symbol_read = step['symbol_read']
        write_symbol = step['write_symbol']
        direction = step['direction']

        print(f"  Step {step['step']}:")
        print(f"    READ: {symbol_read}, STATE: {state_before}")
        print(f"    WRITE: {write_symbol}, MOVE: {direction}, NEW STATE: {state_after}")
        print(f"    right_tape: {step['right_tape_before']} -> {step.get('right_tape_after', '?')}")
        print(f"    left_tape: {step['left_tape_before']} -> {step.get('left_tape_after', '?')}")
        print()

    # Decode final tape
    print("Final tape state:")
    print(f"  right_tape = {result['right_tape_final']}")
    print(f"  left_tape = {result['left_tape_final']}")
    print(f"  right CF digits = {result['right_digits_final']}")
    print(f"  left CF digits = {result['left_digits_final']}")
    print()

    # Reconstruct the output tape
    # Left tape is reversed (leftmost symbols are deepest in CF)
    left_symbols = []
    end_marker = tm.symbol_map.get('end', 3)
    for d in result['left_digits_final']:
        if d == end_marker:
            continue
        left_symbols.append(tm._digit_to_symbol(d))

    right_symbols = []
    for d in result['right_digits_final']:
        if d == end_marker:
            continue
        right_symbols.append(tm._digit_to_symbol(d))

    # Left tape symbols are in reverse order (reversed during encoding)
    output_tape = list(reversed(left_symbols)) + right_symbols
    print(f"Reconstructed tape: {output_tape}")
    if output_tape:
        binary_val = sum(b * (2 ** (len(output_tape) - 1 - i)) for i, b in enumerate(output_tape))
        print(f"Binary value: {''.join(str(x) for x in output_tape)} = {binary_val}")
    print()

    # Additional test cases
    print("-" * 70)
    print("  Additional test cases")
    print("-" * 70)
    print()

    test_cases = [
        ([0, 0, 1], 1, 2),   # 001 = 1 -> 010 = 2
        ([0, 1, 1], 3, 4),   # 011 = 3 -> 100 = 4
        ([1, 1, 1], 7, 8),   # 111 = 7 -> 1000 = 8 (overflow)
        ([0, 0, 0], 0, 1),   # 000 = 0 -> 001 = 1
    ]

    for tape, val_in, val_out in test_cases:
        print(f"  Testing: {tape} ({val_in}) -> expected {val_out}")
        tm = AdelicTM(transitions, initial_state=0, state_prime=2)
        result = tm.run(tape, start_at='right')

        # Reconstruct output
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

        output = list(reversed(left_symbols)) + right_symbols
        if output:
            computed_val = sum(b * (2 ** (len(output) - 1 - i)) for i, b in enumerate(output))
        else:
            computed_val = 0

        status = "✓" if computed_val == val_out else "✗"
        print(f"    {status} Output: {output} = {computed_val}")
    print()


def run_all_examples():
    """Run all examples."""
    print()
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*    CF-BASED ADELIC TURING MACHINE - EXAMPLES" + " " * 22 + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print()

    parity_passed = parity_checker()
    print()
    print()
    incrementer()


if __name__ == "__main__":
    run_all_examples()
