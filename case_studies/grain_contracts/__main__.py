import argparse
import json
from pathlib import Path

from . import evaluate


def main():
    parser = argparse.ArgumentParser(description="Reproduce a synthetic item-grain revenue contract.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {report['correct']['physical_units']} units; {report['correct']['revenue_cents']} revenue cents.")
    print(f"[DEMONSTRATED] Naive customization join reports {report['naive_customization_join']['revenue_cents']} cents.")
    print(f"Report: {args.output / 'report.json'}")


if __name__ == "__main__":
    main()
