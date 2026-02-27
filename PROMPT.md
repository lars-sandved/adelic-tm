Read SPEC.md for full mathematical context. Build a Python project:

## Files to create:

### turing.py
TuringMachine class. Takes transition table as dict mapping (state, symbol) -> (new_state, write_symbol, direction). Direction is 'L' or 'R'. Methods: step(), run(max_steps), get_trace(). Built-in factories: binary_incrementer() and busy_beaver_3state(). The binary incrementer takes a binary number on tape and adds 1 (with carry propagation). Tape is a defaultdict(int) with 0 as blank.

### padic.py  
PAdic class representing p-adic integers. Store as list of digits (least significant first) up to precision. Support: add, mul, from_int, to_int (for small numbers), mod_p, div_p, valuation, __repr__ showing p-adic expansion. Key insight: a 2-adic integer with digits [b0,b1,b2,...] IS the binary tape b0+b1*2+b2*4+...

### adelic.py
Adele class: real_part (float) + padic_parts (dict mapping prime -> PAdic). Encode TM config as adele: tape right of head -> 2-adic, tape left of head -> 3-adic (binary digits encoded in base 3), state -> 5-adic, step count -> real part. Functions: tm_config_to_adele(), adele_to_tm_config(), adelic_step() that advances one TM step via adelic operations.

### correspondence.py
Run TM and adelic version in parallel for n steps. At each step decode the adele back to TM config and verify match. Return list of (tm_config, adele, match_bool) tuples. Special handling for binary incrementer: show that the net effect is +1 in Z_2.

### visualize.py
print_comparison(): side-by-side terminal output showing TM tape and adelic components at each step. generate_html_report(): creates standalone HTML file with styled step-by-step visualization. For incrementer, highlight the carry propagation.

### main.py
CLI: `python main.py increment [--start N] [--html FILE]` and `python main.py beaver [--steps N] [--html FILE]`. Default start=23 for incrementer, steps=20 for beaver.

### README.md
Explain the mathematical correspondence, how to run, example output.

## Critical: Test everything
Run `python main.py increment` and `python main.py beaver` and make sure they produce correct output with no errors.
