# Retail / DTC Analytics Platform (dbt + BigQuery)

[![dbt-ci](https://github.com/PharaohFresh/analytics-engineering-portfolio/actions/workflows/dbt-ci.yml/badge.svg)](https://github.com/PharaohFresh/analytics-engineering-portfolio/actions/workflows/dbt-ci.yml)

A governed, agentic analytics-engineering platform built on Google's
`bigquery-public-data.thelook_ecommerce` sample data — a synthetic direct-to-consumer
retail store. Orders, customers, products, order items, and distribution centers are
modeled into trustworthy, documented, self-serve marts.

This repo is deliberately **not** a tutorial clone. It demonstrates four things a technical screener
actually looks for:

1. **Dimensional modeling with intent** — explicit grain decisions, conformed dims, staging → intermediate → marts.
2. **Testing & documentation like someone who has owned a platform** — generic + singular tests, source definitions, described models.
3. **Governance** — dev/prod separation, no-deletion policy, PR-based promotion, a human-approval gate before prod. (Rare in a portfolio.)
4. **Governed agentic delivery** — AI used as an accountable accelerator, with the receipts (`runbooks/ai-assisted-delivery.md`).

> Companion repo: the governed agentic delivery model that operates this warehouse —
> multi-agent plan → approval gate → execute → verify → log — lives at
> [`agentic-analytics-delivery`](https://github.com/PharaohFresh/agentic-analytics-delivery).

## Architecture

```
models/
  staging/        stg_* (1:1 with source, renamed/typed) + sources + generic tests
  intermediate/   int_order_items_enriched, int_customer_orders
  marts/
    core/         dim_customers, dim_products, dim_distribution_centers, dim_dates, fct_orders, fct_order_items
    finance/      mart_revenue_by_segment, mart_product_category_margin   ← business marts
    _exposures.yml  declared dashboard consumer (impact analysis via `dbt ls`)
  semantic/       MetricFlow semantic models + 9 governed metrics
snapshots/        snap_products (SCD-2)
scripts/          qa_audit.py — Python row-count reconciliation (trust-but-verify)
runbooks/         declarative runbooks (add-a-new-mart, model-review, qa, ai-assisted-delivery)
```

### Grain (stated explicitly — the thing screeners check)
- `fct_orders` — **one row per order** (`order_key`).
- `fct_order_items` — **one row per order item / physical unit** (`order_item_key`, the natural item id); **incremental** on `item_created_at` to mirror high-volume fact patterns.

## Stack
- **Warehouse:** BigQuery (`bigquery-public-data.thelook_ecommerce`)
- **Transformation:** dbt (staging views, marts as tables, one incremental fact, one SCD-2 snapshot)
- **Verification:** Python (`scripts/qa_audit.py`)

## Quickstart
```bash
pip install dbt-bigquery
gcloud auth application-default login          # OAuth via Application Default Credentials
cp profiles.yml.example ~/.dbt/profiles.yml    # then set your GCP project (never commit secrets)
dbt deps        # installs packages if packages.yml is present
dbt build       # runs models + tests in DAG order
dbt docs generate && dbt docs serve

# independent reconciliation (after a build)
export BQ_PROJECT=career-analytics-portfolio BQ_DATASET=dbt_dev
python scripts/qa_audit.py
```

> The source is a public dataset; you only pay BigQuery's free-tier query/storage in **your own**
> project. The marts are tiny — well within the monthly free tier.

## Semantic layer
Metric definitions live in one governed place (`models/semantic/`), not re-derived in every
dashboard: two semantic models (`orders`, `order_items`) expose 9 metrics — revenue, gross
margin, AOV, return rate, margin rate, active customers, and friends. `dim_dates` doubles as
the MetricFlow time spine, and ratio metrics resolve across semantic models (AOV = item-grain
revenue ÷ order-grain count). Validated against the warehouse with `mf validate-configs`:

```
mf query --metrics total_revenue,order_count,average_order_value,return_rate --group-by metric_time__year

metric_time__year    total_revenue    order_count    average_order_value    return_rate
-----------------  ---------------  -------------  ---------------------  -------------
2024                    1,859,960          21,600                  86.11         0.0961
2025                    2,824,870          32,853                  85.99         0.1040
2026                    2,971,470          33,835                  87.82         0.0988
```

Downstream consumption is declared, not implied: the finance marts feed a dashboard registered
as an exposure (`models/marts/_exposures.yml`), so
`dbt ls --select +exposure:revenue_margin_overview` answers "what breaks this dashboard?"
before a change ships.

## Governance
See [`GOVERNANCE.md`](GOVERNANCE.md) — environment separation, no-deletion policy, PR promotion, approval gate.

## Roadmap
A platform is never "done" — deliberate next iterations:
- **Orchestration** — Airflow DAG artifact with a DagBag CI test
- **Grain-assertion macro** (`dbt_utils`) — reusable uniqueness/grain guards across facts
- **Generated docs + DAG** — published lineage graph and model-level documentation

---
*Built by Amir Ebrahim — senior analytics engineer. [linkedin.com/in/amirebrahim](https://linkedin.com/in/amirebrahim)*
