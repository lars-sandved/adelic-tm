# Adelic Turing Machines — From Scratch

**Date:** 2026-03-02
**Purpose:** Bottom-up explanation of the entire project, assuming no prior knowledge.

---

## What is a Turing Machine?

A Turing machine is the simplest possible model of a computer. Alan Turing invented it in 1936 to answer the question: "What does it mean to compute something?"

It has three parts:

**1. A tape** — an infinitely long strip divided into cells. Each cell holds a symbol (like 0 or 1). Think of it as an infinite piece of paper with one character per box.

```
... | 0 | 1 | 1 | 0 | 1 | 0 | 0 | ...
              ^
              head is here
```

**2. A head** — points at one cell at a time. It can read the symbol in that cell, write a new symbol, and move one step left or right.

**3. A state machine** — a small set of rules that says: "If I'm in state X and I read symbol Y, then write symbol Z, move left/right, and switch to state X'."

That's it. That's a computer. Every program ever written — every app, every game, every AI — can in principle be run on a Turing machine. It's just the rules (state machine) and the data (tape).

**A tiny example — the binary incrementer:**

This machine adds 1 to a binary number. The tape holds the number, and the head starts at the rightmost digit.

Rules:
- If you see a 1, write 0 (carry), move left
- If you see a 0, write 1, stop

Adding 1 to 011 (= 3):
```
Step 0: 0 1 [1]  → see 1, write 0, move left
Step 1: 0 [1] 0  → see 1, write 0, move left  
Step 2: [0] 0 0  → see 0, write 1, stop
Result: 1 0 0    → that's 4 ✓
```

The carry propagation — flipping 1s to 0s until you hit a 0 — is the entire computation.

---

## What are p-adic numbers?

Normal numbers (real numbers) measure "how big" something is. The number 1000000 is big, 0.000001 is small.

P-adic numbers flip this. They measure "how divisible" something is.

Pick a prime number p (like 2, 3, 5, 7...). In the **p-adic** world:
- A number is "small" if it's highly divisible by p
- A number is "big" if p doesn't divide it at all

**Example with p = 2 (2-adic numbers):**
- The number 64 = 2⁶ is very "small" 2-adically (highly divisible by 2)
- The number 7 is "big" 2-adically (not divisible by 2 at all)
- The number 12 = 4 × 3 = 2² × 3 is "medium" (divisible by 2 twice)

The "2-adic size" of a number n is |n|₂ = 1/2^(how many times 2 divides n):
- |64|₂ = 1/2⁶ = 1/64 (very small!)
- |7|₂ = 1 (2 divides it 0 times)
- |12|₂ = 1/4

**Why is this useful?** Because p-adic numbers naturally encode digit-by-digit structure.

A 2-adic integer is just an infinite binary string extending to the LEFT:
```
...1010110₂
```

The rightmost digits are the "most significant" (opposite of normal). You can do arithmetic on these — add, multiply — and the carries propagate to the left, exactly like in a Turing machine.

That carry propagation in our incrementer example? That's literally 2-adic addition.

---

## What is the real number line really?

When we say "real numbers" (ℝ), we mean the standard number line: 0, 1, π, √2, etc. This is one way to "complete" the rational numbers ℚ (fractions).

A rational number like 355/113 can be viewed as:
- A point on the real line: ≈ 3.14159...
- A 2-adic number: what's its binary expansion?
- A 3-adic number: how divisible by 3?
- A 5-adic number: how divisible by 5?
- ...one for every prime

Each of these is a different "lens" on the same rational number. Each lens reveals different structure.

The real number lens shows you the *size*.
The p-adic lenses show you the *arithmetic structure*.

---

## What is an adele?

An adele is ALL the lenses at once.

For a rational number x ∈ ℚ, the adele of x is the tuple:

**(x as a real number, x as a 2-adic number, x as a 3-adic number, x as a 5-adic number, ...)**

Written: α = (α∞, α₂, α₃, α₅, α₇, ...)

**Example:** x = 12 = 2² × 3

- α∞ = 12 (it's the number twelve on the real line)
- α₂ = ...001100₂ (in 2-adic binary: 12 = 4+8, divisible by 2² so "small" 2-adically)
- α₃ = ...000110₃ (in 3-adic: 12 = 3×4, divisible by 3 once)
- α₅ = ...000022₅ (in 5-adic: 12 is not divisible by 5, 12 = 2×5 + 2)
- α₇ = 12 in 7-adic...
- etc.

Every prime sees the same number 12, but through its own lens.

**The key structure: the product formula.** For any rational number x ≠ 0:

|x|∞ × |x|₂ × |x|₃ × |x|₅ × ... = 1

The "sizes" at all places multiply to 1. If a number is big at one place, it must be small at others. **Information is conserved across the lenses.**

For x = 12:
- |12|∞ = 12
- |12|₂ = 1/4 (2² divides it)
- |12|₃ = 1/3 (3 divides it once)
- All other |12|_p = 1

Check: 12 × (1/4) × (1/3) × 1 × 1 × ... = 1 ✓

This is not a coincidence — it's a deep theorem. It means the adele is a *constrained* object: you can't change one component without affecting others.

---

## What is a continued fraction?

A continued fraction (CF) is a way to write a number as a chain of nested divisions:

x = a₀ + 1/(a₁ + 1/(a₂ + 1/(a₃ + ...)))

Where a₀, a₁, a₂, ... are positive integers called the "digits" or "partial quotients."

**Example:** 355/113

355 ÷ 113 = 3 remainder 16, so a₀ = 3
113 ÷ 16 = 7 remainder 1, so a₁ = 7
16 ÷ 1 = 16, so a₂ = 16

355/113 = 3 + 1/(7 + 1/16) = [3; 7, 16]

**This IS the Euclidean algorithm.** Computing the CF of a/b is exactly computing gcd(a,b) via repeated division. The CF digits are the quotients at each step.

**The Gauss map** extracts CF digits one at a time:

G(x) = 1/(x − ⌊x⌋)

Where ⌊x⌋ means "round down" (floor). This:
1. Reads the current digit: a = ⌊x⌋
2. Strips it off and advances: G(x) = [a₁; a₂, a₃, ...] (the remaining CF)

So applying G repeatedly peels off CF digits one by one — like a tape head moving through the data.

---

## Now: why combine Turing machines with adeles?

Here's the big idea Emmett is pursuing:

**A Turing machine has two parts: data (tape) and control (state machine).**
**An adele has two parts: the real place (∞) and the p-adic places (2, 3, 5, ...).**

Emmett's claim: these match up.

| TM component | Adelic component |
|---|---|
| **Tape** (data) | **Real place** α∞ (Archimedean) |
| **State machine** (control) | **p-adic places** α₂, α₃, ... |
| **One step of computation** | **One step of the Gauss map** (CF expansion) |

The tape is a real number. Its continued fraction expansion is the sequence of symbols on the tape. Each application of the Gauss map reads one symbol and advances the head.

The state machine lives in the p-adic components. The primes encode which state the machine is in and what transition to apply.

**And the product formula couples them.** When the Gauss map changes α∞ (reading/writing the tape), the p-adic components MUST adjust to maintain ∏|α|_v = 1. The state transition isn't independent of the tape operation — they're forced to be consistent by number theory itself.

This is why it's more than just a clever encoding. The adelic structure *imposes* computational constraints. The conservation law (product formula) means information can't be created or destroyed — it flows between the real and p-adic places.

---

## The parity checker: a complete walkthrough

Let's see this work concretely. We'll build a machine that reads a binary string and tells you whether it has an even or odd number of 1s.

**The machine:**
- Two states: EVEN and ODD (start in EVEN)
- Read symbols left to right
- If you read a 1, flip your state (EVEN↔ODD)
- If you read a 0, state stays the same
- When you hit the end marker, your state IS the answer

**Encoding the tape as a real number:**

Our input is: 1, 0, 1, 1 (which has three 1s → odd parity)

CF digits must be ≥ 1, so we shift: symbol 0 → digit 1, symbol 1 → digit 2, end-marker → digit 3.

Tape [1, 0, 1, 1, end] → CF digits [2, 1, 2, 2, 3]

Build the real number bottom-up:
- Start from the end: 3
- Wrap: 2 + 1/3 = 7/3
- Wrap: 2 + 1/(7/3) = 2 + 3/7 = 17/7
- Wrap: 1 + 1/(17/7) = 1 + 7/17 = 24/17
- Wrap: 2 + 1/(24/17) = 2 + 17/24 = 65/24

**α∞ = 65/24 ≈ 2.708**

This single rational number contains the entire tape.

**Encoding the state in p-adics:**

State ∈ {EVEN=0, ODD=1}. We use α₂ mod 2:
- α₂ = 0 → EVEN
- α₂ = 1 → ODD

Start in EVEN: α₂ = 0.

**Now run it:**

**Step 1:**
- READ: ⌊65/24⌋ = 2 → that means symbol 1
- STATE: α₂ = 0 → EVEN
- TRANSITION: EVEN + read 1 → flip to ODD
- ADVANCE: G(65/24) = 1/(65/24 − 2) = 1/(17/24) = 24/17
- UPDATE: α₂ = 1 (ODD)

α∞ = 24/17, state = ODD

**Step 2:**
- READ: ⌊24/17⌋ = 1 → symbol 0
- STATE: ODD
- TRANSITION: ODD + read 0 → stay ODD
- ADVANCE: G(24/17) = 1/(24/17 − 1) = 1/(7/17) = 17/7
- UPDATE: α₂ = 1 (stays ODD)

α∞ = 17/7, state = ODD

**Step 3:**
- READ: ⌊17/7⌋ = 2 → symbol 1
- STATE: ODD
- TRANSITION: ODD + read 1 → flip to EVEN
- ADVANCE: G(17/7) = 1/(17/7 − 2) = 1/(3/7) = 7/3
- UPDATE: α₂ = 0 (EVEN)

α∞ = 7/3, state = EVEN

**Step 4:**
- READ: ⌊7/3⌋ = 2 → symbol 1
- STATE: EVEN
- TRANSITION: EVEN + read 1 → flip to ODD
- ADVANCE: G(7/3) = 1/(7/3 − 2) = 1/(1/3) = 3
- UPDATE: α₂ = 1 (ODD)

α∞ = 3, state = ODD

**Step 5:**
- READ: ⌊3⌋ = 3 → end marker
- STATE: ODD
- RESULT: **ODD parity** ✓ (the input 1,0,1,1 has three 1s)

The Gauss map naturally unwound the CF digit by digit, and the state tracked parity through the p-adic component. The entire computation was: iterate G on a rational number while tracking a mod-2 counter.

---

## What we built before (and why it was inverted)

In our existing code, we did it backwards from Emmett's picture:
- Tape → p-adic (stored tape data in 2-adic numbers)
- State → real number or small prime
- Stepping → Python lookup table, or Collatz-style piecewise maps

This worked in the sense that it produced correct answers, but the adelic structure wasn't doing computational work — it was just a filing cabinet. The branching logic (which transition to use) was external Python code, not number theory.

Emmett's architecture makes the adelic structure do the actual work: the Gauss map reads the tape, the primes handle state, and the product formula couples them.

---

## What's still unclear / open questions for Emmett

1. **Left movement:** The Gauss map only moves right (peeling off CF digits). How does the head move left? Probably involves an inverse Gauss map or a second stack, but we need Emmett's view on this.

2. **Writing:** The parity checker only reads. A real TM also writes symbols. How does writing modify the CF?

3. **What exactly is α^n?** Emmett says "the adele α^n is executed for n−1 timesteps." Is that n iterations of the Gauss map? Or literal exponentiation in the adele ring? Big difference.

4. **The residue optimization:** Emmett says the standard Gauss map (numerator = 1) converges fast but thrashes computationally. He wants residues near unity. This is about choosing a *modified* CF expansion — a known technique but the specific recipe matters.

5. **Binary tape encoding:** Emmett says "do the CF in ℤ₂, which just means you use a lot more tape places per integer." Does this mean each CF digit is itself read in binary (via its ℤ₂ expansion), creating a two-level hierarchy?

6. **The product formula as conservation law:** Does ∏|α|_v = 1 play an active role in the TM dynamics, or is it a background constraint?
