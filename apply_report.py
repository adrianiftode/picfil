#!/usr/bin/env python
"""Apply a similarity threshold to a scan.csv produced by filter_by_person.py.

Copies (or moves) every photo whose best_similarity >= threshold into --output.
Run it with different thresholds as many times as you like without rescanning.
"""
import argparse
import csv
import os
import shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="scan.csv produced by filter_by_person.py")
    ap.add_argument("--output", required=True, help="output folder for matches")
    ap.add_argument("--threshold", type=float, default=0.40)
    ap.add_argument("--move", action="store_true", help="move instead of copy")
    ap.add_argument("--min-faces", type=int, default=1, help="require at least this many faces in the photo")
    ap.add_argument("--clean", action="store_true", help="delete existing files in output first")
    args = ap.parse_args()

    if args.clean and os.path.isdir(args.output):
        for fn in os.listdir(args.output):
            p = os.path.join(args.output, fn)
            if os.path.isfile(p):
                os.remove(p)

    os.makedirs(args.output, exist_ok=True)
    matched = 0
    total = 0
    with open(args.report, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            total += 1
            if not row["best_similarity"]:
                continue
            if int(row["n_faces"]) < args.min_faces:
                continue
            sim = float(row["best_similarity"])
            if sim < args.threshold:
                continue
            src = row["path"]
            dest = os.path.join(args.output, os.path.basename(src))
            if not os.path.exists(src):
                print(f"[WARN] missing source: {src}")
                continue
            if os.path.exists(dest):
                continue
            if args.move:
                shutil.move(src, dest)
            else:
                shutil.copy2(src, dest)
            matched += 1

    print(f"rows in report : {total}")
    print(f"written        : {matched}")
    print(f"threshold      : {args.threshold}")
    print(f"output         : {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
