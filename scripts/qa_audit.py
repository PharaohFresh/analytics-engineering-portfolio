"""Independent read-only BigQuery checks for counts, keys and values.

Set BQ_PROJECT and BQ_DATASET to the exact built target. Uses worker Application
Default Credentials. Exit 0 means all contracts pass; exit 1 means a failed check.
"""
import os
import sys

from qa_contracts import queries

try:
    from google.cloud import bigquery
except ImportError:
    sys.exit("[ERROR] pip install google-cloud-bigquery to run this audit.")

def main():
    try:
        project, dataset = os.environ["BQ_PROJECT"], os.environ["BQ_DATASET"]
        checks = queries(project, dataset)
    except (KeyError, ValueError) as exc:
        sys.exit(f"[ERROR] Set a valid BQ_PROJECT and BQ_DATASET for the built target: {exc}")
    client = bigquery.Client(project=project)
    failures = 0
    for label, query in checks:
        value = list(client.query(query).result())[0][0]
        ok = (value == 0)
        status = "[OK]  " if ok else "[FAIL]"
        print(f"{status} {label}  (result={value})")
        if not ok:
            failures += 1

    print("-" * 60)
    if failures:
        print(f"[FAIL] {failures} reconciliation check(s) failed.")
        sys.exit(1)
    print("[OK] all reconciliation checks passed.")


if __name__ == "__main__":
    main()
