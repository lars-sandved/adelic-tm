# Adelic–Turing Machine Correspondence: Proof of Principle

**Status:** Draft spec for discussion with Emmett
**Date:** 2026-02-27
**Goal:** Concrete encoding of a small TM as adelic operations, then test whether α^n faithfully reproduces n steps of computation.

---

## 1. The Claim to Test

**Weak claim (trivial):** Any TM can be simulated by arithmetic, hence by adelic arithmetic.
**Strong claim (interesting):** The adelic structure *naturally* encodes TM computation — the decomposition into primes corresponds to something meaningful about the computation, and universality is visible in the adelic structure.

We want evidence for the strong claim.

## 2. Choice of Test Machine

Per Emmett's recommendations:

| Machine | States | Symbols | Type | Notes |
|---------|--------|---------|------|-------|
| (2,3) | 2 | 3 | Weakly universal | Simplest known UTM (Smith 2007). Needs infinite non-blank background. |
| (6,2) | 6 | 2 | Weakly universal, reversible | Good for testing since reversibility ↔ invertible adelic operation |
| **(15,2)** | **15** | **2** | **Strongly universal** | Smallest binary strongly universal (Neary-Woods). Blank tape start. Best for clean test. |

**Recommendation: Start with a NON-universal toy machine** to get the encoding right, then scale to (15,2).

**Toy machine:** 2-state, 2-symbol binary incrementer.
- States: {q₀, q_halt}, Symbols: {0, 1}, Tape: binary number, increments by 1.
- Transition table:
  - δ(q₀, 0) = (q_halt, 1, Stay)  — flip 0→1, done
  - δ(q₀, 1) = (q₀, 0, Left)     — flip 1→0, carry left

This is perfect because: (a) it's a well-understood arithmetic operation, (b) the "carry" propagation has a natural p-adic interpretation.

## 3. Proposed Adelic Encoding

### 3.1 The Adele Ring

An adele α ∈ 𝔸_ℚ is a tuple (α_∞, α₂, α₃, α₅, α₇, ...) where:
- α_∞ ∈ ℝ (Archimedean place)
- α_p ∈ ℚ_p for each prime p (p-adic places)
- Almost all α_p ∈ ℤ_p (integrality condition)

### 3.2 Encoding the TM Configuration

A TM configuration = (state, tape contents, head position).

**Proposal A: Pure 2-adic encoding (for binary TMs)**

For a binary TM, the tape is a bi-infinite binary sequence. The 2-adic integers ℤ₂ naturally encode one-sided infinite binary strings:

- **Tape right of head:** α₂ ∈ ℤ₂, where the 2-adic expansion gives the tape cells to the right
  - tape = b₀b₁b₂... → α₂ = b₀ + b₁·2 + b₂·4 + ...
- **Tape left of head:** Use α₃ or the "negative" direction in ℤ₂
  - Or: encode left tape in another p-adic component
- **State:** α_∞ ∈ ℝ (or a small prime, e.g., α₅ mod 15 for a 15-state machine)
- **Head position:** Implicit (always at boundary between left/right tape encodings)

**Proposal B: Multi-prime encoding (richer)**

Each prime encodes a different aspect:
- p = 2: tape contents (binary data)
- p = 3: state register (q ∈ {0,...,14} for 15-state machine via α₃ mod 15... but 15 isn't prime. Use α₃ for state mod 3, α₅ for state mod 5, reconstruct by CRT.)
- p = 5: head position (as 5-adic integer?)
- α_∞: "energy" / step counter

This is more adelically interesting — uses the CRT structure.

**Proposal C: Single-number Gödel encoding**

Encode the full configuration as a single rational number q ∈ ℚ, then look at it adelically:
- Configuration c → Gödel number g(c) ∈ ℕ
- Factorize: g(c) = 2^a · 3^b · 5^c · ...
- This IS an adele: the exponents are visible at each prime place
- Transition function T becomes multiplication by some rational: g(c') = g(c) · r(c)

### 3.3 Recommended Approach: Start with Proposal A

For the binary incrementer, the cleanest test:

**Configuration:** (state ∈ {0,1}, tape ∈ ℤ₂)

Since the incrementer operates on a binary number and the result is +1:
- Tape as 2-adic integer: n ∈ ℤ₂
- One step of "increment" = n → n + 1 in ℤ₂

**This is the key observation:** Binary increment IS 2-adic addition by 1. The carry propagation that the TM performs step-by-step is EXACTLY what happens digit-by-digit in 2-adic arithmetic, but the 2-adic operation does it "all at once."

So: α₂^(new) = α₂^(old) + 1 in ℤ₂.

If we define the adele α such that the transition operator is "add 1 in the 2-adic component," then α^n (in the sense of n applications) gives n increments = adding n.

**But this is too simple** — it doesn't test universality. It just shows one arithmetic operation maps to one adelic operation.

## 4. Toward Universality: Encoding Transition Tables

For a general TM with states Q and symbols Σ:

### 4.1 The Transition Function as Adelic Operation

δ: Q × Σ → Q × Σ × {L, R}

We need this to be expressible as an adelic operation α → f(α) where f uses the ring structure of 𝔸_ℚ.

**Key insight from Emmett:** α^n should give n-1 steps. This suggests the transition is multiplication by α (or by something derived from α). So the TM "IS" an adele, and running it = repeated multiplication.

**Attempt:** For configuration encoded as β ∈ 𝔸_ℚ:
- After one step: β' = α · β (adelic multiplication)
- After n steps: β^(n) = α^n · β₀

For this to work, multiplication by α must:
1. Read the current symbol (look at the relevant digit of β₂)
2. Look up the state (encoded somewhere in β)
3. Write the new symbol
4. Move the head
5. Update the state

This is a LOT to ask of a single multiplication. But consider:

**The p-adic valuation extracts information.** If β₂ has 2-adic expansion b₀ + b₁·2 + b₂·4 + ..., then:
- v₂(β₂) tells you how many leading zeros
- β₂ mod 2 gives the current symbol (b₀)
- Dividing by 2 = shifting the tape right
- Multiplying by 2 = shifting the tape left

So tape head movement IS multiplication/division by 2 in the 2-adic component.

### 4.2 Concrete Attempt: 2-State 2-Symbol Machine

States: {A, B}. Symbols: {0, 1}. Head moves: {L, R}.

Encode:
- Tape right of head: r ∈ ℤ₂ (2-adic, r = b₀ + b₁·2 + ...)
- Tape left of head: l ∈ ℤ₂ (2-adic, leftward cells)
- State: s ∈ {0, 1}

Current symbol = r mod 2 = b₀.

**Transition δ(s, b₀) = (s', w, D):**

To write w and move right:
- Remove current symbol: r' = (r - b₀)/2
- Prepend w to left tape: l' = l·2 + w
- New right tape: r' as above
- New state: s' from transition table

To write w and move left:
- Remove leftmost from left: b_L = l mod 2, l' = (l - b_L)/2
- Prepend w to right tape: r' = r - b₀ + w + ... wait, need to replace current symbol then shift

Let me re-derive:

**Move Right after writing w:**
- Right tape was: b₀, b₁, b₂, ... → becomes b₁, b₂, ... = (r - b₀)/2
- Left tape was: ..., a₁, a₀ → becomes ..., a₁, a₀, w = 2l + w

So: r_new = (r - (r mod 2)) / 2, l_new = 2l + w

**Move Left after writing w:**
- Right tape was: b₀, b₁, b₂, ... → becomes w, b₁, b₂, ... = w + 2·(r - b₀)/2 = w + r - (r mod 2)
- Left tape was: ..., a₁, a₀ → head moves to a₀, left becomes ..., a₁ = (l - (l mod 2))/2

So: r_new = w + r - (r mod 2), l_new = (l - (l mod 2))/2

### 4.3 Can These Be Adelic Multiplication?

The operations above are:
- mod 2 (reading a digit)
- divide by 2 (shifting)
- multiply by 2 (shifting)
- add a bit

These are all 2-adic operations. The BRANCHING (which transition to apply based on state × symbol) is the hard part — multiplication alone doesn't branch.

**Possible resolution:** Use the state to select among adeles. If s=0, multiply by α₀; if s=1, multiply by α₁. But this requires a conditional, which isn't a single adelic operation.

**Alternative:** Encode state and tape together so that multiplication by a SINGLE α automatically does the right thing regardless of current state. This would require α to somehow contain the full transition table.

This is where Emmett's (2,3) insight matters — perhaps in the right encoding, a specific adele α encodes the full transition table, and α^n really does give n steps.

## 5. What Emmett Might Mean

Re-reading: "the Adele α^n is executed for n-1 timesteps."

Perhaps α isn't multiplied against a configuration. Perhaps **α IS the configuration**, and raising it to the nth power IS the evolution. This would mean:

- α encodes initial config + machine
- α² encodes config after 1 step  
- α³ encodes config after 2 steps
- α^n encodes config after n-1 steps

For this to work, the algebraic structure of exponentiation in 𝔸_ℚ must naturally implement the TM transitions. This is a much stronger claim.

**How?** In the adele ring, α^n has p-adic components (α_p)^n. Each prime "tracks" a different aspect of the computation as it's exponentiated.

Example: if α₂ encodes the tape, then α₂^n evolves the tape n times. If α₃ encodes the state (as some element of ℤ₃), then α₃^n evolves the state n times.

**The product formula** ∏_v |α|_v = 1 (for α ∈ ℚ×) means that growth at one place is compensated by shrinkage at others. This is what Emmett means by "step in the Archimedean place, primes adjust" — there's a CONSERVATION LAW.

## 6. Proposed Proof of Principle: Step by Step

### Phase 1: Binary Incrementer (trivial but clarifying)
1. Encode binary number n as 2-adic integer
2. Show increment = +1 in ℤ₂
3. Show n increments = +n
4. Verify carry propagation matches TM step-by-step execution
5. Examine: what happens at OTHER primes when you add 1? (The adelic product formula perspective)

### Phase 2: Simple Non-Trivial TM (e.g., 3-state busy beaver)
1. Encode full configuration (state + tape) adelically
2. Find adelic operation corresponding to one TM step
3. Verify: does iterated application match TM execution?
4. Key test: does the encoding use multiple primes in a meaningful way?

### Phase 3: (15,2) Strongly Universal Machine
1. Encode the 15-state transition table
2. Demonstrate universal computation via adelic exponentiation
3. Show that the "background pattern" problem (for weak universality) doesn't arise because strongly universal machines start from blank tape

## 7. Key Questions for Emmett

1. When you say α^n, is this multiplication in 𝔸_ℚ (so α·α·...·α), or something else?
2. Is the configuration encoded IN α, or is α the operator and the configuration is separate?
3. The "tree pruning" in adelic gradient descent — is this literally the p-adic tree structure (ℤ_p as a tree of nested balls)?
4. Do you have a specific encoding for how transition tables map to adelic elements?

## 8. Connection to Lars's ProtoNum

The ProtoNum construction gives us F₁ → binary operations → arithmetic. The adelic encoding goes the other direction: full arithmetic → TM computation. Together they suggest a CIRCLE:

F₁ (one element) → distinguish two types → proto-arithmetic → ℤ → ℚ → 𝔸_ℚ → universal computation → ... → can encode any TM → including one that constructs F₁

The adjoint tower might be the precise mathematical path through this circle.
