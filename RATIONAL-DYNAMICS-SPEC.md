# Rational Dynamics Spec: Toward α^n = n Steps

**Status:** Research spec / theoretical roadmap  
**Date:** 2026-02-27  
**Goal:** Make the adelic structure do actual computational work, not just storage.

---

## The Problem With What We Have

Our current implementation stores TM configurations in an adele:
- α₂ ∈ ℤ₂ = right tape  
- α₃ ∈ ℤ₃ = left tape  
- α₂₃ ∈ ℤ₂₃ = state  
- α_∞ ∈ ℝ = step counter

But these components are **independent**. They don't interact through
the adelic structure. The branching logic (which transition to apply)
lives in a Python dict lookup. The adele is a filing cabinet, not a
calculator.

For the adelic structure to do computational work, we need:
1. Components that **interact** via the ring structure
2. The **product formula** (∏|α|_v = 1) acting as a constraint
3. **Exponentiation or iteration** of a fixed algebraic operation

## The Proposal: Rational Function Dynamics

### Core Idea

Encode the TM configuration as a single rational number x ∈ ℚ.
The transition function is a rational map T: ℚ → ℚ defined by
T(x) = P(x)/Q(x) where P, Q are polynomials with integer coefficients.

Then:
- **One step** of computation = T(x)
- **n steps** = T^n(x) = T(T(...T(x)...))
- **Every prime sees the same x**, but through its own p-adic lens
- The product formula constrains how information flows between primes

### Why This Is Genuinely Adelic

When x ∈ ℚ and T(x) = P(x)/Q(x), the transformation is **simultaneously**
an operation in every completion:

```
x ∈ ℚ ↪ ℝ      →  T acts on x as a real number
x ∈ ℚ ↪ ℚ₂     →  T acts on x as a 2-adic number
x ∈ ℚ ↪ ℚ₃     →  T acts on x as a 3-adic number
...
```

The SAME rational map T, applied to the SAME rational x, is simultaneously
doing different things at different primes. The product formula

    ∏_v |T(x)|_v = ∏_v |P(x)/Q(x)|_v = ∏_v |P(x)|_v / ∏_v |Q(x)|_v

constrains the dynamics: if T(x) grows at one place, it must shrink at another.

This is the "spinning up and down the solenoid" that Emmett describes.

## Concrete Construction

### Step 1: Gödel-Style Configuration Encoding

Encode a TM configuration (state s, tape, head position h) as a rational:

    x = 2^a · 3^b · 5^c · 7^d · ...

where the exponents encode the configuration. For a binary TM:

    x = p_state^s · p_head^h · ∏_i p_tape_i^{tape[i]}

For example, with primes assigned:
- p = 2: encodes tape cell 0
- p = 3: encodes tape cell 1
- p = 5: encodes tape cell 2
- ...
- p_k: encodes tape cell k
- p_state = next prime: encodes state
- p_head = next prime: encodes head position

So the configuration (state=2, tape=[1,0,1,1,0], head=1) becomes:

    x = 2^1 · 3^0 · 5^1 · 7^1 · 11^0 · 13^2 · 17^1
      = 2 · 1 · 5 · 7 · 1 · 169 · 17
      = 200,410

The p-adic valuation v_p(x) at each prime READS the corresponding part
of the configuration:
- v₂(x) = 1 → tape[0] = 1
- v₃(x) = 0 → tape[1] = 0
- v₅(x) = 1 → tape[2] = 1
- v₁₃(x) = 2 → state = 2
- v₁₇(x) = 1 → head at position 1

### Step 2: Transition as Rational Multiplication

For a specific transition δ(s, σ) = (s', σ', d), we need a rational r
such that x' = r · x correctly updates the configuration.

**Reading the current symbol:** The symbol at the head is v_{p_head_cell}(x).
But the head moves, so "the cell under the head" changes. This is the tricky part.

**Simpler variant — fixed head, moving tape:** Equivalently, keep the head
at a fixed position and shift the tape. Then:

- **Write σ' to current cell (prime p_curr):** 
  Multiply by p_curr^(σ' - σ) — this changes the exponent from σ to σ'.
  
- **Shift tape left (head moves right):**
  We need to relabel: what was cell i+1 is now cell i.
  This is a permutation of primes, which can't be done by multiplication alone.

**The fundamental obstacle:** Rational multiplication changes exponents
(valuations) at fixed primes. But TM head movement requires *relabeling*
which primes correspond to which tape cells. Multiplication can't permute primes.

### Step 3: Working Around the Relabeling Problem

**Option A: Fixed-width tape with modular addressing**

For a tape of width N, encode the tape as a single number at ONE prime:

    α₂ = tape[0] + tape[1]·2 + tape[2]·4 + ... (this is our current approach)

Then the head position h determines which "digit" we're looking at.
Reading = extracting a digit. Writing = modifying a digit.

This brings us back to p-adic digit manipulation, but now with the key
difference that T is a fixed rational function of BOTH α₂ and the state.

**Option B: Collatz-style dynamics**

The Collatz map is: if n is even, n→n/2; if n is odd, n→3n+1.
The branching (even/odd) is determined by v₂(n): if v₂(n) > 0, divide by 2.

This is a TM-like conditional implemented as a rational operation!
The "if even" branch = "if v₂(x) > 0" = reading the least significant
2-adic digit.

Generalize: a "Collatz-style TM" is a map of the form:

    T(x) = (a_i · x + b_i) / c_i   when x ≡ i (mod m)

The residue x mod m selects which branch to take. This IS p-adic:
x mod m is determined by the m-adic (or p-adic for prime m) expansion.

For a 2-symbol TM with k states, we can encode:
- Tape in the 2-adic expansion of x (low-order bits)
- State in x mod (2k+1) or similar

The transition becomes:
    
    T(x) = (a_r · x + b_r) / d_r   where r = x mod M

with M chosen so that x mod M encodes (state, current_symbol).

**This is genuinely algebraic branching.** The "if" is replaced by
modular arithmetic, which IS p-adic structure. Different residue
classes → different linear maps. But they're all part of ONE function T.

**Option C: Polynomial interpolation**

Given a finite set of (input, output) pairs from the transition table,
there exists a unique polynomial T(x) passing through all of them
(Lagrange interpolation). This T is a single function that "branches"
by being designed to give the right output for each input.

The problem: the polynomial may have very high degree, and its behavior
on non-configuration values is unpredictable. Also, intermediate
compositions T^n may explode in degree.

### Step 4: The Collatz Construction in Detail

This is the most promising direction. Here's how it works concretely.

**Setup:** A TM with states {0, 1, ..., k-1} and symbols {0, 1}.

**Encoding:** x ∈ ℤ encodes (state, tape) as:

    x = state + k · (tape as binary integer)

So the low-order "digits" in base k encode the state, and the rest
(shifted by k) encode the tape.

More precisely, using a mixed-radix representation:
- x mod k = state
- x mod 2k = (state, current_symbol)  ... almost
  
Actually, cleaner: Let M = 2k (or next convenient modulus).

    x = tape_integer · M + (k · current_symbol + state)

Then:
- x mod M gives (state, symbol) → determines which transition to apply
- x ÷ M (integer division) gives the rest of the tape

Each transition δ(s, σ) = (s', σ', d) becomes a linear-fractional map:

    T_r(x) = (a_r · x + b_r) / M

where r = k·σ + s, and a_r, b_r are chosen so that:
1. The new low-order part encodes (s', next_symbol)
2. The written symbol σ' replaces σ at the correct position
3. The tape shifts appropriately for head movement

The full map:

    T(x) = T_r(x)  where r = x mod M

This is a **single piecewise-linear function** that branches based on
x mod M — which is exactly the p-adic structure at primes dividing M.

### Step 5: What the Adelic View Gives You

For this Collatz-style T:

**At p | M (primes dividing the modulus):** These primes "see" the state
and current symbol. The p-adic expansion of x at these primes contains
the control information.

**At p = 2 (if 2 ∤ M):** This prime "sees" the tape contents. The 2-adic
expansion is the binary tape.

**At p = ∞ (real place):** |T^n(x)|_∞ tracks the growth of the tape —
whether the computation is expanding or contracting.

**The product formula:** If T(x) = (ax+b)/M, then

    |T(x)|_v ≈ |a|_v · |x|_v / |M|_v

The product formula forces: what M "takes away" at primes p | M
(reading the state) must be "given back" at other primes (writing
to the tape). Information conservation!

**This is the solenoid:** The integer lattice ℤ ⊂ ℚ sits inside the
adelic solenoid ℚ\𝔸_ℚ. The dynamics T: ℚ → ℚ lifts to dynamics on
the solenoid. "Spinning up and down" = the orbit of x under T projected
to different completions.

### Step 6: Implementation Plan

1. **Start with the binary incrementer.**
   Encoding: x = tape_as_integer · 2 + state (state ∈ {0, 1}).
   T₀(x) = (x - 0) / 2 + 2^N       (state 0, symbol 0: write 1, halt → just +1 effectively)
   T₁(x) = (x - 1) / 2 · 2 + 0     (state 0, symbol 1: write 0, carry)
   
   Verify T^n(x₀) gives the correct final configuration.

2. **Then the busy beaver.**
   Encoding: x = tape · 6 + (3·symbol + state), M=6, k=4 (3 states + halt).
   Design T_r for each r ∈ {0,...,5}.
   Verify T^14(x₀) gives 6 ones.

3. **Then U18,2.**
   M = 36 (18 states × 2 symbols).
   T_r for each of the 33 defined transitions.
   Show the same T works for all four bi-tag encodings.

4. **Adelic analysis.**
   For each step, compute:
   - v_p(T^n(x)) at relevant primes → watch the valuations evolve
   - |T^n(x)|_∞ → watch the real magnitude (tape size)
   - ∏|T^n(x)|_v → verify product formula conservation
   - Project the orbit onto the 2-adic solenoid → visualize

## What This Would Prove

If implemented:

1. **T^n(x) genuinely computes** — a single algebraic object (the rational
   map T), iterated n times, performs n TM steps. No external lookup table.

2. **The adelic structure is doing the branching** — the modular reduction
   x mod M (a p-adic operation at primes dividing M) selects which branch
   of T to apply. The "if-then-else" is number theory.

3. **The product formula is a conservation law** — information (as measured
   by p-adic valuations) flows between primes but is never created or destroyed.

4. **Universality of T** — for U18,2, the SAME rational map T handles any
   input (any encoded bi-tag system), because the transition table is baked
   into T's definition. Different inputs = different starting x, same T.

## Connection to Emmett's α^n

Emmett says: "the Adele α^n is executed for n-1 timesteps."

In this framework:
- α is not an adele per se, but a rational map T (or equivalently, the pair
  (a, M) defining the piecewise-linear map)
- x₀ ∈ ℚ is the initial configuration
- T^n(x₀) is the configuration after n steps
- The adelic VIEW of T^n(x₀) — looking at it at each prime — reveals
  different aspects of the computation simultaneously

If we want a single adele α such that α^n IS the answer: consider
the map T(x) = αx for a carefully chosen α. Then T^n(x) = α^n · x.
This only works if the transition is pure multiplication (no additive
constant). The incrementer case: adding 1 in ℤ₂ isn't multiplication,
it's translation. But in the p-adic GROUP, translation can be conjugated
to multiplication by a careful change of coordinates...

This is where it gets deep and connects to Iwasawa theory. For now,
the Collatz-style piecewise-linear approach is the concrete path forward.

## Open Questions

1. Does the orbit {T^n(x₀)} have interesting p-adic analytic structure?
   (Is there a p-adic power series that interpolates the orbit?)

2. For universal T (encoding U18,2), what does the real magnitude |T^n(x)|_∞
   tell us about the computation? (Halting = orbit stays bounded?)

3. Can the piecewise-linear map T be "smoothed" to a single polynomial
   or rational function? (At the cost of higher degree, but gaining algebraic
   unity.)

4. What is adelic gradient descent in this picture? (Minimizing some function
   f(x) where the gradient is computed adelically — step in ℝ, project back
   to ℚ via the product formula?)
