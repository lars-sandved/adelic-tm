# Task: Implement Emmett's Möbius-Shear Framework (Phase 1-3)

Build a reusable Python library implementing the core building blocks from Emmett Shear's paper "Möbius Transformations on the Adeles as Computational Steps." Each component should be independently testable with clear assertions.

## Architecture

Create `mobius_shear.py` — a single-file library with clean classes:

### Class 1: `CFStack`
Encodes a stack of symbols as a continued fraction.

```python
class CFStack:
    """A stack of positive integer symbols encoded as a continued fraction.
    
    The stack [a₀, a₁, a₂, ...] encodes as the CF [a₀; a₁, a₂, ...].
    All symbols must be ≥ 1.
    """
    
    def __init__(self, symbols: list[int]):
        """Create from explicit symbol list. Validates all ≥ 1."""
        
    def push(self, k: int) -> 'CFStack':
        """Push symbol k onto stack. X → k + 1/X. Returns new CFStack."""
        
    def pop(self) -> tuple[int, 'CFStack']:
        """Pop top symbol. Returns (symbol, remaining_stack).
        Uses Gauss map: k = floor(X), remainder = 1/(X - k).
        """
        
    def to_float(self) -> float:
        """Evaluate the CF as a float (for verification)."""
        
    def to_matrix(self) -> np.ndarray:
        """Return the convergent matrix product: ∏ P_{aᵢ}."""
        
    @property
    def symbols(self) -> list[int]:
        """Return the symbol list."""
        
    def __repr__(self):
        """Show as [a₀; a₁, a₂, ...]"""
```

Key implementation details:
- Use `fractions.Fraction` for EXACT arithmetic (not floats!) to avoid rounding issues with the Gauss map
- The CF value of [a₀; a₁, ...] = a₀ + 1/(a₁ + 1/(a₂ + ...))
- Push k: prepend k to symbols (equivalently, X_new = k + 1/X_old)
- Pop: remove first symbol (equivalently, k = symbols[0], X_new = 1/(X_old - k))
- Blank tape = infinite sequence of 1s. For practical purposes, use a finite list (e.g., 50 ones)

### Class 2: `MobiusMatrix`
A 2×2 integer matrix representing a Möbius transformation.

```python
class MobiusMatrix:
    """A 2×2 integer matrix acting as a Möbius transformation.
    
    The matrix [[a,b],[c,d]] acts on x as (ax + b)/(cx + d).
    """
    
    def __init__(self, a, b, c, d):
        """Create from four integers."""
        
    @staticmethod
    def push(k: int) -> 'MobiusMatrix':
        """P_k = ((k,1),(1,0)) — push symbol k onto CF stack."""
        
    @staticmethod
    def pop(k: int) -> 'MobiusMatrix':
        """Q_k = ((0,1),(1,-k)) — pop symbol k from CF stack."""
        
    @staticmethod
    def shear(k: int) -> 'MobiusMatrix':
        """S(k) = ((1,k),(0,1)) — upper shear matrix."""
        
    @staticmethod
    def swap() -> 'MobiusMatrix':
        """J = ((0,1),(1,0)) — swap matrix. J² = I."""
        
    @staticmethod
    def identity() -> 'MobiusMatrix':
        """I = ((1,0),(0,1))."""
        
    def __matmul__(self, other: 'MobiusMatrix') -> 'MobiusMatrix':
        """Matrix multiplication."""
        
    def act(self, x: Fraction) -> Fraction:
        """Apply Möbius transformation: x → (ax + b)/(cx + d)."""
        
    def det(self) -> int:
        """Determinant ad - bc."""
        
    def factor(self) -> list:
        """Factor into S(k) and J components. Returns list of (type, k) tuples."""
        
    def __repr__(self):
        """Show as [[a,b],[c,d]]"""
```

### Class 3: `TapeConfig`
A full tape configuration: left stack + right stack + state.

```python
class TapeConfig:
    """A Turing machine tape configuration.
    
    Left stack: symbols to the left of head (top = nearest to head)
    Right stack: symbols to the right of head (top = symbol under head)  
    State: current machine state
    """
    
    def __init__(self, left: CFStack, right: CFStack, state: int):
        pass
        
    @classmethod
    def blank(cls, state: int = 0, blank_symbol: int = 1, tape_length: int = 50):
        """Create blank tape. Blank = symbol 1 (shifted from 0)."""
        
    def read(self) -> int:
        """Read symbol under head (top of right stack)."""
        
    def write_and_move(self, write_sym: int, direction: str) -> 'TapeConfig':
        """Execute one TM step: write symbol, move head.
        
        For right move:
            1. Pop from right stack (reads current symbol)
            2. Push write_sym onto left stack
            3. Return new config
            
        For left move:
            1. Pop from right stack (reads current, discards)
            2. Push write_sym onto right stack (write in place)
            ... actually:
            
        Wait — let me be precise about the encoding:
        
        Move RIGHT (read a, write w):
            - Pop a from X_R (verify a matches expected)
            - Push w onto X_L
            - Head now points to new top of X_R
            
        Move LEFT (read a, write w):
            - Pop a from X_R (verify a matches expected)
            - Push w onto... hmm.
            
        Actually, the paper's encoding:
        - X_R = [head_symbol; symbols_to_right...]
        - X_L = [symbol_left_of_head; symbols_further_left...]
        
        Move RIGHT (read a from head, write w):
            - Pop a from X_R (removes head symbol)
            - Push w onto X_L (writes w where head was)
            - New head symbol = top of X_R (moved right)
            
        Move LEFT (read a from head, write w):  
            - Pop a from X_R (removes head symbol)
            - Pop b from X_L (this will be new head position)
            - Push w onto X_R (writes w where head was, it's now to the right)
            - Push b onto X_R (b is now under the head)
            
        Hmm, that's not right either. Let me re-read the paper:
        
        The paper says:
        - Rightward move (read a, write w): Pop a from X_R, push w onto X_L
        - Leftward move (read b from left, write w): Pop b from X_L, push w onto X_R
        
        But this doesn't handle writing! When moving right:
        - We read a from head position (pop from X_R)
        - We write w at the old head position (push onto X_L, which is now to the left of new head)
        - Head moves to next position on right (new top of X_R)
        
        When moving left:
        - We need to write at current position AND read from left
        - Pop current symbol from X_R, push write symbol onto X_R... 
        
        Actually the paper's description is for the HALF-STEP. A full TM step involves:
        1. Read: pop from X_R to get current symbol
        2. Write + Move Right: push write symbol onto X_L (it stays behind as head moves right)
        OR
        2. Write + Move Left: push write symbol onto X_R (it stays behind), pop from X_L (new head pos), push that onto X_R
        
        Let me just implement what the paper says literally:
        
        Right move: X_R' = Q_a · X_R, X_L' = P_w · X_L
        Left move: X_L' = Q_b · X_L, X_R' = P_w · X_R
        
        But wait — for left move, what about writing at the current position? 
        
        I think the answer is: the paper assumes the write symbol replaces during the move.
        For left move (read current a, write w, move left):
            Step 1: Pop a from X_R (removes current symbol)
            Step 2: Push w onto X_R (puts write symbol where we were — now to right of new head)
            Step 3: Pop b from X_L (reveals new head position)
            ... but the paper says just: Pop b from X_L, push w onto X_R
            
        I think the full left move is actually:
            X_R' = P_w · Q_a · X_R (pop a, push w — replaces head symbol)
            X_L' = Q_b · X_L (pop b — b is new head symbol, but where does it go?)
            
        This needs careful thought. For now, implement EXACTLY what the paper says and verify with the classical trace.
        """
```

### Class 4: `TuringMachine`
Classical TM for ground truth comparison.

```python
class TuringMachine:
    """Classical Turing machine for reference/verification."""
    
    def __init__(self, transitions: dict, initial_state, halt_states: set):
        """
        transitions: {(state, symbol): (new_state, write_symbol, direction)}
        direction: 'R' or 'L'
        """
        
    def run(self, tape: list[int], head_pos: int, max_steps: int = 1000) -> list[dict]:
        """Run and return full trace: list of {state, tape, head, step}."""
        
    @classmethod 
    def busy_beaver_3(cls):
        """The 3-state 2-symbol busy beaver.
        
        Uses shifted alphabet: blank=1, mark=2.
        States: 0=A, 1=B, 2=C, 3=HALT.
        
        Standard BB(3) transitions (shifted to 1-indexed symbols):
        (A, blank=1) -> (B, mark=2, R)
        (A, mark=2)  -> (C, mark=2, L) -- actually check the standard definition
        ...
        
        Look up the STANDARD BB(3) definition:
        (A,0) -> (B,1,R)
        (A,1) -> (C,1,L)
        (B,0) -> (A,1,L)
        (B,1) -> (B,1,R)
        (C,0) -> (B,1,L)
        (C,1) -> (HALT,1,R)
        
        After shifting (0->1, 1->2):
        (A,1) -> (B,2,R)
        (A,2) -> (C,2,L)
        (B,1) -> (A,2,L)
        (B,2) -> (B,2,R)
        (C,1) -> (B,2,L)
        (C,2) -> (HALT,2,R)  -- HALT = state 3
        
        Should write 6 twos (=ones in original encoding) and halt in 21 steps.
        """
```

## Tests (in the same file, at the bottom)

Write comprehensive tests as a `if __name__ == "__main__":` block:

### Phase 1 Tests: CF Encoding Roundtrip
```
1. Create CFStack([1,1,1,...]) — blank tape. Verify value ≈ φ (golden ratio)
2. Push symbol 2 onto blank stack. Pop it back. Verify we get 2 and the original stack.
3. Push 3, push 1, push 4. Pop 4, pop 1, pop 3. Verify roundtrip.
4. Verify P_k matrix produces same result as push operation.
5. Verify Q_k matrix produces same result as pop operation.
6. Test: P_k factors as S(k) · J. Verify for k = 1,2,3,4,5.
7. Test: Q_k factors as J · S(-k). Verify for k = 1,2,3,4,5.
```

### Phase 2 Tests: GL(2,Z) Step Execution
```
8. Run BB(3) classically. Verify: 21 steps, 6 marks, halts.
9. Encode BB(3) initial tape as TapeConfig (blank tape, state A).
10. For each of the 21 steps:
    a. Read symbol from right stack (verify matches classical trace)
    b. Construct the correct P_k and Q_k matrices for this step
    c. Apply matrices to CF stacks
    d. Verify new tape state matches classical trace
11. After all 21 steps, verify final tape matches classical result.
```

### Phase 3 Tests: Shear Expansion
```
12. Collect all matrices from the 21 steps into a list.
13. Compute Φ(γ) = product of all matrices (for each stack separately).
14. Verify: Φ_R applied to initial X_R gives final X_R.
15. Verify: Φ_L applied to initial X_L gives final X_L.
16. Factor Φ into S(k)·J components. Count total elementary factors.
17. Verify det(Φ) = ±1.
```

## Implementation Notes

- **Use `fractions.Fraction` everywhere** for exact arithmetic. Floats will break the Gauss map.
- **Use numpy only for matrix display if needed.** Core math should be Fraction-based.
- **Print clear, readable output** for each test. Include the matrices, the CF values, and comparison with expected.
- **Every test should print PASS/FAIL** with details on failure.
- **Handle the tape encoding carefully.** The move-left operation needs special attention — verify against classical trace at every step.

## What NOT to do
- Don't implement the CRT selector yet (that's Phase 4, later)
- Don't use floating-point arithmetic for CF operations
- Don't skip tests — every building block must be independently verified
- Don't import heavy dependencies (just fractions, typing, maybe numpy for display)
