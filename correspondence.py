"""
Proof of principle: run TM and adelic operations in parallel, verify correspondence.

Two modes:
1. STEP-BY-STEP: Run adelic_step() which mirrors the TM transition table
   using p-adic operations. Verify decoded adele matches TM config at each step.

2. DIRECT (incrementer only): Show that the TM's carry-propagation computation
   is equivalent to a single +1 in Z_2. The multi-step TM computation collapses
   to one adelic operation.
"""

from __future__ import annotations
from dataclasses import dataclass
from turing import TuringMachine, TMConfig, binary_incrementer, busy_beaver_3state
from padic import PAdic, tape_to_2adic
from adelic import (
    Adele, tm_config_to_adele, adele_to_tm_config, adelic_step, adelic_increment,
)


@dataclass
class StepComparison:
    """One step of the TM-adele correspondence."""
    step: int
    tm_config: TMConfig
    adele: Adele
    decoded_config: TMConfig
    match: bool
    notes: str = ""


def compare_incrementer(start_value: int = 23, precision: int = 64) -> list[StepComparison]:
    """
    Run the binary incrementer TM and adelic operations in parallel.
    
    Demonstrates: incrementing 23 (10111) to 24 (11000) requires
    a carry chain through 3 bits. In Z_2, this is just 23 + 1 = 24.
    
    We show BOTH:
    - Step-by-step correspondence (adelic_step mirrors each TM step)
    - Direct correspondence (adelic_increment does it in one shot)
    """
    # Set up TM
    tm = binary_incrementer()
    tm.load_binary(start_value)

    # Set up adele from initial config
    initial_config = tm.snapshot()
    adele = tm_config_to_adele(initial_config, precision)

    results: list[StepComparison] = []

    # Record initial state
    decoded = adele_to_tm_config(adele, precision)
    results.append(StepComparison(
        step=0,
        tm_config=initial_config.copy(),
        adele=adele,
        decoded_config=decoded,
        match=_configs_match(initial_config, decoded),
        notes="Initial configuration",
    ))

    # Run step by step
    while not tm.halted:
        tm.step()
        tm_cfg = tm.snapshot()
        adele = adelic_step(adele, tm.table)
        decoded = adele_to_tm_config(adele, precision)

        match = _configs_match(tm_cfg, decoded)
        results.append(StepComparison(
            step=tm.step_count,
            tm_config=tm_cfg.copy(),
            adele=adele,
            decoded_config=decoded,
            match=match,
            notes=_increment_notes(tm.step_count, start_value),
        ))

    return results


def compare_incrementer_direct(start_value: int = 23, precision: int = 64) -> dict:
    """
    Show that n steps of binary incrementer = +1 in Z_2.
    
    Returns a dict with before/after comparison.
    """
    # TM execution
    tm = binary_incrementer()
    tm.load_binary(start_value)
    trace = tm.run(max_steps=100)
    tm_final = trace[-1]

    # Direct adelic operation
    initial_config = TMConfig(state=0, tape=dict(trace[0].tape), head=0, step=0)
    adele_before = tm_config_to_adele(initial_config, precision)
    adele_after = adelic_increment(adele_before)
    decoded_after = adele_to_tm_config(adele_after, precision)

    # The 2-adic values
    before_2adic = adele_before.padic_parts[2].to_int()
    after_2adic = adele_after.padic_parts[2].to_int()

    return {
        "start_value": start_value,
        "start_binary": bin(start_value),
        "end_value": start_value + 1,
        "end_binary": bin(start_value + 1),
        "tm_steps": tm.step_count,
        "before_2adic": before_2adic,
        "after_2adic": after_2adic,
        "2adic_difference": after_2adic - before_2adic,
        "match": after_2adic == start_value + 1,
        "tm_final_tape_binary": tm_final.tape_as_binary(),
        "adelic_final_tape_binary": decoded_after.tape_as_binary(),
    }


def compare_beaver(max_steps: int = 20, precision: int = 64) -> list[StepComparison]:
    """
    Run the 3-state busy beaver and adelic operations in parallel.
    
    BB(3) writes 6 ones and halts in 14 steps. Here we encode the full
    configuration (state + bidirectional tape) as an adele and verify
    the correspondence at every step.
    """
    tm = busy_beaver_3state()
    initial_config = tm.snapshot()
    adele = tm_config_to_adele(initial_config, precision)

    results: list[StepComparison] = []

    decoded = adele_to_tm_config(adele, precision)
    results.append(StepComparison(
        step=0,
        tm_config=initial_config.copy(),
        adele=adele,
        decoded_config=decoded,
        match=_configs_match(initial_config, decoded),
        notes="Initial: blank tape, state A",
    ))

    for _ in range(max_steps):
        if tm.halted:
            break
        tm.step()
        tm_cfg = tm.snapshot()
        adele = adelic_step(adele, tm.table)
        decoded = adele_to_tm_config(adele, precision)

        state_names = {0: 'A', 1: 'B', 2: 'C', 3: 'HALT'}
        match = _configs_match(tm_cfg, decoded)
        results.append(StepComparison(
            step=tm.step_count,
            tm_config=tm_cfg.copy(),
            adele=adele,
            decoded_config=decoded,
            match=match,
            notes=f"State: {state_names.get(tm_cfg.state, '?')}",
        ))

    return results


def _configs_match(a: TMConfig, b: TMConfig, window: int = 32) -> bool:
    """Check if two TM configs match within a window around the head."""
    if a.state != b.state:
        return False
    for i in range(-window, window):
        av = a.tape.get(a.head + i, 0)
        bv = b.tape.get(b.head + i, 0)
        if av != bv:
            return False
    return True


def _increment_notes(step: int, start: int) -> str:
    """Generate explanatory notes for incrementer steps."""
    bits = []
    n = start
    for i in range(8):
        bits.append(n & 1)
        n >>= 1
    # Which bit is being processed at this step?
    if step <= len([b for b in bits if b == 1]):
        return f"Carry propagation through bit {step - 1}"
    return "Carry resolved"
