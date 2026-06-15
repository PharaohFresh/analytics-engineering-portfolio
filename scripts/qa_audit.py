"""Independent row-count reconciliation: staging -> marts (trust, but verify).

Mirrors the 'verify with a script, don't just trust the run' discipline from production work.
Reads Snowflake connection from environment variables (never hard-coded):
    SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD,
    SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA

Usage:  python scripts/qa_audit.py
Exit code 0 = all checks pass, 1 = at least one reconciliation failed.
"""
import os
import sys

try:
    import snowflake.connector
except ImportError:
    sys.exit("[ERROR] pip install snowflake-connector-python to run this audit.")

# (label, expectation, query) -- each query returns a single integer.
CHECKS = [
    (
        "fct_order_items grain == stg_lineitems rows",
        "equal",
        "select (select count(*) from fct_order_items) "
        "     - (select count(*) from stg_lineitems)",
    ),
    (
        "fct_orders grain == stg_orders rows",
        "equal",
        "select (select count(*) from fct_orders) "
        "     - (select count(*) from stg_orders)",
    ),
    (
        "no orphan order_items (line without parent order)",
        "zero",
        "select count(*) from fct_order_items oi "
        "left join fct_orders o on oi.order_key = o.order_key "
        "where o.order_key is null",
    ),
    (
        "no null net_revenue in order items",
        "zero",
        "select count(*) from fct_order_items where net_revenue is null",
    ),
]


def main():
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
        database=os.environ.get("SNOWFLAKE_DATABASE"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA"),
    )
    failures = 0
    cur = conn.cursor()
    try:
        for label, expectation, query in CHECKS:
            cur.execute(query)
            value = cur.fetchone()[0]
            ok = (value == 0)  # both 'equal' (diff==0) and 'zero' expect 0
            status = "[OK]  " if ok else "[FAIL]"
            print(f"{status} {label}  (result={value})")
            if not ok:
                failures += 1
    finally:
        cur.close()
        conn.close()

    print("-" * 60)
    if failures:
        print(f"[FAIL] {failures} reconciliation check(s) failed.")
        sys.exit(1)
    print("[OK] all reconciliation checks passed.")


if __name__ == "__main__":
    main()
