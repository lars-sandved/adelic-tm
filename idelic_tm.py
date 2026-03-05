"""
The Idelic Turing Machine
===========================

Implementation of Emmett Shear's framework (March 2026):
  Shape = Program, Magnitude = Tape, CF extraction = Execution

The tape is encoded as TWO magnitudes:
  R = cell₀/d + cell₁/d² + cell₂/d³ + ...    (rightward from head)
  L = cell₋₁/d + cell₋₂/d² + ...              (leftward from head)

The fetch-execute cycle at each step:
  1. FETCH  (Ostrowski extraction): digit = floor(d × R)
  2. DECODE (transition lookup):    (state, digit) → (write, new_state, dir)
  3. EXECUTE (tape rewrite):        R ← R − read/d + write/d
  4. SHIFT  (magnitude scaling):    scale L,R based on direction

References:
  - Emmett Shear, "The Idelic Turing Machine" (2026)
  - Emmett Shear, "Continued Fractions from Magnitude and Shape" (2026)
"""

from fractions import Fraction


class TapeAsMagnitude:
    """
    Bidirectional tape encoded as two rational magnitudes L, R.

    R encodes cells rightward from head (cell₀ at head):
      R = cell₀/d + cell₁/d² + cell₂/d³ + ...

    L encodes cells leftward from head:
      L = cell₋₁/d + cell₋₂/d² + ...

    d = alphabet size (denominator of the shape).
    θ = 1/d = the read quantum (Ostrowski basis element).
    """

    def __init__(self, d: int, R: Fraction = Fraction(0), L: Fraction = Fraction(0)):
        self.d = d
        self.theta = Fraction(1, d)
        self.R = R
        self.L = L

    @classmethod
    def from_cells(cls, d: int, right_cells: list[int], left_cells: list[int] = None):
        """
        Build tape from explicit cell values.

        right_cells[0] = cell under head, right_cells[1] = one right, etc.
        left_cells[0] = one left of head, left_cells[1] = two left, etc.
        """
        R = Fraction(0)
        for i, cell in enumerate(right_cells):
            R += Fraction(cell, d ** (i + 1))

        L = Fraction(0)
        if left_cells:
            for i, cell in enumerate(left_cells):
                L += Fraction(cell, d ** (i + 1))

        return cls(d, R, L)

    def read(self) -> int:
        """
        FETCH: Ostrowski extraction.

        digit = floor(R / θ) = floor(d × R)

        This IS the continued fraction "extract integer part" step.
        The shape determines θ, which determines the digit basis.
        """
        return int(self.d * self.R)

    def write(self, old_symbol: int, new_symbol: int):
        """
        EXECUTE: Tape rewrite via magnitude adjustment.

        R ← R − old/d + new/d = R + (new − old)/d

        The net change is a rational quantum: (new − old) × θ.
        """
        self.R = self.R - Fraction(old_symbol, self.d) + Fraction(new_symbol, self.d)

    def move_right(self, written_symbol: int):
        """
        SHIFT RIGHT: Push current cell onto L, advance R.

        L ← written_symbol/d + L/d    (push symbol onto left stack)
        R ← (R − written_symbol/d) × d (pop head cell, scale up)
        """
        new_L = Fraction(written_symbol, self.d) + self.L / self.d
        new_R = (self.R - Fraction(written_symbol, self.d)) * self.d
        self.L = new_L
        self.R = new_R

    def move_left(self, written_symbol: int):
        """
        SHIFT LEFT: Pop from L, push current cell onto R.

        The left magnitude's leading digit becomes the new cell under head.
        L ← (L − popped/d) × d     (pop from left stack, scale up)
        R ← written_symbol/d + R/d  (push current cell onto right, scale down)

        But we need to read the top of L first: popped = floor(d × L).
        """
        popped = int(self.d * self.L)
        new_R = Fraction(popped, self.d) + self.R / self.d
        new_L = (self.L - Fraction(popped, self.d)) * self.d
        self.L = new_L
        self.R = new_R

    def to_cells(self, n: int = 8) -> tuple[list[int], list[int]]:
        """Extract first n cells in each direction (for display)."""
        right = []
        r = self.R
        for _ in range(n):
            digit = int(self.d * r)
            right.append(digit)
            r = r * self.d - digit

        left = []
        l = self.L
        for _ in range(n):
            digit = int(self.d * l)
            left.append(digit)
            l = l * self.d - digit

        return left, right


class IdelicTM:
    """
    A Turing machine executing via idelic magnitude arithmetic.

    The transition table maps (state, symbol) → (write, new_state, direction).
    Direction is 'R' (right), 'L' (left), or 'H' (halt).

    The tape is encoded as two rational magnitudes (L, R).
    All tape operations are rational arithmetic — no arrays, no indexing.
    """

    def __init__(self, d: int, transitions: dict, initial_state: int):
        """
        Args:
            d: alphabet size (number of symbols, = base for magnitudes)
            transitions: dict mapping (state, symbol) → (write, new_state, 'R'|'L'|'H')
            initial_state: starting state
        """
        self.d = d
        self.transitions = transitions
        self.initial_state = initial_state

    def run(self, tape: TapeAsMagnitude, max_steps: int = 100):
        """
        Execute the TM on the given tape.

        Returns: list of step records, each containing full state.
        """
        state = self.initial_state
        history = []

        for step in range(max_steps):
            # ── Phase 1: FETCH (Ostrowski extraction) ──
            symbol = tape.read()

            # Check for halt
            key = (state, symbol)
            if key not in self.transitions:
                history.append({
                    "step": step,
                    "state": state,
                    "read": symbol,
                    "action": "HALT",
                    "R": Fraction(tape.R),
                    "L": Fraction(tape.L),
                })
                return history, state, True

            # ── Phase 2: DECODE (transition lookup) ──
            write_sym, new_state, direction = self.transitions[key]

            # Record pre-step state
            record = {
                "step": step,
                "state": state,
                "read": symbol,
                "write": write_sym,
                "new_state": new_state,
                "direction": direction,
                "R_before": Fraction(tape.R),
                "L_before": Fraction(tape.L),
            }

            # ── Phase 3: EXECUTE (tape rewrite) ──
            tape.write(symbol, write_sym)

            # ── Phase 4: SHIFT (magnitude scaling) ──
            if direction == 'R':
                tape.move_right(write_sym)
            elif direction == 'L':
                tape.move_left(write_sym)

            record["R_after"] = Fraction(tape.R)
            record["L_after"] = Fraction(tape.L)
            history.append(record)

            state = new_state

        return history, state, False  # Did not halt

    def trace(self, tape: TapeAsMagnitude, max_steps: int = 100):
        """Run with detailed output."""
        print(f"\n  Initial: state={self.initial_state}, R={tape.R} ({float(tape.R):.4f}), L={tape.L} ({float(tape.L):.4f})")
        left_cells, right_cells = tape.to_cells(6)
        left_str = ' '.join(str(c) for c in reversed(left_cells))
        right_str = ' '.join(str(c) for c in right_cells)
        print(f"  Tape: ...{left_str} [{right_cells[0]}] {' '.join(str(c) for c in right_cells[1:])}...")

        print(f"\n  {'Step':>4} │ {'State':>5} │ {'Read':>4} │ {'Write':>5} │ {'→State':>6} │ {'Dir':>3} │ {'R before':>12} │ {'R after':>12}")
        print(f"  {'─'*4}─┼{'─'*5}─┼{'─'*4}─┼{'─'*5}─┼{'─'*6}─┼{'─'*3}─┼{'─'*12}─┼{'─'*12}")

        history, final_state, halted = self.run(tape, max_steps)

        for h in history:
            if h.get("action") == "HALT":
                print(f"  {h['step']:>4} │ {h['state']:>5} │ {h['read']:>4} │ {'—':>5} │ {'—':>6} │ {'H':>3} │ {str(h['R']):>12} │ {'HALT':>12}")
            else:
                print(f"  {h['step']:>4} │ {h['state']:>5} │ {h['read']:>4} │ {h['write']:>5} │ {h['new_state']:>6} │ {h['direction']:>3} │ {str(h['R_before']):>12} │ {str(h['R_after']):>12}")

        print(f"\n  {'Halted' if halted else 'Did not halt'} after {len(history)} steps. Final state: {final_state}")

        # Show R trajectory
        r_values = []
        for h in history:
            r_values.append(h.get('R_before', h.get('R')))
        if history and 'R_after' in history[-1]:
            r_values.append(history[-1]['R_after'])
        print(f"  R trajectory: {' → '.join(str(r) for r in r_values)}")

        return history, final_state, halted


# ════════════════════════════════════════════════════════════════════════
# EMMETT'S EXACT EXAMPLE
# ════════════════════════════════════════════════════════════════════════

def emmett_example():
    """
    Reproduce Emmett's worked example exactly.

    2-state TM, 4-symbol alphabet:
      State 1, Read 3 → Write 2, State 0, Right
      State 0, Read 2 → Write 1, State 1, Right
      State 1, Read 1 → Write 0, State 0, Left
      State 0, Read 1 → Write 0, State 1, Left
      State 1, Read 2 → Write 1, State 0, Right
      State 0, Read 0 → HALT

    Initial tape: ...0 0 [3] 2 1 0 0...
    Expected R trajectory: 57/64 → 9/16 → 1/4 → 1/4 → 1/2 → 0
    """
    print("=" * 65)
    print("  EMMETT'S EXACT EXAMPLE: 2-state, 4-symbol TM")
    print("  From 'The Idelic Turing Machine' (March 2026)")
    print("=" * 65)

    # Transition table
    transitions = {
        (1, 3): (2, 0, 'R'),
        (0, 2): (1, 1, 'R'),
        (1, 1): (0, 0, 'L'),
        (0, 1): (0, 1, 'L'),
        (1, 2): (1, 0, 'R'),
        # (0, 0) → HALT (not in table = halt)
    }

    # Build tape: ...0 0 [3] 2 1 0 0...
    # right_cells = [3, 2, 1, 0, 0] (cell under head = 3, then 2, 1, 0, 0)
    # left_cells = [0, 0, 0] (all zeros to the left)
    d = 4
    tape = TapeAsMagnitude.from_cells(d, [3, 2, 1, 0, 0], [0, 0, 0])

    print(f"\n  Alphabet: {{0, 1, 2, 3}}, Base d = {d}")
    print(f"  Shape: α = 5/4, CF = [1; 4], θ = 1/{d}")
    print(f"  Initial R = {tape.R} = {float(tape.R):.6f}")
    print(f"  Expected R = 57/64 = {57/64:.6f}")
    assert tape.R == Fraction(57, 64), f"R should be 57/64, got {tape.R}"
    print(f"  ✓ R = 57/64 confirmed")

    tm = IdelicTM(d, transitions, initial_state=1)
    history, final_state, halted = tm.trace(tape)

    # Verify against Emmett's expected trajectory
    expected_R = [
        Fraction(57, 64),   # Step 0: before
        Fraction(9, 16),    # Step 1: after move (= before step 1)
        Fraction(1, 4),     # Step 2: after move
        Fraction(1, 4),     # Step 3: after move
        Fraction(1, 2),     # Step 4: after move
        Fraction(0),        # Step 5: HALT
    ]

    print(f"\n  Verification against Emmett's document:")
    r_trajectory = [h.get('R_before', h.get('R')) for h in history]
    # Add final R
    if history and 'R_after' in history[-1]:
        r_trajectory.append(history[-1]['R_after'])
    elif history and 'R' in history[-1]:
        r_trajectory.append(history[-1]['R'])

    all_match = True
    for i, (actual, expected) in enumerate(zip(r_trajectory, expected_R)):
        match = actual == expected
        if not match:
            all_match = False
        print(f"    Step {i}: R = {str(actual):>8} {'✓' if match else '✗'} (expected {expected})")

    print(f"\n  {'✓ ALL MATCH' if all_match else '✗ MISMATCH'} — Emmett's arithmetic verified")
    return all_match


# ════════════════════════════════════════════════════════════════════════
# CF CONNECTION: Show how each step IS a CF operation
# ════════════════════════════════════════════════════════════════════════

def show_cf_connection():
    """Show how each TM step maps to CF operations."""
    print("\n" + "=" * 65)
    print("  CF ↔ TM CORRESPONDENCE")
    print("=" * 65)

    print("""
  CF Operation          │ TM Phase     │ Magnitude Operation
  ─────────────────────┼─────────────┼──────────────────────────
  Extract integer part  │ 1. FETCH     │ digit = floor(d × R)
  Subtract extracted    │ 3. EXECUTE   │ R ← R − (read−write)/d
  Scale (invert)        │ 4. SHIFT     │ R ← R × d (reposition)
  Iterate               │ Next step    │ Apply same shape again

  The Collatz connection:
  In base d=2 (binary):
    FETCH:   digit = floor(2 × R) = leading bit = parity
    EXECUTE: depends on digit (even/odd branch)
    SHIFT:   R ← 2R (equivalent to reading next bit)

  Our ℤ₂ Collatz IS this framework with d=2!
  The difference: Collatz transforms the WHOLE magnitude
  (×3, +1) rather than rewriting one cell.
    """)


# ════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ok = emmett_example()
    show_cf_connection()

    if ok:
        print("\n  ✓ Emmett's idelic TM framework verified and implemented.")
        print("  File: /root/adelic-tm/idelic_tm.py")
    else:
        print("\n  ✗ Verification failed — check implementation.")
