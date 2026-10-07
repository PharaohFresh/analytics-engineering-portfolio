import argparse
import json
from pathlib import Path

from . import evaluate


def main():
    parser = argparse.ArgumentParser(description="Model synthetic checkout events at complete-session grain.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {report['summary']['sessions']} sessions; {report['summary']['payment_attempts']} payment attempts.")
    print("[REVIEW] Multiple authorizations are review candidates, not confirmed duplicate charges.")
    print(f"Report: {args.output / 'report.json'}")


if __name__ == "__main__":
    main()
