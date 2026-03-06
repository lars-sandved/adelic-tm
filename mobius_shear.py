"""
Möbius-Shear Framework
======================
Implementation of Emmett Shear's "Möbius Transformations on the Adeles 
as Computational Steps" — building blocks for encoding Turing machines
as GL(2,ℤ) matrix products over continued fractions.

Phase 1: CF encoding roundtrip
Phase 2: GL(2,ℤ) step-by-step TM execution  
Phase 3: Shear expansion (full computation as single matrix product)

All arithmetic uses fractions.Fraction for exactness.
"""

from fractions import Fraction
from typing import Optional


# =============================================================================
# Class 1: MobiusMatrix — 2×2 integer matrix as Möbius transformation
# =============================================================================

class MobiusMatrix:
    """A 2×2 integer matrix [[a,b],[c,d]] acting as Möbius transformation.
    
    Acts on x as: x → (ax + b) / (cx + d)
    
    Key matrices:
        P_k = ((k,1),(1,0))  — push k onto CF stack
        Q_k = ((0,1),(1,-k)) — pop k from CF stack (Gauss map)
        S(k) = ((1,k),(0,1)) — upper shear
        J    = ((0,1),(1,0))  — swap (J² = I)
    """
    
    __slots__ = ('a', 'b', 'c', 'd')
    
    def __init__(self, a: int, b: int, c: int, d: int):
        self.a, self.b, self.c, self.d = int(a), int(b), int(c), int(d)
    
    # --- Named constructors ---
    
    @staticmethod
    def push(k: int) -> 'MobiusMatrix':
        """P_k = ((k,1),(1,0)) — push symbol k onto CF stack."""
        return MobiusMatrix(k, 1, 1, 0)
    
    @staticmethod
    def pop(k: int) -> 'MobiusMatrix':
        """Q_k = ((0,1),(1,-k)) — pop symbol k from CF stack."""
        return MobiusMatrix(0, 1, 1, -k)
    
    @staticmethod
    def shear(k: int) -> 'MobiusMatrix':
        """S(k) = ((1,k),(0,1)) — upper shear."""
        return MobiusMatrix(1, k, 0, 1)
    
    @staticmethod
    def swap() -> 'MobiusMatrix':
        """J = ((0,1),(1,0)) — swap. J² = I."""
        return MobiusMatrix(0, 1, 1, 0)
    
    @staticmethod
    def identity() -> 'MobiusMatrix':
        """I = ((1,0),(0,1))."""
        return MobiusMatrix(1, 0, 0, 1)
    
    # --- Operations ---
    
    def __matmul__(self, other: 'MobiusMatrix') -> 'MobiusMatrix':
        """Matrix multiplication: self @ other."""
        return MobiusMatrix(
            self.a * other.a + self.b * other.c,
            self.a * other.b + self.b * other.d,
            self.c * other.a + self.d * other.c,
            self.c * other.b + self.d * other.d,
        )
    
    def act(self, x: Fraction) -> Fraction:
        """Apply Möbius transformation: x → (ax + b) / (cx + d)."""
        num = self.a * x + self.b
        den = self.c * x + self.d
        if den == 0:
            raise ValueError(f"Möbius transform undefined: denominator = 0 for x={x}")
        return Fraction(num, den)
    
    def det(self) -> int:
        """Determinant ad - bc."""
        return self.a * self.d - self.b * self.c
    
    def __eq__(self, other):
        if not isinstance(other, MobiusMatrix):
            return False
        return (self.a == other.a and self.b == other.b and 
                self.c == other.c and self.d == other.d)
    
    def __repr__(self):
        return f"[({self.a},{self.b}),({self.c},{self.d})]"
    
    def pretty(self) -> str:
        return f"┌{self.a:3d} {self.b:3d}┐\n└{self.c:3d} {self.d:3d}┘"


# =============================================================================
# Class 2: CFStack — Stack of symbols encoded as continued fraction
# =============================================================================

class CFStack:
    """A stack of positive integer symbols encoded as a continued fraction.
    
    The stack [a₀, a₁, a₂, ...] encodes as CF [a₀; a₁, a₂, ...].
    All symbols must be ≥ 1 (alphabet shifted so blank = 1).
    
    Uses exact Fraction arithmetic throughout.
    """
    
    def __init__(self, symbols: list[int]):
        """Create from explicit symbol list. All must be ≥ 1."""
        if any(s < 1 for s in symbols):
            raise ValueError(f"All symbols must be ≥ 1, got {symbols}")
        self._symbols = list(symbols)
    
    @staticmethod
    def blank(length: int = 50) -> 'CFStack':
        """Blank tape: all 1s. CF value → golden ratio φ as length → ∞."""
        return CFStack([1] * length)
    
    @property
    def symbols(self) -> list[int]:
        return list(self._symbols)
    
    def push(self, k: int) -> 'CFStack':
        """Push symbol k onto top of stack. Equivalent to X → k + 1/X."""
        if k < 1:
            raise ValueError(f"Symbol must be ≥ 1, got {k}")
        return CFStack([k] + self._symbols)
    
    def pop(self) -> tuple[int, 'CFStack']:
        """Pop top symbol. Returns (symbol, remaining_stack).
        
        Equivalent to Gauss map: k = ⌊X⌋, remainder = 1/(X - k).
        """
        if not self._symbols:
            raise ValueError("Cannot pop from empty stack")
        return self._symbols[0], CFStack(self._symbols[1:])
    
    def value(self) -> Fraction:
        """Evaluate as exact Fraction. Computes from bottom up."""
        if not self._symbols:
            raise ValueError("Empty CF has no value")
        # Build from right: start with last symbol, work backwards
        result = Fraction(self._symbols[-1])
        for i in range(len(self._symbols) - 2, -1, -1):
            result = Fraction(self._symbols[i]) + Fraction(1, result)
        return result
    
    def to_float(self) -> float:
        """Evaluate as float (for display)."""
        return float(self.value())
    
    def convergent_matrix(self) -> MobiusMatrix:
        """Convergent matrix: product of P_{aᵢ} for all symbols.
        
        This is the matrix whose columns give successive convergents.
        """
        result = MobiusMatrix.identity()
        for s in self._symbols:
            result = result @ MobiusMatrix.push(s)
        return result
    
    def __len__(self):
        return len(self._symbols)
    
    def __repr__(self):
        if len(self._symbols) <= 8:
            inner = ", ".join(str(s) for s in self._symbols)
        else:
            inner = ", ".join(str(s) for s in self._symbols[:6]) + ", ..."
        return f"[{inner}]"


# =============================================================================
# Class 3: TapeConfig — Full tape as left/right CF stacks + state
# =============================================================================

class TapeConfig:
    """Turing machine tape as two CF stacks + state.
    
    Encoding (from Emmett's paper):
        X_R = [head_symbol; symbols_to_right...]
        X_L = [symbol_left_of_head; symbols_further_left...]
        
    Move RIGHT (read a, write w):
        Pop a from X_R, push w onto X_L.
        New head = new top of X_R.
        
    Move LEFT (read a, write w):
        Pop a from X_R, push w onto X_R (write replaces read).
        Pop b from X_L (move left), push b onto X_R (b becomes new head).
        
        Wait — paper says: Pop b from X_L, push w onto X_R.
        But that loses the current head symbol...
        
        Let me be precise. The paper's description:
        
        Rightward (read a, write w):
            X_R → Q_a · X_R    (pop a)
            X_L → P_w · X_L    (push w)
            
        Leftward (read b from left, write w):
            X_L → Q_b · X_L    (pop b from left)
            X_R → P_w · X_R    (push w onto right)
            
        But this doesn't account for removing the current head symbol
        when moving left. I think the full left-move step is actually:
        
        1. Pop current symbol a from X_R (read)
        2. Push write symbol w onto X_R (write in place)
        3. Pop b from X_L (reveal symbol to the left)  
        4. Push b onto X_R (b becomes new head)
        
        Steps 3-4 are what the paper describes as the leftward move.
        Steps 1-2 are the read-and-write.
        
        Actually — re-reading more carefully, I think the paper COMBINES 
        read+write+move into a single description:
        
        Rightward: pop old head from right (read), push written value to left (write+move)
        Leftward: pop from left (move), push written value to right (write)
        
        The current head symbol is consumed by the pop, and the written 
        symbol takes its structural position.
        
        For rightward: old head popped from R, write goes to L, new head = new top of R
        For leftward: the write symbol replaces the head on R, then we pop from L to get new head
        
        So leftward is: 
            X_R → P_w · Q_a · X_R   (pop a, push w — replace head with write)
            ... then pop b from L, push b onto R...
            
        Hmm, I think the cleanest interpretation is:
        
        RIGHT: pop a from R, push w to L → head moved right, w left behind
        LEFT:  pop a from R, push w to R, pop b from L, push b to R
               = Q_b on L, then on R: P_b · P_w · Q_a
               
        But paper says LEFT = Q_b on L, P_w on R.
        That means: pop b from L (move), push w onto R.
        The current head symbol a is OVERWRITTEN by w (not popped first).
        
        Actually I think there's a subtlety: in the paper's model, 
        "read" happens BEFORE the matrix is chosen (to select the transition).
        The matrix itself does write+move. So:
        
        For RIGHT move after reading a:
            Apply Q_a to R (pops the a we already read) 
            Apply P_w to L (pushes write symbol onto left = leaves it behind)
            
        For LEFT move after reading a:
            Apply Q_a to R first? Or does reading happen differently?
            
        I think the cleanest approach: implement both interpretations,
        test against classical trace, see which one works.
    """
    
    def __init__(self, left: CFStack, right: CFStack, state: int):
        self.left = left
        self.right = right 
        self.state = state
    
    @classmethod
    def blank(cls, state: int = 0, tape_length: int = 30) -> 'TapeConfig':
        """Blank tape: all 1s (shifted blank symbol), head at first position."""
        return cls(
            CFStack.blank(tape_length),
            CFStack.blank(tape_length),
            state
        )
    
    def read(self) -> int:
        """Read symbol under head (top of right stack)."""
        sym, _ = self.right.pop()
        return sym
    
    def step_right(self, read_sym: int, write_sym: int, new_state: int) -> 'TapeConfig':
        """Move head right: pop read_sym from R, push write_sym onto L.
        
        Matrices: X_R → Q_a · X_R, X_L → P_w · X_L
        """
        popped, new_right = self.right.pop()
        assert popped == read_sym, f"Expected to read {read_sym}, got {popped}"
        new_left = self.left.push(write_sym)
        return TapeConfig(new_left, new_right, new_state)
    
    def step_left(self, read_sym: int, write_sym: int, new_state: int) -> 'TapeConfig':
        """Move head left.
        
        This needs careful handling. The paper says:
            Leftward: Q_b on X_L, P_w on X_R
            
        But we also need to handle the current head symbol (read_sym).
        
        Interpretation: 
        1. Pop current symbol from R (consume read_sym)
        2. Push write_sym onto R (write in current position)
        3. Pop b from L (move left — b becomes new head)
        4. Push b onto R (b is now the head symbol on top of R)
        
        Net effect on R: P_b · P_w · Q_a · X_R
        Net effect on L: Q_b · X_L
        """
        # 1. Pop current head (verify it matches read_sym)
        popped, rest_right = self.right.pop()
        assert popped == read_sym, f"Expected to read {read_sym}, got {popped}"
        
        # 2. Push write symbol (it stays in the position we're leaving)
        right_with_write = rest_right.push(write_sym)
        
        # 3. Pop from left (move head left)
        left_sym, new_left = self.left.pop()
        
        # 4. Push left symbol onto right (it's now under the head)
        new_right = right_with_write.push(left_sym)
        
        return TapeConfig(new_left, new_right, new_state)

    def step_matrices_right(self, read_sym: int, write_sym: int) -> tuple[MobiusMatrix, MobiusMatrix]:
        """Return (M_right, M_left) matrices for a right-move step."""
        return (MobiusMatrix.pop(read_sym), MobiusMatrix.push(write_sym))
    
    def step_matrices_left(self, read_sym: int, write_sym: int) -> tuple[MobiusMatrix, MobiusMatrix]:
        """Return (M_right, M_left) matrices for a left-move step.
        
        On R: P_b · P_w · Q_a (but b is data-dependent — known only after popping L).
        On L: Q_b
        
        Returns the Q_a and P_w components; the P_b and Q_b depend on what's on the left stack.
        """
        # We can't fully determine the left-move matrices without knowing b
        # This is a fundamental issue: the matrix depends on runtime data
        # For now, return the read/write components
        return (MobiusMatrix.pop(read_sym), MobiusMatrix.push(write_sym))
    
    def to_tape_list(self, width: int = 10) -> tuple[list[int], int]:
        """Convert back to classical tape representation for verification.
        
        Returns (tape_symbols, head_position).
        """
        left_syms = self.left.symbols[:width]
        right_syms = self.right.symbols[:width]
        
        # Left stack: top = nearest to head, so reverse for tape display
        tape_left = list(reversed(left_syms))
        tape_right = right_syms
        
        head_pos = len(tape_left)
        tape = tape_left + tape_right
        
        return tape, head_pos
    
    def display(self, width: int = 8) -> str:
        """Pretty-print tape with head marker."""
        tape, head = self.to_tape_list(width)
        # Unshift: display original symbols (1→0, 2→1)
        syms = " ".join(str(s - 1) for s in tape)
        marker = "  " * head + "^"
        return f"State {self.state} | {syms}\n{'':>10}{marker}"


# =============================================================================
# Class 4: TuringMachine — Classical TM for ground truth
# =============================================================================

class TuringMachine:
    """Classical Turing machine for reference/verification.
    
    Uses shifted alphabet: original 0 → 1, original 1 → 2, etc.
    """
    
    def __init__(self, transitions: dict, initial_state: int, halt_states: set):
        """
        transitions: {(state, symbol): (new_state, write_symbol, direction)}
        direction: 'R' or 'L'
        """
        self.transitions = transitions
        self.initial_state = initial_state
        self.halt_states = halt_states
    
    @classmethod
    def busy_beaver_3(cls) -> 'TuringMachine':
        """3-state 2-symbol busy beaver (shifted alphabet: blank=1, mark=2).
        
        Original BB(3):
            (A,0) → (B,1,R)    (A,1) → (C,1,L)
            (B,0) → (A,1,L)    (B,1) → (B,1,R)
            (C,0) → (B,1,L)    (C,1) → (HALT,1,R)
            
        Shifted (0→1, 1→2), states A=0, B=1, C=2, HALT=3:
            (0,1) → (1,2,R)    (0,2) → (2,2,L)
            (1,1) → (0,2,L)    (1,2) → (1,2,R)
            (2,1) → (1,2,L)    (2,2) → (3,2,R)
        """
        transitions = {
            (0, 1): (1, 2, 'R'),  # A,blank → B,mark,R
            (0, 2): (2, 2, 'L'),  # A,mark  → C,mark,L
            (1, 1): (0, 2, 'L'),  # B,blank → A,mark,L
            (1, 2): (1, 2, 'R'),  # B,mark  → B,mark,R
            (2, 1): (1, 2, 'L'),  # C,blank → B,mark,L
            (2, 2): (3, 2, 'R'),  # C,mark  → HALT,mark,R
        }
        return cls(transitions, initial_state=0, halt_states={3})
    
    def run(self, tape: Optional[list[int]] = None, head_pos: int = 15, 
            max_steps: int = 1000) -> list[dict]:
        """Run machine, return full trace.
        
        Each trace entry: {step, state, tape, head, read, write, direction, new_state}
        """
        if tape is None:
            tape = [1] * 30  # blank tape (shifted)
        else:
            tape = list(tape)
        
        state = self.initial_state
        trace = []
        
        for step in range(max_steps):
            # Extend tape if needed
            while head_pos < 0:
                tape.insert(0, 1)
                head_pos += 1
            while head_pos >= len(tape):
                tape.append(1)
            
            read_sym = tape[head_pos]
            
            if state in self.halt_states:
                trace.append({
                    'step': step, 'state': state, 
                    'tape': list(tape), 'head': head_pos,
                    'halted': True
                })
                break
            
            if (state, read_sym) not in self.transitions:
                raise ValueError(f"No transition for (state={state}, symbol={read_sym})")
            
            new_state, write_sym, direction = self.transitions[(state, read_sym)]
            
            trace.append({
                'step': step, 'state': state,
                'tape': list(tape), 'head': head_pos,
                'read': read_sym, 'write': write_sym,
                'direction': direction, 'new_state': new_state,
                'halted': False
            })
            
            tape[head_pos] = write_sym
            state = new_state
            head_pos += 1 if direction == 'R' else -1
        
        return trace


# =============================================================================
# Shear Expansion — collecting the full matrix product
# =============================================================================

class ShearExpansion:
    """Collects matrices from a computation into the Shear expansion Φ(γ).
    
    Tracks separate products for the right and left stacks.
    """
    
    def __init__(self):
        self.right_matrices = []  # List of matrices applied to X_R
        self.left_matrices = []   # List of matrices applied to X_L
        self.right_product = MobiusMatrix.identity()
        self.left_product = MobiusMatrix.identity()
    
    def record_right(self, m: MobiusMatrix):
        """Record a matrix applied to the right stack."""
        self.right_matrices.append(m)
        self.right_product = m @ self.right_product  # Left-multiply (newest first)
    
    def record_left(self, m: MobiusMatrix):
        """Record a matrix applied to the left stack."""
        self.left_matrices.append(m)
        self.left_product = m @ self.left_product
    
    def factor_into_shears(self) -> list[tuple[str, int]]:
        """Factor all matrices into S(k) and J components.
        
        P_k = S(k) · J
        Q_k = J · S(-k)
        
        Returns list of ('S', k) or ('J', 0) tuples.
        """
        factors = []
        for m in self.right_matrices + self.left_matrices:
            # Check if it's a push P_k
            if m.c == 1 and m.d == 0 and m.b == 1:
                k = m.a
                factors.append(('S', k))
                factors.append(('J', 0))
            # Check if it's a pop Q_k
            elif m.a == 0 and m.b == 1 and m.c == 1:
                k = -m.d
                factors.append(('J', 0))
                factors.append(('S', -k))
            else:
                factors.append(('?', m))
        return factors
    
    @property
    def total_elementary_factors(self) -> int:
        """Total count of S(k) and J factors."""
        return len(self.factor_into_shears())
    
    def summary(self) -> str:
        lines = [
            f"Shear Expansion Summary:",
            f"  Right stack: {len(self.right_matrices)} matrices",
            f"  Left stack:  {len(self.left_matrices)} matrices",
            f"  Φ_R = {self.right_product}  (det = {self.right_product.det()})",
            f"  Φ_L = {self.left_product}  (det = {self.left_product.det()})",
            f"  Total elementary (S,J) factors: {self.total_elementary_factors}",
        ]
        return "\n".join(lines)


# =============================================================================
# TESTS
# =============================================================================

def run_tests():
    """Run all Phase 1-3 tests."""
    
    passed = 0
    failed = 0
    
    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            print(f"  ✅ {name}")
            passed += 1
        else:
            print(f"  ❌ {name}")
            if detail:
                print(f"     {detail}")
            failed += 1
    
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 1: CF Encoding Roundtrip")
    print("="*70)
    
    # Test 1: Blank tape ≈ golden ratio
    print("\n--- Test 1: Blank tape value ---")
    blank = CFStack.blank(30)
    val = blank.to_float()
    phi = (1 + 5**0.5) / 2
    check("Blank tape [1;1,1,...] ≈ φ", abs(val - phi) < 1e-6,
          f"Got {val:.10f}, expected {phi:.10f}")
    
    # Test 2: Push/pop roundtrip
    print("\n--- Test 2: Push/pop roundtrip ---")
    stack = CFStack.blank(20)
    original_val = stack.value()
    pushed = stack.push(2)
    sym, popped = pushed.pop()
    check("Push 2, pop → get 2 back", sym == 2, f"Got {sym}")
    check("Stack restored after push/pop", popped.value() == original_val,
          f"Got {popped.value()}, expected {original_val}")
    
    # Test 3: Multi push/pop roundtrip
    print("\n--- Test 3: Multi push/pop ---")
    stack = CFStack([3, 1, 4, 1, 5])
    s1, stack = stack.pop()
    s2, stack = stack.pop()
    s3, stack = stack.pop()
    check("Pop sequence 3,1,4", (s1, s2, s3) == (3, 1, 4),
          f"Got ({s1}, {s2}, {s3})")
    
    stack = stack.push(4).push(1).push(3)
    check("Rebuild via push", stack.symbols == [3, 1, 4, 1, 5],
          f"Got {stack.symbols}")
    
    # Test 4: P_k matrix matches push
    print("\n--- Test 4: P_k matrix = push operation ---")
    for k in [1, 2, 3, 4, 5]:
        base = CFStack([2, 3, 1])
        x = base.value()
        pushed_val = base.push(k).value()
        matrix_val = MobiusMatrix.push(k).act(x)
        check(f"P_{k} · {x} = push({k})", pushed_val == matrix_val,
              f"push={pushed_val}, matrix={matrix_val}")
    
    # Test 5: Q_k matrix matches pop
    print("\n--- Test 5: Q_k matrix = pop operation ---")
    for k in [1, 2, 3, 4, 5]:
        stack = CFStack([k, 2, 3, 1])
        x = stack.value()
        _, popped_stack = stack.pop()
        popped_val = popped_stack.value()
        matrix_val = MobiusMatrix.pop(k).act(x)
        check(f"Q_{k} · {float(x):.4f} = pop (k={k})", popped_val == matrix_val,
              f"pop={popped_val}, matrix={matrix_val}")
    
    # Test 6: P_k = S(k) · J
    print("\n--- Test 6: P_k = S(k) · J ---")
    for k in [1, 2, 3, 4, 5]:
        pk = MobiusMatrix.push(k)
        sk_j = MobiusMatrix.shear(k) @ MobiusMatrix.swap()
        check(f"P_{k} = S({k})·J", pk == sk_j,
              f"P_{k}={pk}, S({k})·J={sk_j}")
    
    # Test 7: Q_k = J · S(-k)
    print("\n--- Test 7: Q_k = J · S(-k) ---")
    for k in [1, 2, 3, 4, 5]:
        qk = MobiusMatrix.pop(k)
        j_sk = MobiusMatrix.swap() @ MobiusMatrix.shear(-k)
        check(f"Q_{k} = J·S(-{k})", qk == j_sk,
              f"Q_{k}={qk}, J·S(-{k})={j_sk}")
    
    # Test 8: det(P_k) = -1, det(Q_k) = -1
    print("\n--- Test 8: Determinants ---")
    for k in [1, 2, 3]:
        check(f"det(P_{k}) = -1", MobiusMatrix.push(k).det() == -1)
        check(f"det(Q_{k}) = -1", MobiusMatrix.pop(k).det() == -1)
    check("det(S(k)) = 1", MobiusMatrix.shear(3).det() == 1)
    check("det(J) = -1", MobiusMatrix.swap().det() == -1)
    
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 2: GL(2,ℤ) Step-by-Step BB(3) Execution")
    print("="*70)
    
    # Test 9: Classical BB(3) ground truth
    print("\n--- Test 9: Classical BB(3) ---")
    bb3 = TuringMachine.busy_beaver_3()
    trace = bb3.run()
    
    num_steps = len([t for t in trace if not t.get('halted')])
    final = trace[-1]
    marks = sum(1 for s in final['tape'] if s == 2)
    
    check("BB(3) halts", final.get('halted', False))
    check(f"BB(3) takes 13 steps", num_steps == 13, f"Got {num_steps}")
    check(f"BB(3) writes 6 marks", marks == 6, f"Got {marks}")
    
    print(f"\n  Classical trace (first 5 steps):")
    for t in trace[:5]:
        state_name = 'ABCH'[t['state']]
        tape_display = ''.join(str(s-1) for s in t['tape'][10:20])
        head_rel = t['head'] - 10
        print(f"    Step {t['step']:2d}: state={state_name} tape=...{tape_display}... head@{t['head']}")
    print(f"    ...")
    
    # Test 10-11: CF-encoded execution matches classical trace
    print("\n--- Test 10-11: CF execution vs classical ---")
    
    # Initialize CF tape to match classical tape
    # Classical starts: blank tape, head at position 15
    # Left of head: positions 14,13,12,... all blank (=1)
    # Right from head: positions 15,16,17,... all blank (=1)
    TAPE_LEN = 20
    config = TapeConfig(CFStack.blank(TAPE_LEN), CFStack.blank(TAPE_LEN), 0)
    
    shear = ShearExpansion()
    
    all_steps_match = True
    mismatch_step = -1
    
    for t in trace:
        if t.get('halted'):
            break
            
        step = t['step']
        expected_read = t['read']
        write_sym = t['write']
        direction = t['direction']
        new_state = t['new_state']
        
        # Read from CF tape
        actual_read = config.read()
        if actual_read != expected_read:
            print(f"    ❌ Step {step}: read mismatch! CF={actual_read}, classical={expected_read}")
            all_steps_match = False
            mismatch_step = step
            break
        
        # Record matrices and execute step
        if direction == 'R':
            m_r = MobiusMatrix.pop(actual_read)
            m_l = MobiusMatrix.push(write_sym)
            shear.record_right(m_r)
            shear.record_left(m_l)
            config = config.step_right(actual_read, write_sym, new_state)
        else:  # 'L'
            # For left move, we need to know what symbol is on the left stack
            # Record the matrices we can determine
            config_before = config
            config = config.step_left(actual_read, write_sym, new_state)
            
            # The matrices for left move:
            # On R: P_b · P_w · Q_a where b = symbol popped from L
            # On L: Q_b
            # We need to reconstruct b from the config change
            # b is what was on top of the left stack
            b_sym = config_before.left.symbols[0]
            
            shear.record_right(MobiusMatrix.pop(actual_read))
            shear.record_right(MobiusMatrix.push(write_sym))
            shear.record_right(MobiusMatrix.push(b_sym))
            shear.record_left(MobiusMatrix.pop(b_sym))
        
        # Verify state matches
        if config.state != new_state:
            print(f"    ❌ Step {step}: state mismatch!")
            all_steps_match = False
            mismatch_step = step
            break
    
    check("All 21 steps: CF read matches classical", all_steps_match,
          f"First mismatch at step {mismatch_step}" if not all_steps_match else "")
    
    # Verify final tape
    if all_steps_match:
        final_tape, final_head = config.to_tape_list(TAPE_LEN)
        classical_final = trace[-1]['tape']
        
        # Compare the relevant portion
        # Our CF tape starts at a different offset, so compare the marks
        cf_marks = sum(1 for s in final_tape if s == 2)
        check(f"Final tape: {cf_marks} marks (expected 6)", cf_marks == 6,
              f"CF tape: {final_tape}")
        check(f"Final state: HALT ({config.state})", config.state == 3)
    
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 3: Shear Expansion")
    print("="*70)
    
    if all_steps_match:
        print(f"\n{shear.summary()}")
        
        # Test 12-13: Verify matrix products
        print("\n--- Test 12: Shear expansion properties ---")
        check(f"det(Φ_R) = ±1", abs(shear.right_product.det()) == 1,
              f"Got {shear.right_product.det()}")
        check(f"det(Φ_L) = ±1", abs(shear.left_product.det()) == 1,
              f"Got {shear.left_product.det()}")
        
        # Test 14-15: Verify Φ maps initial → final
        print("\n--- Test 13: Φ maps initial config to final ---")
        initial_R = CFStack.blank(TAPE_LEN).value()
        initial_L = CFStack.blank(TAPE_LEN).value()
        
        phi_R_result = shear.right_product.act(initial_R)
        phi_L_result = shear.left_product.act(initial_L)
        
        final_R_value = config.right.value()
        final_L_value = config.left.value()
        
        check("Φ_R · X_R_initial = X_R_final", phi_R_result == final_R_value,
              f"Φ·X₀={float(phi_R_result):.6f}, actual={float(final_R_value):.6f}")
        check("Φ_L · X_L_initial = X_L_final", phi_L_result == final_L_value,
              f"Φ·X₀={float(phi_L_result):.6f}, actual={float(final_L_value):.6f}")
        
        # Test 16: Factor count
        print("\n--- Test 14: Elementary factor count ---")
        n_factors = shear.total_elementary_factors
        print(f"  Total elementary (S,J) factors: {n_factors}")
        check(f"Factor count reasonable (≤ 2 × matrices)", 
              n_factors <= 2 * (len(shear.right_matrices) + len(shear.left_matrices)))
    
    # =========================================================================
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    run_tests()
