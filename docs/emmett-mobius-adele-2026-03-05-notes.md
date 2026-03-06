# Emmett's "Möbius Transformations on the Adeles" — Notes & Analysis
**Date received:** 2026-03-05
**Source file:** emmett-mobius-adele-2026-03-05.pdf

## Summary

This paper is the theoretical backbone that was missing from the previous doc. It presents a complete arithmetic model where:
- Each TM step = a GL(2,ℤ) Möbius transformation
- The full computation = a matrix product (the "Shear expansion")
- State + branching = arithmetic via CRT + Lagrange selectors (NOT external lookup)
- Three failure modes correspond to three adelic places

## Architecture (8 sections)

### §2: CF-Stack Tape Encoding
Same L/R idea as previous doc, but now using continued fractions (not base-d):
- X_R = [t₀; t₁, t₂, ...] (rightward from head)
- X_L = [t₋₁; t₋₂, ...] (leftward)
- All symbols ≥ 1 (shift alphabet to avoid 0)

Push k: X → k + 1/X, matrix P_k = ((k,1),(1,0))
Pop:    X → 1/(X-k) where k=⌊X⌋, matrix Q_k = ((0,1),(1,-k))

Key: Push = the CF "build" operation. Pop = the Gauss map. Both are GL(2,ℤ).

### §3: Shear Expansion
P_k = S(k) · J  where S(k) = ((1,k),(0,1)) is a shear, J = ((0,1),(1,0)) is swap
Q_k = J · S(-k)

So every computation of length T is a word of ≤ 2T generators of GL(2,ℤ).
The "Shear expansion" Φ(γ) = ∏ M_t is a single GL(2,ℤ) element encoding the whole computation.

Remark 3.4 is deep: a CF [a₀; a₁, ..., aₙ] IS the matrix product ∏ S(aᵢ)·J.
So the tape configuration is a partial product, and computation extends that product.

### §4: Arithmetic Selectors (THIS SOLVES THE STATE PROBLEM)
CRT packing: with d symbols and q states, gcd(d,q)=1, set N=dq.
ℤ/Nℤ ≅ ℤ/dℤ × ℤ/qℤ

Every (state, symbol) pair packs into a single residue u ∈ ℤ/Nℤ.
a = u mod d (digit channel)
s = u mod q (state channel)

Lagrange selectors: e_i(u) = ∏_{j≠i} (u-r_j)/(r_i-r_j)
This is a polynomial that equals 1 at case i and 0 at all other cases.

Arithmetic transition: M(u) = Σ e_i(u) · M_i
This selects the right Möbius matrix PURELY ARITHMETICALLY. No if/else. No table lookup.

### §5: Three Adelic Places
- **Aleph (ℵ, p=∞):** Archimedean. CF stacks must converge. Failure = divergence.
- **Mem (מ, finite primes):** Selectors must be well-defined (denominators are units mod N). Failure = crash.
- **Tav (ת, p=1):** Trivial place. Computation must halt. Failure = non-termination.

### §5.4: Golem Metaphor
אמת (emet = "truth") = Aleph + Mem + Tav
- Erase Aleph → מת (met = "death"): divergent process
- Erase Tav → אם (em = "if/mother"): runs but never halts
- Erase Mem → no transition logic: clay without inscription

### §6: Emet-Shear Theorem
**Definition:** Emet condition ℰ = ℵ ∧ Mem ∧ Tav (convergence ∧ totality ∧ termination)
**Definition:** Tam condition = each step is well-formed (selector fires uniquely, shear parameter valid, stacks stay positive)

**Theorem 6.3:** If initial config satisfies Emet and every Shear factor satisfies Tam, then Emet is conserved at every step. "Truth, once inscribed, is conserved under a complete Shear expansion."

**Corollary 6.4 (Met):** A single incomplete step can destroy truth. אמת → מת.

### §7: Connection to base-d formulation
Shows how the CF-stack and base-d formulations relate. CF version is "native" Möbius; base-d version is "emergent" (projective linearity on P²).

### §8.3: Tameh (reversal)
The reversed computation Φ(γ)⁻¹ "uncomputes." אמת reversed ≈ טמא (tameh = "impurity"). Connection to reversible computation / Landauer's principle.

## Critical Analysis

### What's genuinely strong

1. **The CRT selector SOLVES the state problem.** This is the answer to "where does state live?" — it's packed into ℤ/Nℤ alongside the digit via CRT. The Lagrange selector does arithmetic branching without any external logic. This is what was missing from the previous doc.

2. **Computation as GL(2,ℤ) word.** A halting computation IS a single group element. This is a genuine structural insight — it connects computation to the algebraic structure of the modular group.

3. **The three-place correspondence is non-trivial.** Convergence/totality/termination mapping to archimedean/finite/trivial places is real mathematical content, not just relabeling.

4. **Push/Pop as Möbius maps.** The fact that stack operations are literally GL(2,ℤ) elements makes the whole framework algebraically natural. The CF connection (Remark 3.4) means the tape configuration and the computation live in the same algebraic object.

### Concerns

1. **CRT requires gcd(d,q)=1.** For a 2-state, 4-symbol TM (like in his previous example), gcd(4,2)=2≠1. You'd need to pad to 3 or 5 states. Not fatal but adds overhead. COULD be a real problem for minimal TMs.

2. **Lagrange selector denominators must be units.** The paper correctly identifies this as the Mem condition, but doesn't show how to construct a valid encoding for a given TM. Is it always possible? For what class of TMs? This is a gap.

3. **Product formula invocation in Theorem 6.3 is loose.** det(Φ) = ±1, so |det|_v = 1 at all places trivially. The product formula is satisfied but doesn't "do work" in the proof. The three conditions hold independently, not because the product formula forces them. The proof sketch leans on this more than it should.

4. **Tav condition is philosophically appealing but mathematically thin.** Saying "termination = trivial place" because the trivial absolute value distinguishes 0 from nonzero is a naming convention, not a theorem. Compare with the Aleph and Mem conditions which have real mathematical content.

5. **No worked numerical example of CRT selector.** The previous doc had verifiable arithmetic at every step. This paper is purely theoretical. Would be much stronger with a concrete example of: here's a TM, here's the CRT packing, here are the selectors, here's M(u) for each u.

6. **Symbols must be ≥ 1.** The CF encoding requires positive partial quotients. Zero symbols need to be absorbed by shifting the alphabet. This is fine for theory but changes the TM you're encoding.

### What this addresses from our gaps

- ✅ **State register:** CRT packing puts state into ℤ/Nℤ
- ✅ **Branching:** Lagrange selectors do arithmetic branching
- ✅ **External logic:** M(u) = Σ e_i(u)·M_i is a formula, not a lookup
- ✅ **Adelic structure:** Three places correspond to three conditions
- ✅ **Connection to CF:** Push/pop are literally GL(2,ℤ)
- ⚠️ **Practical encoding:** No worked example, gcd constraint

### For code implementation

The key thing to build:
1. CRT packing: encode (state, digit) as residue u ∈ ℤ/Nℤ
2. Lagrange selectors: compute e_i(u) in ℤ/Nℤ
3. Selector-weighted Möbius step: M(u) = Σ e_i(u) · M_i
4. Shear expansion: accumulate the GL(2,ℤ) product
5. Verify Emet condition at each step

This would give us a FULLY arithmetic TM with no external branching.
