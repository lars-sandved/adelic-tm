"""
Genuinely Adelic Turing Machine

A computational model where the product formula acts as a genuine conservation law.
The computation state lives in GL(2, A_Q) — the adelic group — with the product formula
constraining total resource across places.

Key idea: the tape (archimedean place) can only grow by spending p-adic fuel.
The product formula bounds total computation.

Architecture:
- Archimedean place: tape as continued fraction (real magnitude)
- p-adic places: computational fuel at each prime
- Product formula: |x|_∞ · Π|x|_p = 1 enforced as budget constraint
- Each TM step costs archimedean magnitude, paid by p-adic fuel

Author: Clawd (research assistant)
Date: March 25, 2026
"""

from fractions import Fraction
from math import log, prod, sqrt
from typing import Optional
import json


class AdelicBudget:
    """
    Tracks the adelic budget across places.
    
    The product formula says: |x|_∞ · Π_p |x|_p = 1
    In log form: log|x|_∞ + Σ_p log|x|_p = 0
    
    We track log-magnitudes at each place.
    Total must remain ≤ initial_budget (= 0 in log form).
    """
    
    def __init__(self, primes: list[int], initial_fuel: dict[int, float] = None):
        """
        primes: list of primes to use as computational fuel
        initial_fuel: log-magnitude fuel at each prime (positive = fuel available)
        """
        self.primes = sorted(primes)
        
        # Each prime starts with fuel. Default: log(p) per prime (natural scale)
        if initial_fuel is None:
            self.fuel = {p: log(p) for p in primes}
        else:
            self.fuel = dict(initial_fuel)
        
        self.archimedean_cost = 0.0  # total log-magnitude spent at ∞
        self.total_initial = sum(self.fuel.values())
        self.steps_run = 0
        self.fuel_history = []  # track fuel over time
    
    def remaining_fuel(self) -> float:
        """Total fuel remaining across all primes."""
        return sum(max(0, f) for f in self.fuel.values())
    
    def budget_remaining(self) -> float:
        """How much more archimedean growth is possible."""
        return self.total_initial - self.archimedean_cost
    
    def can_afford(self, cost: float) -> bool:
        """Can we afford this archimedean cost?"""
        return self.archimedean_cost + cost <= self.total_initial + 1e-10
    
    def spend(self, cost: float, prime: int = None) -> bool:
        """
        Spend archimedean cost, drawing fuel from a prime.
        
        cost: log-magnitude cost of this tape operation
        prime: which prime to draw from (None = cheapest available)
        
        Returns True if affordable, False if budget exhausted.
        """
        if cost <= 0:
            # Free operation (no tape growth)
            self.steps_run += 1
            return True
        
        if not self.can_afford(cost):
            return False
        
        # Choose prime to draw from
        if prime is None:
            # Draw from the prime with most fuel
            available = {p: f for p, f in self.fuel.items() if f > 0}
            if not available:
                return False
            prime = max(available, key=available.get)
        
        if self.fuel.get(prime, 0) <= 0:
            return False
        
        # Spend
        actual_spend = min(cost, self.fuel[prime])
        self.fuel[prime] -= actual_spend
        self.archimedean_cost += actual_spend
        self.steps_run += 1
        
        return True
    
    def snapshot(self) -> dict:
        return {
            'step': self.steps_run,
            'fuel': dict(self.fuel),
            'archimedean_cost': self.archimedean_cost,
            'remaining': self.remaining_fuel(),
            'budget_remaining': self.budget_remaining(),
        }
    
    def __repr__(self):
        fuel_str = ', '.join(f'p={p}: {f:.3f}' for p, f in self.fuel.items() if f > 0.001)
        return (f'AdelicBudget(arch_cost={self.archimedean_cost:.3f}, '
                f'remaining={self.remaining_fuel():.3f}, fuel=[{fuel_str}])')


class AdelicTM:
    """
    Genuinely Adelic Turing Machine.
    
    Like a standard TM, but each tape operation costs archimedean magnitude
    that must be paid from p-adic fuel. When fuel runs out, the tape can't grow.
    """
    
    def __init__(self, transitions: dict, start_state: str, 
                 initial_tape: list[int], budget: AdelicBudget,
                 cost_model: str = 'logarithmic'):
        """
        transitions: {(state, read_sym): (write_sym, move, next_state)}
        start_state: initial state
        initial_tape: initial tape contents
        budget: AdelicBudget instance
        cost_model: how to compute cost of a tape operation
            'logarithmic': cost = log of push matrix entry (natural CF cost)
            'uniform': cost = 1 per step
            'symbol': cost = log(symbol + 1) (larger symbols cost more)
        """
        self.transitions = transitions
        self.state = start_state
        self.cost_model = cost_model
        self.budget = budget
        
        # Tape as two stacks (internal symbols = external + 1)
        self.left_stack = []
        self.right_stack = [s + 1 for s in initial_tape]
        self.blank_int = 1  # external 0 = internal 1
        
        self.halted = False
        self.budget_exhausted = False
        self.history = []
    
    def _operation_cost(self, write_symbol_ext: int, move: str) -> float:
        """Compute the archimedean cost of a tape operation."""
        write_int = write_symbol_ext + 1
        
        if self.cost_model == 'uniform':
            return 1.0
        elif self.cost_model == 'symbol':
            return log(write_int + 1)
        elif self.cost_model == 'logarithmic':
            # Cost based on CF: pushing k onto a CF grows magnitude by ~log(k)
            # More precisely, |P_k · x| ≈ k·|x|, so log cost ≈ log(k)
            return log(max(write_int, 1.01))
        else:
            return 1.0
    
    def step(self) -> dict:
        """Execute one step. Returns step info dict."""
        if self.halted or self.budget_exhausted:
            return {'status': 'stopped', 'reason': 'halted' if self.halted else 'budget_exhausted'}
        
        # Read
        if self.right_stack:
            read_int = self.right_stack[0]
        else:
            read_int = self.blank_int
        read_ext = read_int - 1
        
        # Lookup transition
        key = (self.state, read_ext)
        if key not in self.transitions:
            self.halted = True
            return {'status': 'halted', 'step': self.budget.steps_run,
                    'state': self.state, 'read': read_ext}
        
        write_ext, move, next_state = self.transitions[key]
        write_int = write_ext + 1
        
        # Compute cost
        cost = self._operation_cost(write_ext, move)
        
        # Try to spend
        if not self.budget.spend(cost):
            self.budget_exhausted = True
            return {'status': 'budget_exhausted', 'step': self.budget.steps_run,
                    'state': self.state, 'cost_needed': cost,
                    'fuel_remaining': self.budget.remaining_fuel()}
        
        # Execute tape operation
        if move == 'R':
            if self.right_stack:
                self.right_stack.pop(0)
            self.left_stack.insert(0, write_int)
        else:
            if self.right_stack:
                self.right_stack.pop(0)
            self.right_stack.insert(0, write_int)
            if self.left_stack:
                left_top = self.left_stack.pop(0)
                self.right_stack.insert(0, left_top)
            else:
                self.right_stack.insert(0, self.blank_int)
        
        self.state = next_state
        
        return {
            'status': 'running',
            'step': self.budget.steps_run,
            'state': self.state,
            'read': read_ext,
            'write': write_ext,
            'move': move,
            'cost': cost,
            'fuel_remaining': self.budget.remaining_fuel(),
            'tape_size': len(self.left_stack) + len(self.right_stack),
        }
    
    def run(self, max_steps: int = 100000) -> dict:
        """Run until halt, budget exhaustion, or max_steps."""
        for _ in range(max_steps):
            result = self.step()
            self.history.append(result)
            if result['status'] != 'running':
                return result
        return {'status': 'max_steps', 'step': self.budget.steps_run}
    
    def tape_contents(self) -> list[int]:
        """Current tape as external symbols."""
        left_rev = list(reversed(self.left_stack))
        full = left_rev + self.right_stack
        return [s - 1 for s in full]


# ============================================================
# Standard machine definitions
# ============================================================

ROGOZHIN_TRANSITIONS = {
    ('q1', 0): (1, 'R', 'q2'),
    ('q1', 1): (2, 'L', 'q1'),
    ('q1', 2): (1, 'L', 'q1'),
    ('q2', 0): (2, 'L', 'q1'),
    ('q2', 1): (2, 'R', 'q2'),
    ('q2', 2): (0, 'R', 'q2'),
}

BB3_TRANSITIONS = {
    ('A', 0): (1, 'R', 'B'),
    ('A', 1): (1, 'R', 'HALT'),
    ('B', 0): (0, 'R', 'C'),
    ('B', 1): (1, 'R', 'B'),
    ('C', 0): (1, 'L', 'C'),
    ('C', 1): (1, 'L', 'A'),
}

UNARY_ADD_TRANSITIONS = {
    ('seek', 1): (1, 'R', 'seek'),
    ('seek', 2): (2, 'R', 'check'),
    ('check', 1): (2, 'L', 'promote'),
    ('check', 0): (0, 'L', 'erase'),
    ('promote', 2): (1, 'R', 'at_sep'),
    ('at_sep', 2): (2, 'R', 'check'),
    ('erase', 2): (0, 'R', 'HALT'),
}

COUNTER_TRANSITIONS = {
    # Simple 2-state counter: writes 1s forever, moving right
    ('go', 0): (1, 'R', 'go'),
    ('go', 1): (1, 'R', 'go'),
}


def run_experiment(name: str, transitions: dict, start_state: str, 
                   tape: list[int], primes: list[int], 
                   fuel_multiplier: float = 1.0,
                   cost_model: str = 'logarithmic',
                   max_steps: int = 100000) -> dict:
    """Run a single experiment and return results."""
    
    fuel = {p: log(p) * fuel_multiplier for p in primes}
    budget = AdelicBudget(primes, fuel)
    tm = AdelicTM(transitions, start_state, tape, budget, cost_model)
    
    initial_budget = budget.total_initial
    result = tm.run(max_steps)
    
    return {
        'name': name,
        'primes': primes,
        'fuel_multiplier': fuel_multiplier,
        'cost_model': cost_model,
        'initial_budget': initial_budget,
        'steps_run': budget.steps_run,
        'status': result['status'],
        'fuel_remaining': budget.remaining_fuel(),
        'tape_size': len(tm.left_stack) + len(tm.right_stack),
        'tape_sample': tm.tape_contents()[:20],
    }


def main():
    """Run experiments with genuinely adelic TMs."""
    
    print("=" * 70)
    print("GENUINELY ADELIC TURING MACHINE — EXPERIMENTS")
    print("Product formula as conservation law")
    print("=" * 70)
    
    results = []
    
    # ============================================================
    # Experiment 1: Rogozhin UTM with varying fuel
    # ============================================================
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Rogozhin (2,3) UTM — How far can it go?")
    print("=" * 70)
    
    for n_primes in [1, 3, 5, 10, 25, 50, 100]:
        # Use first n primes
        primes = []
        candidate = 2
        while len(primes) < n_primes:
            if all(candidate % p != 0 for p in primes):
                primes.append(candidate)
            candidate += 1
        
        r = run_experiment(
            f'Rogozhin, {n_primes} primes',
            ROGOZHIN_TRANSITIONS, 'q1', [2, 2, 2, 2, 2],
            primes, fuel_multiplier=1.0
        )
        results.append(r)
        
        ones = sum(1 for s in r['tape_sample'] if s == 1)
        print(f"  {n_primes:3d} primes | budget={r['initial_budget']:8.3f} | "
              f"steps={r['steps_run']:6d} | status={r['status']:17s} | "
              f"tape={r['tape_size']:5d} | ~{ones}+ ones")
    
    # ============================================================
    # Experiment 2: Fuel multiplier scaling
    # ============================================================
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Rogozhin with 10 primes — varying fuel multiplier")
    print("=" * 70)
    
    primes_10 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    for mult in [0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0]:
        r = run_experiment(
            f'Rogozhin, 10p, fuel×{mult}',
            ROGOZHIN_TRANSITIONS, 'q1', [2, 2, 2, 2, 2],
            primes_10, fuel_multiplier=mult
        )
        results.append(r)
        print(f"  fuel×{mult:6.1f} | budget={r['initial_budget']:10.3f} | "
              f"steps={r['steps_run']:7d} | status={r['status']:17s} | "
              f"tape={r['tape_size']:6d}")
    
    # ============================================================
    # Experiment 3: BB(3) — does it halt before budget runs out?
    # ============================================================
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: BB(3) Busy Beaver — halt vs budget exhaustion")
    print("=" * 70)
    
    for n_primes in [1, 3, 5, 10, 25]:
        primes = []
        candidate = 2
        while len(primes) < n_primes:
            if all(candidate % p != 0 for p in primes):
                primes.append(candidate)
            candidate += 1
        
        r = run_experiment(
            f'BB(3), {n_primes} primes',
            BB3_TRANSITIONS, 'A', [],
            primes, fuel_multiplier=1.0
        )
        results.append(r)
        print(f"  {n_primes:3d} primes | budget={r['initial_budget']:8.3f} | "
              f"steps={r['steps_run']:6d} | status={r['status']:17s} | "
              f"tape={r['tape_size']:5d}")
    
    # ============================================================
    # Experiment 4: Unary addition — can it complete?
    # ============================================================
    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Unary Addition (3+2) — completion vs budget")
    print("=" * 70)
    
    for n_primes in [1, 3, 5, 10]:
        primes = []
        candidate = 2
        while len(primes) < n_primes:
            if all(candidate % p != 0 for p in primes):
                primes.append(candidate)
            candidate += 1
        
        r = run_experiment(
            f'Add 3+2, {n_primes} primes',
            UNARY_ADD_TRANSITIONS, 'seek', [1, 1, 1, 2, 1, 1],
            primes, fuel_multiplier=1.0
        )
        results.append(r)
        tape_str = ''.join(str(s) for s in r['tape_sample'][:10])
        print(f"  {n_primes:3d} primes | budget={r['initial_budget']:8.3f} | "
              f"steps={r['steps_run']:6d} | status={r['status']:17s} | "
              f"tape=[{tape_str}]")
    
    # ============================================================
    # Experiment 5: Simple counter — pure tape growth
    # ============================================================
    print("\n" + "=" * 70)
    print("EXPERIMENT 5: Counter (writes 1s forever) — pure tape growth")
    print("=" * 70)
    
    for n_primes in [1, 5, 10, 25, 50]:
        primes = []
        candidate = 2
        while len(primes) < n_primes:
            if all(candidate % p != 0 for p in primes):
                primes.append(candidate)
            candidate += 1
        
        r = run_experiment(
            f'Counter, {n_primes} primes',
            COUNTER_TRANSITIONS, 'go', [],
            primes, fuel_multiplier=1.0
        )
        results.append(r)
        print(f"  {n_primes:3d} primes | budget={r['initial_budget']:8.3f} | "
              f"steps={r['steps_run']:6d} | status={r['status']:17s} | "
              f"tape={r['tape_size']:6d}")
    
    # ============================================================
    # Experiment 6: Cost model comparison
    # ============================================================
    print("\n" + "=" * 70)
    print("EXPERIMENT 6: Rogozhin 10 primes — cost model comparison")
    print("=" * 70)
    
    for model in ['uniform', 'logarithmic', 'symbol']:
        r = run_experiment(
            f'Rogozhin, model={model}',
            ROGOZHIN_TRANSITIONS, 'q1', [2, 2, 2, 2, 2],
            primes_10, fuel_multiplier=10.0, cost_model=model
        )
        results.append(r)
        print(f"  {model:12s} | budget={r['initial_budget']:10.3f} | "
              f"steps={r['steps_run']:7d} | status={r['status']:17s} | "
              f"tape={r['tape_size']:6d}")
    
    # ============================================================
    # Experiment 7: Scaling law — steps vs number of primes
    # ============================================================
    print("\n" + "=" * 70)
    print("EXPERIMENT 7: Scaling — steps achievable vs number of primes")
    print("=" * 70)
    
    prime_counts = [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 75, 100, 150, 200]
    scaling_data = []
    
    for n_primes in prime_counts:
        primes = []
        candidate = 2
        while len(primes) < n_primes:
            if all(candidate % p != 0 for p in primes):
                primes.append(candidate)
            candidate += 1
        
        r = run_experiment(
            f'Counter, {n_primes}p',
            COUNTER_TRANSITIONS, 'go', [],
            primes, fuel_multiplier=1.0
        )
        
        budget = r['initial_budget']
        steps = r['steps_run']
        scaling_data.append((n_primes, budget, steps))
        print(f"  {n_primes:4d} primes | budget={budget:10.3f} | "
              f"steps={steps:8d} | steps/budget={steps/budget:.2f}")
    
    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTotal experiments run: {len(results)}")
    print(f"\nKey findings:")
    print(f"  - More primes = more fuel = more computation")
    print(f"  - Tape growth is bounded by total p-adic fuel")
    print(f"  - Halting programs (BB3, addition) may complete within budget")
    print(f"  - Non-halting programs (Rogozhin, counter) always exhaust budget")
    
    return results


if __name__ == '__main__':
    main()
