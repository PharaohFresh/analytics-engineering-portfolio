"""Independent row-count reconciliation: staging -> marts (trust, but verify).

Mirrors the 'verify with a script, don't just trust the run' discipline from production work.
Reads BigQuery target from environment variables (never hard-coded):
    BQ_PROJECT   -- GCP project that holds the built models
    BQ_DATASET   -- dataset/schema the models were built into (e.g. dbt_dev)
Auth: Application Default Credentials -- run once:  gcloud auth application-default login

Usage:  python scripts/qa_audit.py
Exit code 0 = all checks pass, 1 = at least one reconciliation failed.
"""
import os
import sys

try:
    from google.cloud import bigquery
except ImportError:
    sys.exit("[ERROR] pip install google-cloud-bigquery to run this audit.")

PROJECT = os.environ["BQ_PROJECT"]
DATASET = os.environ["BQ_DATASET"]


def t(name):
    return f"`{PROJECT}.{DATASET}.{name}`"


# (label, query) -- each query returns a single integer expected to be 0.
CHECKS = [
    (
        "fct_order_items grain == stg_order_items rows",
        f"select (select count(*) from {t('fct_order_items')}) "
        f"     - (select count(*) from {t('stg_order_items')})",
    ),
    (
        "fct_orders grain == stg_orders rows",
        f"select (select count(*) from {t('fct_orders')}) "
        f"     - (select count(*) from {t('stg_orders')})",
    ),
    (
        "no orphan order_items (item without parent order)",
        f"select count(*) from {t('fct_order_items')} oi "
        f"left join {t('fct_orders')} o on oi.order_key = o.order_key "
        f"where o.order_key is null",
    ),
    (
        "no null sale_price in order items",
        f"select count(*) from {t('fct_order_items')} where sale_price is null",
    ),
]


def main():
    client = bigquery.Client(project=PROJECT)
    failures = 0
    for label, query in CHECKS:
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
