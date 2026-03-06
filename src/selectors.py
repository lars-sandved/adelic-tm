"""Arithmetic selectors and Mem diagnostics.

Two selector modes:

1. **CRT selector** (ℤ/Nℤ, N=d×q) — Emmett's original design.
   Uses Chinese Remainder Theorem packing. Fails when denominators
   in Lagrange interpolation are non-units (Mem violation).

2. **Prime field selector** (𝔽_P, P = smallest prime ≥ #transitions) —
   Lagrange interpolation over a prime field, which is guaranteed to
   work for ANY machine. Every nonzero element is invertible in a field,
   so the Mem condition is trivially satisfied.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .spec import MachineSpec, Transition


class SelectorError(Exception):
    """Raised when the arithmetic selector fails (Mem violation)."""
    pass


@dataclass(frozen=True)
class CollisionWitness:
    prime: int
    ri_mod_p: int
    rj_mod_p: int


@dataclass(frozen=True)
class MemCollision:
    transition_i: str
    transition_j: str
    ri: int
    rj: int
    delta: int
    gcd_with_n: int
    primes: list[int]
    witnesses: list[CollisionWitness]


@dataclass(frozen=True)
class MemCheckReport:
    is_total: bool
    modulus_n: int
    alphabet_size: int
    state_count: int
    gcd_d_q: int
    collisions: list[MemCollision]
    notes: list[str]


def _prime_factors(n: int) -> list[int]:
    n = abs(n)
    if n <= 1:
        return []
    factors: list[int] = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            factors.append(d)
            while n % d == 0:
                n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors.append(n)
    return factors


def _mod_inverse(a: int, n: int) -> int:
    return pow(a, -1, n)


def pack_residue(read_symbol: int, state_index: int, d: int, q: int) -> int:
    """Pack (read, state) into ℤ/(dq)ℤ via CRT, requiring gcd(d,q)=1."""
    n = d * q
    m1 = q
    m2 = d
    inv1 = _mod_inverse(m1 % d, d)
    inv2 = _mod_inverse(m2 % q, q)
    return (read_symbol * m1 * inv1 + state_index * m2 * inv2) % n


def build_case_residues(machine: MachineSpec) -> list[tuple[Transition, int]]:
    d = machine.alphabet_size
    q = len(machine.states)
    state_idx = {s: i for i, s in enumerate(machine.states)}

    residues: list[tuple[Transition, int]] = []
    for transition in machine.transitions:
        residues.append(
            (transition, pack_residue(transition.read, state_idx[transition.state], d, q))
        )
    return residues


def check_mem_totality(machine: MachineSpec) -> MemCheckReport:
    """Check if the machine's selector has Mem (no zero-divisor collisions)."""
    d = machine.alphabet_size
    q = len(machine.states)
    n = d * q
    g = math.gcd(d, q)
    notes: list[str] = []

    if g != 1:
        notes.append(
            "alphabet_size and state_count are not coprime; CRT selector packing is not valid"
        )
        return MemCheckReport(
            is_total=False, modulus_n=n, alphabet_size=d,
            state_count=q, gcd_d_q=g, collisions=[], notes=notes,
        )

    cases = build_case_residues(machine)
    collisions: list[MemCollision] = []
    for i in range(len(cases)):
        ti, ri = cases[i]
        for j in range(i + 1, len(cases)):
            tj, rj = cases[j]
            delta = ri - rj
            gcd_with_n = math.gcd(abs(delta), n)
            if gcd_with_n > 1:
                primes = _prime_factors(gcd_with_n)
                witnesses = [
                    CollisionWitness(prime=p, ri_mod_p=ri % p, rj_mod_p=rj % p)
                    for p in primes
                ]
                collisions.append(
                    MemCollision(
                        transition_i=ti.case_id, transition_j=tj.case_id,
                        ri=ri, rj=rj, delta=delta, gcd_with_n=gcd_with_n,
                        primes=primes, witnesses=witnesses,
                    )
                )

    return MemCheckReport(
        is_total=(len(collisions) == 0), modulus_n=n, alphabet_size=d,
        state_count=q, gcd_d_q=g, collisions=collisions, notes=notes,
    )


def select_transition(machine: MachineSpec, state: str, read_symbol: int) -> Transition:
    """Select transition using Lagrange interpolation over ℤ/Nℤ.

    Crashes explicitly on Mem violation (non-unit denominators).
    """
    d = machine.alphabet_size
    q = len(machine.states)
    n = d * q
    if math.gcd(d, q) != 1:
        raise SelectorError("selector mode requires gcd(alphabet_size, state_count) = 1")

    state_idx = {s: i for i, s in enumerate(machine.states)}
    if state not in state_idx:
        raise SelectorError(f"unknown state in selector mode: {state}")

    u = pack_residue(read_symbol, state_idx[state], d, q)
    cases = build_case_residues(machine)

    selector_values: list[int] = []
    for i, (_, ri) in enumerate(cases):
        value = 1
        for j, (_, rj) in enumerate(cases):
            if i == j:
                continue
            denom = (ri - rj) % n
            if math.gcd(denom, n) != 1:
                factors = _prime_factors(math.gcd(denom, n))
                raise SelectorError(
                    f"Mem violation: selector denominator non-unit in ℤ/{n}ℤ "
                    f"for pair (ri={ri}, rj={rj}), primes={factors}"
                )
            numer = (u - rj) % n
            value = (value * numer * _mod_inverse(denom, n)) % n
        selector_values.append(value)

    chosen = [i for i, v in enumerate(selector_values) if v % n == 1]
    zeros_ok = all((v % n == 0) for i, v in enumerate(selector_values) if i not in chosen)

    if len(chosen) != 1 or not zeros_ok:
        raise SelectorError(
            f"selector failed uniqueness/orthogonality at u={u}, values={selector_values}"
        )

    transition = cases[chosen[0]][0]
    if transition.state != state or transition.read != read_symbol:
        raise SelectorError(
            f"selector chose wrong transition: expected ({state}, {read_symbol}), "
            f"got ({transition.state}, {transition.read})"
        )

    return transition


# ---------------------------------------------------------------------------
# Prime field selector (𝔽_P)
# ---------------------------------------------------------------------------

def _next_prime(n: int) -> int:
    """Smallest prime ≥ n."""
    if n <= 2:
        return 2
    candidate = n if n % 2 != 0 else n + 1
    while True:
        if _is_prime(candidate):
            return candidate
        candidate += 2


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    d = 5
    while d * d <= n:
        if n % d == 0 or n % (d + 2) == 0:
            return False
        d += 6
    return True


def prime_field_modulus(machine: MachineSpec) -> int:
    """Return the prime P used for the 𝔽_P selector.

    P must be ≥ d*q (the index space), not just ≥ number of transitions,
    because indices range from 0 to d*q - 1 and must be distinct mod P.
    """
    index_space = machine.alphabet_size * len(machine.states)
    return _next_prime(index_space)


def pack_index(read_symbol: int, state: str, machine: MachineSpec) -> int:
    """Pack (read, state) into a simple linear index.

    index = read_symbol * q + state_index, where q = len(states).
    All values are in {0, ..., d*q - 1}, guaranteed < P.
    """
    state_idx = {s: i for i, s in enumerate(machine.states)}
    q = len(machine.states)
    return read_symbol * q + state_idx[state]


def build_prime_field_cases(machine: MachineSpec) -> list[tuple[Transition, int]]:
    """Assign each transition a unique index for prime field interpolation."""
    state_idx = {s: i for i, s in enumerate(machine.states)}
    q = len(machine.states)
    cases: list[tuple[Transition, int]] = []
    for t in machine.transitions:
        idx = t.read * q + state_idx[t.state]
        cases.append((t, idx))
    return cases


def select_transition_prime(machine: MachineSpec, state: str, read_symbol: int) -> Transition:
    """Select transition using Lagrange interpolation over 𝔽_P.

    Works for ANY machine — no coprimality conditions needed.
    P is the smallest prime ≥ number of transition cases.
    """
    P = prime_field_modulus(machine)
    u = pack_index(read_symbol, state, machine)
    cases = build_prime_field_cases(machine)

    # Lagrange basis polynomials evaluated at u, over 𝔽_P
    for i, (ti, ri) in enumerate(cases):
        basis = 1
        for j, (_, rj) in enumerate(cases):
            if i == j:
                continue
            denom = (ri - rj) % P
            # In 𝔽_P every nonzero element is invertible
            assert denom != 0, f"duplicate indices: ri={ri} rj={rj}"
            numer = (u - rj) % P
            basis = (basis * numer * pow(denom, -1, P)) % P

        if basis == 1:
            # This is the matching transition
            if ti.state != state or ti.read != read_symbol:
                raise SelectorError(
                    f"prime selector chose wrong transition: "
                    f"expected ({state}, {read_symbol}), got ({ti.state}, {ti.read})"
                )
            return ti

    raise SelectorError(
        f"prime selector found no matching transition for ({state}, {read_symbol}), u={u}"
    )


@dataclass(frozen=True)
class PrimeFieldReport:
    """Diagnostics for the prime field selector."""
    prime: int
    num_transitions: int
    case_indices: list[tuple[str, int]]
    is_total: bool  # always True for prime field


def check_prime_field(machine: MachineSpec) -> PrimeFieldReport:
    """Diagnostic report for the prime field selector."""
    P = prime_field_modulus(machine)
    cases = build_prime_field_cases(machine)
    indices = [(t.case_id, idx) for t, idx in cases]
    # Check uniqueness
    idx_set = {idx for _, idx in cases}
    is_total = len(idx_set) == len(cases)  # should always be True
    return PrimeFieldReport(
        prime=P, num_transitions=len(cases),
        case_indices=indices, is_total=is_total,
    )
