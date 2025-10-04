#!/usr/bin/env python3
"""
Memory Summarizer - Converts session transcripts to Tier-A/B/C briefs

Usage:
  cat session.md | python summarize.py [--mode brief|full|ultra]
  python summarize.py --input session.md --mode full
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path


def extract_markers(lines):
    """Extract content by marker prefixes"""
    C, D, CH, Q, N = [], [], [], [], []

    for ln in lines:
        s = ln.strip()
        if s.startswith("C:"): C.append(s[2:].strip())
        elif s.startswith("D:"): D.append(s[2:].strip())
        elif s.startswith("Δ:"): CH.append(s[2:].strip())
        elif s.startswith("Q:"): Q.append(s[2:].strip())
        elif s.startswith("→:") or s.startswith("->"): N.append(s[2:].strip())

    return C, D, CH, Q, N


def brief_summary(lines, timestamp=None):
    """Generate Tier-A Brief (≤250 tokens ~ 1000 chars)"""
    C, D, CH, Q, N = extract_markers(lines)

    timestamp = timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    out = [f"# BRIEF_SUMMARY ({timestamp})"]

    if C: out.append("C: " + "; ".join(C[:3]))
    if D: out.append("D: " + "; ".join(D[:3]))
    if CH: out.append("Δ: " + "; ".join(CH[:3]))
    if Q: out.append("Q: " + "; ".join(Q[:2]))
    if N: out.append("→: " + "; ".join(N[:3]))

    text = "\n".join(out)

    # Truncate to ~250 tokens (≈1000 chars)
    return text[:1000]


def full_summary(lines, timestamp=None):
    """Generate Tier-B Full (≤900 tokens ~ 3600 chars)"""
    C, D, CH, Q, N = extract_markers(lines)

    timestamp = timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    out = [f"# FULL_SUMMARY ({timestamp})\n"]

    if C:
        out.append("## CONSTRAINTS")
        for i, c in enumerate(C, 1):
            out.append(f"- C{i}: {c}")
        out.append("")

    if D:
        out.append("## DECISIONS")
        for i, d in enumerate(D, 1):
            out.append(f"- D{i}: {d}")
        out.append("")

    if CH:
        out.append("## CHANGES")
        for ch in CH:
            out.append(f"- Δ {ch}")
        out.append("")

    if Q:
        out.append("## OPEN_QUESTIONS")
        for i, q in enumerate(Q, 1):
            out.append(f"- Q{i}: {q}")
        out.append("")

    if N:
        out.append("## NEXT_ACTIONS")
        for i, n in enumerate(N, 1):
            out.append(f"- → A{i}: {n}")

    text = "\n".join(out)

    # Truncate to ~900 tokens (≈3600 chars)
    return text[:3600]


def ultra_summary(lines):
    """Generate Tier-C Ultra (≤120 tokens ~ 480 chars)"""
    C, D, CH, Q, N = extract_markers(lines)

    parts = []
    if C: parts.append(f"C:[{';'.join(C[:2])}]")
    if D: parts.append(f"D:[{';'.join(D[:2])}]")
    if CH: parts.append(f"Δ:[{';'.join(CH[:2])}]")
    if Q: parts.append(f"Q:[{';'.join(Q[:1])}]")
    if N: parts.append(f"→:[{';'.join(N[:2])}]")

    text = " ".join(parts)
    return text[:480]


def main():
    parser = argparse.ArgumentParser(description="Memory session summarizer")
    parser.add_argument("--input", "-i", type=str, help="Input file (default: stdin)")
    parser.add_argument("--mode", "-m", choices=["brief", "full", "ultra"],
                       default="brief", help="Summary mode (default: brief)")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")

    args = parser.parse_args()

    # Read input
    if args.input:
        with open(args.input, 'r') as f:
            lines = f.read().splitlines()
    else:
        lines = sys.stdin.read().splitlines()

    # Generate summary
    if args.mode == "brief":
        summary = brief_summary(lines)
    elif args.mode == "full":
        summary = full_summary(lines)
    else:
        summary = ultra_summary(lines)

    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(summary)
    else:
        print(summary)


if __name__ == "__main__":
    main()
