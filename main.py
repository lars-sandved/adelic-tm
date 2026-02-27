#!/usr/bin/env python3
"""
Adelic-TM Correspondence: Proof of Principle

Demonstrates the correspondence between Turing machine operations
and adelic arithmetic. Two demonstrations:

  python main.py increment [--start N] [--html FILE]
      Binary incrementer: shows carry propagation = +1 in Z_2

  python main.py beaver [--steps N] [--html FILE]
      3-state busy beaver: full TM config encoded as adele
"""

import argparse
import sys

from correspondence import compare_incrementer, compare_incrementer_direct, compare_beaver
from visualize import print_comparison, print_direct_comparison, generate_html_report


def main():
    parser = argparse.ArgumentParser(
        description="Adelic-TM Correspondence: Proof of Principle",
    )
    subparsers = parser.add_subparsers(dest="command", help="Demo to run")

    # Incrementer
    inc = subparsers.add_parser("increment", help="Binary incrementer demo")
    inc.add_argument("--start", type=int, default=23, help="Starting number (default: 23)")
    inc.add_argument("--html", type=str, help="Generate HTML report to file")

    # Busy beaver
    bb = subparsers.add_parser("beaver", help="3-state busy beaver demo")
    bb.add_argument("--steps", type=int, default=20, help="Max steps (default: 20)")
    bb.add_argument("--html", type=str, help="Generate HTML report to file")

    args = parser.parse_args()

    if args.command == "increment":
        run_incrementer(args)
    elif args.command == "beaver":
        run_beaver(args)
    else:
        parser.print_help()
        sys.exit(1)


def run_incrementer(args):
    print(f"Running binary incrementer: {args.start} -> {args.start + 1}")
    print(f"Binary: {bin(args.start)} -> {bin(args.start + 1)}")
    print()

    # Step-by-step comparison
    results = compare_incrementer(args.start)
    print_comparison(results, title=f"Binary Incrementer: {args.start} -> {args.start + 1}")

    # Direct comparison (the key result)
    direct = compare_incrementer_direct(args.start)
    print_direct_comparison(direct)

    if args.html:
        generate_html_report(results, direct=direct,
                           title=f"Binary Incrementer: {args.start} -> {args.start + 1}",
                           filename=args.html)


def run_beaver(args):
    print(f"Running 3-state busy beaver (max {args.steps} steps)")
    print("BB(3): writes 6 ones, halts in 14 steps")
    print()

    results = compare_beaver(max_steps=args.steps)
    print_comparison(results, title="3-State Busy Beaver")

    if args.html:
        generate_html_report(results, title="3-State Busy Beaver", filename=args.html)


if __name__ == "__main__":
    main()
