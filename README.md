# Retail & Supply-Chain Analytics Platform (dbt + Snowflake)

A governed, agentic analytics-engineering platform built on Snowflake's `TPCH_SF1` sample data,
framed as a **retail & supply-chain analytics warehouse** — orders, customers, suppliers, parts,
and line items modeled into trustworthy, documented, self-serve marts.

This repo is deliberately **not** a tutorial clone. It demonstrates four things a technical screener
actually looks for:

1. **Dimensional modeling with intent** — explicit grain decisions, conformed dims, staging → intermediate → marts.
2. **Testing & documentation like someone who has owned a platform** — generic + singular tests, source definitions, described models.
3. **Governance** — dev/prod separation, no-deletion policy, PR-based promotion, a human-approval gate before prod. (Rare in a portfolio.)
4. **Governed agentic delivery** — AI used as an accountable accelerator, with the receipts (`runbooks/ai-assisted-delivery.md`).

## Architecture

```
models/
  staging/        stg_* (1:1 with source, renamed/typed) + sources + generic tests
  intermediate/   int_order_items_enriched, int_customer_orders
  marts/
    core/         dim_customers, dim_parts, dim_suppliers, dim_dates, fct_orders, fct_order_items
    finance/      mart_revenue_by_segment, mart_supplier_spend   ← original business marts
snapshots/        snap_suppliers (SCD-2)
scripts/          qa_audit.py — Python row-count reconciliation (trust-but-verify)
runbooks/         declarative runbooks (add-a-new-mart, model-review, qa, ai-assisted-delivery)
```

### Grain (stated explicitly — the thing screeners check)
- `fct_orders` — **one row per order** (`order_key`).
- `fct_order_items` — **one row per order line** (`order_item_key = order_key || '-' || line_number`); **incremental** on order date to mirror high-volume fact patterns.

## Stack
- **Warehouse:** Snowflake (`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)
- **Transformation:** dbt (staging views, marts as tables, one incremental fact, one SCD-2 snapshot)
- **Verification:** Python (`scripts/qa_audit.py`)

## Quickstart
```bash
pip install dbt-snowflake
cp profiles.yml.example ~/.dbt/profiles.yml   # then fill in your Snowflake creds (never commit them)
dbt deps        # installs packages if packages.yml is present
dbt build       # runs models + tests in DAG order
dbt docs generate && dbt docs serve
```

## Governance
See [`GOVERNANCE.md`](GOVERNANCE.md) — environment separation, no-deletion policy, PR promotion, approval gate.

## Roadmap
A platform is never "done" — deliberate next iterations:
- **Semantic layer** — governed metrics (revenue, AOV) + a downstream exposure
- **Grain-assertion macro** (`dbt_utils`) — reusable uniqueness/grain guards across facts
- **Generated docs + DAG** — published lineage graph and model-level documentation

---
*Built by Amir Ebrahim — senior analytics engineer. [linkedin.com/in/amirebrahim](https://linkedin.com/in/amirebrahim)*
