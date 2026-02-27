"""
Visualization of the TM-adele correspondence.

Terminal output and HTML report generation.
"""

from __future__ import annotations
from correspondence import StepComparison
from padic import PAdic


def print_comparison(results: list[StepComparison], title: str = "TM-Adele Correspondence"):
    """Print a step-by-step comparison to the terminal."""
    print(f"\n{'='*72}")
    print(f"  {title}")
    print(f"{'='*72}\n")

    for r in results:
        match_str = "OK" if r.match else "!! MISMATCH !!"
        print(f"--- Step {r.step} [{match_str}] {r.notes} ---")

        # TM state
        cells, head_offset = r.tm_config.tape_contents(margin=6)
        tape_str = ' '.join(str(c) for c in cells)
        pointer = '  '.join(' ' if i != head_offset else '^' for i in range(len(cells)))
        state_names = {0: 'A/q0', 1: 'B/q1', 2: 'C', 3: 'HALT'}
        print(f"  TM   state={state_names.get(r.tm_config.state, str(r.tm_config.state))}")
        print(f"  Tape:  {tape_str}")
        print(f"  Head:  {pointer}")

        # Adelic components
        a2 = r.adele.padic_parts[2]
        a3 = r.adele.padic_parts[3]
        a_s = r.adele.padic_parts[23]
        print(f"  Adele: a_inf={r.adele.real_part:.0f}  "
              f"a_2=...{a2.digit_string(8)}  "
              f"a_3=...{a3.digit_string(8)}  "
              f"a_5=...{a_s.digit_string(4)}")

        # Norms
        norms = r.adele.norms()
        norm_str = '  '.join(f"|a|_{k}={v:.4f}" for k, v in norms.items() if v != 0)
        if norm_str:
            print(f"  Norms: {norm_str}")

        print()

    # Summary
    all_match = all(r.match for r in results)
    total = len(results)
    matched = sum(1 for r in results if r.match)
    print(f"{'='*72}")
    print(f"  Result: {matched}/{total} steps match.  "
          f"{'ALL MATCH' if all_match else 'MISMATCHES DETECTED'}")
    print(f"{'='*72}\n")


def print_direct_comparison(direct: dict):
    """Print the direct incrementer comparison (one-shot Z_2 addition)."""
    print(f"\n{'='*72}")
    print(f"  Direct Correspondence: Binary Increment = +1 in Z_2")
    print(f"{'='*72}\n")

    print(f"  Start value:  {direct['start_value']}  ({direct['start_binary']})")
    print(f"  End value:    {direct['end_value']}  ({direct['end_binary']})")
    print(f"  TM steps needed: {direct['tm_steps']} (carry propagation)")
    print()
    print(f"  2-adic before:  {direct['before_2adic']}")
    print(f"  2-adic after:   {direct['after_2adic']}")
    print(f"  Difference:     {direct['2adic_difference']}  (should be 1)")
    print()
    print(f"  TM final tape (binary):    {direct['tm_final_tape_binary']}")
    print(f"  Adelic final tape (binary): {direct['adelic_final_tape_binary']}")
    print()

    if direct['match']:
        print(f"  VERIFIED: The TM's {direct['tm_steps']}-step carry propagation")
        print(f"  is exactly +1 in Z_2. Adelic arithmetic captures the")
        print(f"  full computation in a single operation.")
    else:
        print(f"  !! MISMATCH: Something went wrong in the encoding. !!")
    print()


def generate_html_report(
    results: list[StepComparison],
    direct: dict | None = None,
    title: str = "Adelic-TM Correspondence",
    filename: str = "report.html",
):
    """Generate a standalone HTML report with styled visualization."""
    html = [f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  body {{ font-family: 'Courier New', monospace; background: #1a1a2e; color: #e0e0e0; padding: 2em; max-width: 900px; margin: 0 auto; }}
  h1 {{ color: #e94560; border-bottom: 2px solid #e94560; padding-bottom: 0.3em; }}
  h2 {{ color: #0f3460; background: #e94560; padding: 0.3em 0.6em; display: inline-block; }}
  .step {{ background: #16213e; border-left: 4px solid #0f3460; padding: 1em; margin: 1em 0; border-radius: 0 8px 8px 0; }}
  .step.mismatch {{ border-left-color: #ff6b6b; }}
  .match {{ color: #4ecdc4; font-weight: bold; }}
  .mismatch-text {{ color: #ff6b6b; font-weight: bold; }}
  .tape {{ font-size: 1.2em; letter-spacing: 0.3em; }}
  .tape .head {{ color: #e94560; font-weight: bold; text-decoration: underline; }}
  .adele {{ color: #a8d8ea; }}
  .note {{ color: #888; font-style: italic; }}
  .summary {{ background: #0f3460; padding: 1.5em; border-radius: 8px; margin-top: 2em; font-size: 1.1em; }}
  .summary.success {{ border: 2px solid #4ecdc4; }}
  .summary.failure {{ border: 2px solid #ff6b6b; }}
  .direct {{ background: #1a1a40; border: 2px solid #e94560; padding: 1.5em; border-radius: 8px; margin: 1.5em 0; }}
  .key-insight {{ background: #0a3d62; padding: 1em; border-radius: 8px; margin: 1em 0; border-left: 4px solid #4ecdc4; }}
  table {{ border-collapse: collapse; margin: 0.5em 0; }}
  td, th {{ padding: 0.3em 0.8em; border: 1px solid #333; }}
  th {{ background: #0f3460; }}
</style>
</head>
<body>
<h1>{title}</h1>
"""]

    if direct:
        html.append(f"""
<div class="key-insight">
<strong>Key Insight:</strong> The binary incrementer TM performs carry propagation
bit-by-bit over {direct['tm_steps']} steps. In Z_2 (2-adic integers), this entire
computation is a single operation: +1. The p-adic representation naturally encodes
the binary tape, and arithmetic in Z_2 IS the computation.
</div>

<div class="direct">
<h2>Direct Correspondence</h2>
<table>
<tr><th>Property</th><th>Value</th></tr>
<tr><td>Start</td><td>{direct['start_value']} = {direct['start_binary']}</td></tr>
<tr><td>End</td><td>{direct['end_value']} = {direct['end_binary']}</td></tr>
<tr><td>TM steps (carry propagation)</td><td>{direct['tm_steps']}</td></tr>
<tr><td>2-adic: before</td><td>{direct['before_2adic']}</td></tr>
<tr><td>2-adic: after</td><td>{direct['after_2adic']}</td></tr>
<tr><td>Difference</td><td>{direct['2adic_difference']} (should be 1)</td></tr>
<tr><td>Match?</td><td>{'<span class="match">YES</span>' if direct['match'] else '<span class="mismatch-text">NO</span>'}</td></tr>
</table>
</div>
""")

    html.append("<h2>Step-by-Step Trace</h2>")

    for r in results:
        cls = "step" if r.match else "step mismatch"
        match_html = '<span class="match">OK</span>' if r.match else '<span class="mismatch-text">MISMATCH</span>'

        cells, head_offset = r.tm_config.tape_contents(margin=6)
        tape_html = ''
        for i, c in enumerate(cells):
            if i == head_offset:
                tape_html += f'<span class="head">[{c}]</span> '
            else:
                tape_html += f'{c} '

        a2 = r.adele.padic_parts[2]
        a3 = r.adele.padic_parts[3]
        a_s = r.adele.padic_parts[23]

        state_names = {0: 'A/q0', 1: 'B/q1', 2: 'C', 3: 'HALT'}

        html.append(f"""
<div class="{cls}">
  <strong>Step {r.step}</strong> {match_html}
  <span class="note">{r.notes}</span><br>
  <strong>TM</strong> state={state_names.get(r.tm_config.state, str(r.tm_config.state))}<br>
  <span class="tape">{tape_html}</span><br>
  <span class="adele">
    a_inf={r.adele.real_part:.0f} &nbsp;
    a_2=...{a2.digit_string(8)} &nbsp;
    a_3=...{a3.digit_string(8)} &nbsp;
    a_5=...{a_s.digit_string(4)}
  </span>
</div>
""")

    all_match = all(r.match for r in results)
    total = len(results)
    matched = sum(1 for r in results if r.match)
    cls = "summary success" if all_match else "summary failure"

    html.append(f"""
<div class="{cls}">
  <strong>Result:</strong> {matched}/{total} steps match.
  {'ALL MATCH — correspondence verified.' if all_match else 'MISMATCHES DETECTED.'}
</div>
</body></html>""")

    with open(filename, 'w') as f:
        f.write('\n'.join(html))
    print(f"HTML report written to {filename}")
